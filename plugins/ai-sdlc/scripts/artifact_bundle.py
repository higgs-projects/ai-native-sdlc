#!/usr/bin/env python3
"""Validate a reviewed requirements bundle and materialize it in a Git workspace.

Receipts record human decisions supplied by the caller. This tool does not
authenticate a reviewer, approve artifacts, execute content, commit, or deploy.
"""

import argparse
from contextlib import contextmanager
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


ARTIFACTS = ("intent.md", "prd.md", "prototypes.md", "delivery-plan.md")
INTENT_HEADINGS = (
    "Problem", "Proposed outcome", "Affected users and systems", "Constraints",
    "Open questions",
)
MAX_BYTES = 5 * 1024 * 1024
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class BundleError(ValueError):
    pass


def change_id(value):
    if (not isinstance(value, str) or len(value) > 64
            or not SLUG.fullmatch(value) or value == "evals"):
        raise BundleError("change_id must be a safe kebab-case slug, not evals")
    return value


def read_file(path):
    if path.is_symlink() or not path.is_file():
        raise BundleError(f"expected a regular file, not a symlink: {path.name}")
    if path.stat().st_size > MAX_BYTES:
        raise BundleError(f"file exceeds {MAX_BYTES} bytes: {path.name}")
    data = path.read_bytes()
    if len(data) > MAX_BYTES:
        raise BundleError(f"file exceeds {MAX_BYTES} bytes: {path.name}")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise BundleError(f"file is not UTF-8: {path.name}") from error
    return data


def snapshot(bundle, allow_downstream=False):
    if bundle.is_symlink() or not bundle.is_dir():
        raise BundleError("bundle must be a regular directory")
    names = {path.name for path in bundle.iterdir()} - {"review.json"}
    if not set(ARTIFACTS).issubset(names) or (not allow_downstream and names != set(ARTIFACTS)):
        raise BundleError("bundle must contain exactly intent.md, prd.md, "
                          "prototypes.md, delivery-plan.md and optional review.json")
    return {name: read_file(bundle / name) for name in ARTIFACTS}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise BundleError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def nonempty(value, field):
    if not isinstance(value, str) or not value.strip():
        raise BundleError(f"review.{field} must be a nonempty string")


def validate(bundle, allow_downstream=False):
    # Read once: validation and materialization use the same exact bytes.
    files = snapshot(bundle, allow_downstream=allow_downstream)
    receipt_bytes = read_file(bundle / "review.json")
    try:
        receipt = json.loads(receipt_bytes, object_pairs_hook=unique_object)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise BundleError("review.json is not valid UTF-8 JSON") from error
    fields = {"schema_version", "change_id", "status", "reviewer",
              "approved_at", "evidence", "artifacts"}
    if not isinstance(receipt, dict) or set(receipt) != fields:
        raise BundleError("review.json does not match the version 1 contract")
    if type(receipt["schema_version"]) is not int or receipt["schema_version"] != 1:
        raise BundleError("unsupported review schema_version")
    change_id(receipt["change_id"])
    if receipt["status"] != "accepted":
        raise BundleError("bundle has no explicit accepted review")
    for field in ("reviewer", "approved_at", "evidence"):
        nonempty(receipt[field], field)
    try:
        timestamp = datetime.fromisoformat(receipt["approved_at"].replace("Z", "+00:00"))
    except ValueError as error:
        raise BundleError("review.approved_at must be an ISO-8601 timestamp") from error
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise BundleError("review.approved_at must include a timezone")
    hashes = receipt["artifacts"]
    if not isinstance(hashes, dict) or set(hashes) != set(ARTIFACTS):
        raise BundleError("review.artifacts must bind all four exact artifact names")
    for name, data in files.items():
        if hashes[name] != digest(data):
            raise BundleError(f"review digest mismatch: {name}; obtain a matching review")
    intent = files["intent.md"].decode("utf-8")
    if not re.search(r"^(?:Author:[^\r\n]*?\.\s*)?Status:\s*accepted\.?\s*$",
                     intent, re.MULTILINE):
        raise BundleError("intent.md must explicitly declare Status: accepted")
    for heading in INTENT_HEADINGS:
        if not re.search(r"^## " + re.escape(heading) + r"\s*$", intent, re.MULTILINE):
            raise BundleError(f"intent.md is missing contract heading: {heading}")
    return receipt, {**files, "review.json": receipt_bytes}


def review_request(bundle, slug):
    files = snapshot(bundle)
    return {
        "schema_version": 1, "change_id": change_id(slug), "status": "draft",
        "reviewer": "", "approved_at": "", "evidence": "",
        "artifacts": {name: digest(data) for name, data in files.items()},
    }


@contextmanager
def import_lock(root):
    lock = root / ".sdlc-import.lock"
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as error:
        raise BundleError("another import holds .sdlc-import.lock; inspect it before retrying") from error
    try:
        os.close(fd)
        yield
    finally:
        lock.unlink()


def materialize(bundle, workspace):
    receipt, files = validate(bundle)
    root = workspace.resolve(strict=True)
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            check=True, text=True, capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as error:
        raise BundleError("workspace must be an existing Git working tree") from error
    if Path(result.stdout.strip()).resolve() != root:
        raise BundleError("workspace must be the Git working-tree root")
    sdlc = root / ".sdlc"
    if sdlc.is_symlink() or not sdlc.is_dir():
        raise BundleError("initialize the workspace SDLC loop first; .sdlc must not be a symlink")
    destination = sdlc / receipt["change_id"]
    with import_lock(root):
        if destination.exists() or destination.is_symlink():
            raise BundleError("destination already exists; compare versions instead of overwriting")
        staging = Path(tempfile.mkdtemp(prefix=".import-", dir=sdlc))
        try:
            for name, data in files.items():
                (staging / name).write_bytes(data)
            # No source paths from a receipt are used, and no content is executed.
            staging.rename(destination)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    request = sub.add_parser("review-request", help="print a DRAFT receipt, never approve")
    request.add_argument("bundle", type=Path)
    request.add_argument("--change-id", required=True)
    check = sub.add_parser("validate", help="check an accepted receipt and exact artifact bytes")
    check.add_argument("bundle", type=Path)
    check.add_argument("--allow-downstream", action="store_true",
                       help="validate only the four requirements artifacts in a live change directory")
    restore = sub.add_parser("materialize", help="copy a reviewed bundle into an initialized Git workspace")
    restore.add_argument("bundle", type=Path)
    restore.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "review-request":
            print(json.dumps(review_request(args.bundle, args.change_id), indent=2))
        elif args.command == "validate":
            receipt, _ = validate(args.bundle, allow_downstream=args.allow_downstream)
            print(json.dumps({"valid": True, "change_id": receipt["change_id"]}))
        else:
            destination = materialize(args.bundle, args.workspace)
            print(json.dumps({"materialized": str(destination), "committed": False,
                              "next": "commit the reviewed artifacts under project policy; run sdlc-design"}))
    except (BundleError, OSError) as error:
        print(f"artifact bundle: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
