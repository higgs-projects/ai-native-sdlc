#!/usr/bin/env python3
"""Portable requirements round trips and failure cases; standard library only."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("artifact_bundle", HERE / "artifact_bundle.py")
bundle_tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle_tool)


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bundle = self.root / "product package"
        self.bundle.mkdir()
        intent = "# Intent: example\nAuthor: Product reviewer. Status: accepted.\n\n"
        intent += "\n".join(f"## {heading}\nConfirmed requirement.\n"
                            for heading in bundle_tool.INTENT_HEADINGS)
        for name in bundle_tool.ARTIFACTS:
            (self.bundle / name).write_text(intent if name == "intent.md" else f"# {name}\nReviewed.\n")
        self.accept()

    def accept(self):
        receipt = bundle_tool.review_request(self.bundle, "req-7")
        receipt.update(status="accepted", reviewer="Product reviewer",
                       approved_at="2026-10-30T10:00:00+08:00",
                       evidence="review-record:42/version:3")
        self.write_receipt(receipt)
        return receipt

    def write_receipt(self, receipt):
        (self.bundle / "review.json").write_text(json.dumps(receipt))

    def repo(self):
        path = self.root / "code workspace"
        path.mkdir()
        self.git(path, "init", "-q")
        self.git(path, "config", "user.name", "Fixture")
        self.git(path, "config", "user.email", "fixture@example.com")
        (path / ".sdlc").mkdir()
        return path

    def git(self, root, *args):
        return subprocess.run(["git", "-C", str(root), *args], check=True,
                              capture_output=True, text=True)

    def assert_invalid(self, text):
        with self.assertRaisesRegex(bundle_tool.BundleError, text):
            bundle_tool.validate(self.bundle)

    def test_draft_request_never_approves_or_needs_git(self):
        (self.bundle / "review.json").unlink()
        receipt = bundle_tool.review_request(self.bundle, "req-7")
        self.assertEqual(receipt["status"], "draft")
        self.assertEqual(receipt["reviewer"], "")
        self.assertFalse((self.bundle / ".git").exists())
        self.assertFalse((self.bundle / "review.json").exists())

    def test_acceptance_is_exact_and_repository_free(self):
        receipt, files = bundle_tool.validate(self.bundle)
        self.assertEqual(receipt["change_id"], "req-7")
        self.assertEqual(set(files), {*bundle_tool.ARTIFACTS, "review.json"})
        self.assertFalse((self.root / ".git").exists())

    def test_each_artifact_is_bound_by_review(self):
        for name in bundle_tool.ARTIFACTS:
            with self.subTest(name=name):
                original = (self.bundle / name).read_bytes()
                (self.bundle / name).write_bytes(original + b"Changed after review.\n")
                self.assert_invalid("digest mismatch")
                (self.bundle / name).write_bytes(original)

    def test_draft_review_rejected(self):
        receipt = self.accept()
        receipt["status"] = "draft"
        self.write_receipt(receipt)
        self.assert_invalid("no explicit accepted")

    def test_identity_and_evidence_required(self):
        for field in ("reviewer", "approved_at", "evidence"):
            with self.subTest(field=field):
                receipt = self.accept()
                receipt[field] = " "
                self.write_receipt(receipt)
                self.assert_invalid(field)

    def test_timezone_and_valid_timestamp_required(self):
        for timestamp in ("yesterday", "2026-10-30T10:00:00"):
            receipt = self.accept()
            receipt["approved_at"] = timestamp
            self.write_receipt(receipt)
            self.assert_invalid("timestamp|timezone")

    def test_unknown_schema_and_boolean_version_rejected(self):
        for version in (2, True, "1"):
            receipt = self.accept()
            receipt["schema_version"] = version
            self.write_receipt(receipt)
            self.assert_invalid("schema_version")

    def test_missing_or_extra_hash_rejected(self):
        receipt = self.accept()
        receipt["artifacts"].pop("prd.md")
        self.write_receipt(receipt)
        self.assert_invalid("all four")
        receipt = self.accept()
        receipt["artifacts"]["../outside"] = "0" * 64
        self.write_receipt(receipt)
        self.assert_invalid("all four")

    def test_traversal_and_reserved_change_ids_rejected(self):
        for slug in ("../escape", "/absolute", "a/b", "evals", "a" * 65):
            receipt = self.accept()
            receipt["change_id"] = slug
            self.write_receipt(receipt)
            self.assert_invalid("change_id")

    def test_missing_and_unknown_artifact_rejected(self):
        original = (self.bundle / "prd.md").read_bytes()
        (self.bundle / "prd.md").unlink()
        self.assert_invalid("exactly")
        (self.bundle / "prd.md").write_bytes(original)
        (self.bundle / "unreviewed.md").write_text("Unreviewed")
        self.assert_invalid("exactly")

    def test_symlink_artifact_or_receipt_rejected(self):
        for name in ("intent.md", "review.json"):
            with self.subTest(name=name):
                path = self.bundle / name
                original = path.read_bytes()
                outside = self.root / "external"
                outside.write_bytes(original)
                path.unlink()
                path.symlink_to(outside)
                self.assert_invalid("symlink")
                path.unlink()
                path.write_bytes(original)

    def test_duplicate_json_keys_rejected(self):
        receipt = (self.bundle / "review.json").read_text()
        (self.bundle / "review.json").write_text(receipt[:-1] + ', "status": "accepted"}')
        self.assert_invalid("duplicate JSON key")

    def test_draft_intent_with_matching_receipt_rejected(self):
        path = self.bundle / "intent.md"
        path.write_text(path.read_text().replace("Status: accepted", "Status: draft"))
        self.accept()
        self.assert_invalid("intent.md must explicitly")

    def test_missing_intent_heading_rejected(self):
        path = self.bundle / "intent.md"
        path.write_text(path.read_text().replace("## Constraints", "## Missing"))
        self.accept()
        self.assert_invalid("Constraints")

    def test_size_and_encoding_limits(self):
        path = self.bundle / "prd.md"
        path.write_bytes(b"x" * (bundle_tool.MAX_BYTES + 1))
        self.assert_invalid("exceeds")
        path.write_bytes(b"\xff")
        self.assert_invalid("UTF-8")

    def test_materialize_preserves_bytes_and_does_not_commit(self):
        repo = self.repo()
        destination = bundle_tool.materialize(self.bundle, repo)
        for path in self.bundle.iterdir():
            self.assertEqual(path.read_bytes(), (destination / path.name).read_bytes())
        result = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "HEAD"],
                                capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((repo / ".sdlc-import.lock").exists())
        self.assertEqual(sorted(p.name for p in (repo / ".sdlc").iterdir()), ["req-7"])

    def test_existing_destination_not_overwritten(self):
        repo = self.repo()
        destination = bundle_tool.materialize(self.bundle, repo)
        (destination / "intent.md").write_text("Existing local work")
        with self.assertRaisesRegex(bundle_tool.BundleError, "already exists"):
            bundle_tool.materialize(self.bundle, repo)
        self.assertEqual((destination / "intent.md").read_text(), "Existing local work")

    def test_invalid_bundle_leaves_workspace_untouched(self):
        repo = self.repo()
        (self.bundle / "prd.md").write_text("changed")
        with self.assertRaises(bundle_tool.BundleError):
            bundle_tool.materialize(self.bundle, repo)
        self.assertEqual(list((repo / ".sdlc").iterdir()), [])

    def test_workspace_requires_git_root_and_initialized_sdlc(self):
        repo = self.repo()
        (repo / ".sdlc").rmdir()
        with self.assertRaisesRegex(bundle_tool.BundleError, "initialize"):
            bundle_tool.materialize(self.bundle, repo)
        subdir = repo / "nested"
        subdir.mkdir()
        with self.assertRaisesRegex(bundle_tool.BundleError, "root"):
            bundle_tool.materialize(self.bundle, subdir)
        nonrepo = self.root / "no-repo"
        nonrepo.mkdir()
        with self.assertRaisesRegex(bundle_tool.BundleError, "Git working tree"):
            bundle_tool.materialize(self.bundle, nonrepo)

    def test_symlink_sdlc_rejected(self):
        repo = self.repo()
        (repo / ".sdlc").rmdir()
        (repo / ".sdlc").symlink_to(self.bundle, target_is_directory=True)
        with self.assertRaisesRegex(bundle_tool.BundleError, "symlink"):
            bundle_tool.materialize(self.bundle, repo)

    def test_git_worktree_is_supported(self):
        repo = self.repo()
        (repo / "README.md").write_text("fixture")
        self.git(repo, "add", "README.md")
        self.git(repo, "commit", "-qm", "fixture")
        worktree = self.root / "task worktree"
        self.git(repo, "worktree", "add", "-qb", "task", str(worktree))
        (worktree / ".sdlc").mkdir()
        self.assertTrue((worktree / ".git").is_file())
        self.assertEqual(bundle_tool.materialize(self.bundle, worktree),
                         worktree.resolve() / ".sdlc" / "req-7")

    def test_lock_conflict_does_not_remove_other_lock(self):
        repo = self.repo()
        lock = repo / ".sdlc-import.lock"
        lock.write_text("other import")
        with self.assertRaisesRegex(bundle_tool.BundleError, "another import"):
            bundle_tool.materialize(self.bundle, repo)
        self.assertEqual(lock.read_text(), "other import")

    def test_imported_intent_does_not_open_source_gate(self):
        repo = self.repo()
        bundle_tool.materialize(self.bundle, repo)
        self.git(repo, "add", ".sdlc")
        self.git(repo, "commit", "-qm", "Status: accepted; reviewed intent")
        hook = HERE.parent / "hooks" / "artifact-gate.sh"
        result = subprocess.run(["bash", str(hook)], cwd=repo,
                                input=json.dumps({"tool_input": {"file_path": "src/app.py"}}),
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        (repo / ".sdlc" / "req-7" / "plan.md").write_text(
            "# Plan\n\n## Files that change\n- `src/app.py`\n\n## Proof\nUnit and integration checks.\n")
        self.git(repo, "add", ".sdlc")
        self.git(repo, "commit", "-qm", "Fixture: engineer-approved plan")
        allowed = subprocess.run(["bash", str(hook)], cwd=repo,
                                 input=json.dumps({"tool_input": {"file_path": "src/app.py"}}),
                                 capture_output=True, text=True)
        self.assertEqual(allowed.returncode, 0)

    def test_cli_failure_returns_actionable_status(self):
        (self.bundle / "review.json").unlink()
        result = subprocess.run(["python3", str(HERE / "artifact_bundle.py"),
                                 "validate", str(self.bundle)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("review.json", result.stderr)

    def test_live_change_validates_requirements_without_approving_downstream(self):
        repo = self.repo()
        destination = bundle_tool.materialize(self.bundle, repo)
        (destination / "spec.md").write_text("# Spec\nStatus: draft\n")
        (destination / "plan.md").write_text("# Plan\nNot approved\n")
        with self.assertRaisesRegex(bundle_tool.BundleError, "exactly"):
            bundle_tool.validate(destination)
        receipt, files = bundle_tool.validate(destination, allow_downstream=True)
        self.assertEqual(receipt["status"], "accepted")
        self.assertNotIn("spec.md", files)
        self.assertNotIn("plan.md", files)
        (destination / "intent.md").write_text("changed after review")
        with self.assertRaisesRegex(bundle_tool.BundleError, "digest mismatch"):
            bundle_tool.validate(destination, allow_downstream=True)

    def test_materialize_never_imports_unreviewed_downstream_artifacts(self):
        repo = self.repo()
        (self.bundle / "spec.md").write_text("# Spec\nStatus: accepted\nUnreviewed")
        with self.assertRaisesRegex(bundle_tool.BundleError, "exactly"):
            bundle_tool.materialize(self.bundle, repo)
        self.assertEqual(list((repo / ".sdlc").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
