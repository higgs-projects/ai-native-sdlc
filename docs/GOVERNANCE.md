# 治理即代码

有效治理应在行动发生点执行控制、产生证据，且不能被受约束者悄然豁免。

本文将 [Anthropic AI 原生 SDLC 实践指南](https://claude.com/blog/the-ai-native-sdlc-playbook)的控制模型转化为可强制执行的仓库与平台机制。
示例是起点。启用前，依据目标仓库威胁模型审查每条命令、路径、身份和域名。

## 控制原则

1. 指导控制提高安全行为的概率；确定性控制让禁止行为执行失败。
2. 生成变更的身份不能批准同一变更。
3. Agent 仅获得当前阶段和环境所需的最小权限。
4. 生产授权绑定真人、提交、环境和时间窗口。
5. 控制及其证据需版本化或集中记录。
6. 受保护行为后果重大时，控制失败应拒绝放行。
7. 每次阻止都解释原因及有效批准途径。
8. 控制需要测试和观测，不再对应真实威胁时应移除。

## 控制层次

| 层次 | 机制 | 性质 | 主要证据 |
| --- | --- | --- | --- |
| 指导 | 技能 | 建议性 | 技能版本及调用轨迹 |
| 行动 | Hook | 工具边界的确定性控制 | 输入、裁决、原因、时间戳 |
| 管理 | 托管设置 | 集中强制执行 | 管理策略与客户端状态 |
| 变更 | 分支保护 | 合并边界的确定性控制 | PR 检查、评审、合并事件 |
| 执行 | 沙箱 | 操作系统和网络隔离 | 沙箱策略与执行日志 |
| 历史 | Git 审计轨迹 | 可察觉篡改的协作记录 | 提交、签名、评审、标签 |
| 行为 | Eval | Agent 配置回归门禁 | 任务结果、评分器、通过阈值 |
| 自动化 | 非交互 CI | 可复现的有界执行 | 任务身份、输入、工具、输出 |

任何单层都不充分。技能可能被忽略；hook 不能防止 Agent 外的直接推送；分支保护不能阻止 CI 读取不必要的秘密；沙箱不能判断产品需求是否合乎伦理或有价值。各层围绕不同失败面组合控制。

## 技能

### 技能防范什么

技能减少 Agent 规划、设计、实现和审查时对组织知识应用不一致的问题，避免团队反复把过时策略贴进提示词，在需要时发现适用的安全、品牌、无障碍、架构和合规流程。
技能无法阻止蓄意绕过，不得作为不可协商规则的唯一控制。

### 技能的成本

技能占用上下文，需要明确策略负责人。过宽触发描述会加载无关指导，降低结果质量。
策略变化需要技能更新、评审、推广和回归评估。只复述大本策略手册而没有可执行流程，只增加维护工作，不改善决定。

### 示例

在 `.claude/skills/external-api/SKILL.md` 放置仓库技能：

```markdown
---
name: external-api
description: Apply when creating or changing a public HTTP endpoint or OpenAPI contract.
---

# External API control

Before proposing or editing an external endpoint:

1. Read `policy/api-security.md` at the current commit.
2. Require authentication except for the documented health endpoint.
3. Validate request bodies against the published schema and reject unknown fields.
4. Keep fields classified as restricted out of logs, errors, and traces.
5. Add an integration test for authorization and invalid input.
6. Run `./scripts/check-public-api.sh` and attach its output.

If requirements conflict with the policy, stop and name the conflict in `spec.md`.
The security owner must resolve the conflict; do not choose an exception.
```

策略负责人是该目录的代码负责人。Eval 检查改写后的端点任务仍能触发技能，并满足确定性检查。

## Hook

### Hook 防范什么

Hook 在行动边界阻止不安全工具调用。典型用途包括受保护路径修改、意外包含凭据、破坏性命令、受约束缺陷修复期间修改测试，以及未经授权部署生产。
Hook 将策略从提醒变为 allow、ask 或 block 决定。

### Hook 的成本

每次匹配动作都会承担延迟。过宽匹配造成提示疲劳，促使用户寻找绕过方式。
Shell 解析容易出错，命令可能采用意外形式。Hook 需要单元测试、结构化日志、负责人和服务不可用时的恢复途径。
快速检查放在工具使用时，完整扫描放在提交或 PR 阶段。

### 示例：实际 hook 配置

将以下内容提交为 `.claude/settings.json`，作为团队级生产命令门禁：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/production-gate.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

Hook 从标准输入接收工具请求；缺少授权时返回阻止执行的退出状态：

```bash
#!/usr/bin/env bash
set -euo pipefail

payload="$(</dev/stdin)"
command="$(jq -r '.tool_input.command // ""' <<<"$payload")"

if [[ "$command" != *"deploy"* || "$command" != *"production"* ]]; then
  exit 0
fi

if [[ -z "${RELEASE_APPROVAL_ID:-}" || -z "${APPROVED_SHA:-}" ]]; then
  echo "Blocked: production requires a release approval ID and approved commit SHA." >&2
  exit 2
fi

current_sha="$(git rev-parse HEAD)"
if [[ "$current_sha" != "$APPROVED_SHA" ]]; then
  echo "Blocked: HEAD does not match the commit authorized for release." >&2
  exit 2
fi

exit 0
```

批准查询应验证签发者、环境、有效期和提交，不能信任可随意设置的本地环境变量。
生产环境应使用外部签名批准记录或 CI 环境审批。

## 托管设置

### 托管设置防范什么

防止项目文件、用户偏好或命令行参数扩大中央控制允许范围。
可拒绝敏感路径、禁用权限绕过、要求沙箱、限制网络目标、仅允许托管 hook 与 MCP 服务、禁止旁加载插件、强制最低客户端版本。
对范围内所有仓库和工作站都必须适用的要求，应放在这一层。

### 托管设置的成本

中央策略减少本地灵活性，可能破坏合法流程。平台团队承担支持、分批推广、例外处理和客户端兼容测试。
允许清单过小会阻塞工作，未经评审持续扩大又会成为无人检查的许可清单。
一次错误可影响全组织，因此托管策略变更需要变更控制。

### 示例

以下托管设置片段在沙箱不可用时拒绝放行，并防止本地放宽：

```json
{
  "permissions": {
    "deny": [
      "Read(.env*)",
      "Read(./secrets/**)",
      "Bash(curl *)",
      "Bash(wget *)"
    ],
    "allow": [
      "Bash(git status*)",
      "Bash(make build)",
      "Bash(make test)",
      "Bash(make lint)"
    ],
    "disableBypassPermissionsMode": "disable"
  },
  "allowManagedPermissionRulesOnly": true,
  "allowManagedHooksOnly": true,
  "allowManagedMcpServersOnly": true,
  "disableSideloadFlags": true,
  "sandbox": {
    "enabled": true,
    "failIfUnavailable": true,
    "allowUnsandboxedCommands": false,
    "network": {
      "allowedDomains": [
        "git.example.internal",
        "registry.npmjs.org"
      ]
    }
  }
}
```

先部署试点组。扩大策略前记录拒绝动作、复查误报。

## 分支保护

### 分支保护防范什么

防止 Agent、CI 身份或真人直接推送受保护分支、绕过评审。
要求 PR、最新检查、已解决讨论、代码负责人评审，以及最后一次推送后的新批准。
在 Agent 编写或修改代码后保留职责分离。

### 分支保护的成本

必需检查增加排队与执行时间；代码负责人规则可能让批准集中于少数人。
撤销过期批准会让每次修改（含机械修复）都需要复审。
紧急变更需要有文档、可审计的紧急放行途径，而非不可见的绕过身份。

### 示例：实际 GitHub 仓库规则集

通过 `POST /repos/{owner}/{repo}/rulesets` 应用以下对象，按仓库调整检查名称：

```json
{
  "name": "protect-default-branch",
  "target": "branch",
  "enforcement": "active",
  "bypass_actors": [],
  "conditions": {
    "ref_name": {
      "include": ["~DEFAULT_BRANCH"],
      "exclude": []
    }
  },
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "do_not_enforce_on_create": false,
        "required_status_checks": [
          { "context": "ci/test" },
          { "context": "agent-evals" },
          { "context": "review-policy" }
        ]
      }
    },
    {
      "type": "pull_request",
      "parameters": {
        "allowed_merge_methods": ["squash", "merge"],
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": true,
        "require_last_push_approval": true,
        "required_review_thread_resolution": true
      }
    }
  ]
}
```

仅向 Agent 身份授予功能分支的 `contents: write`，不授予规则集绕过角色。
为 `CLAUDE.md`、`REVIEW.md`、`bands.yaml`、技能、hook、工作流和 CODEOWNERS 的变更配置适当负责人。

相同路径也应列入 `REVIEW.md` 的 **Sensitive paths**，作为机器可检查形式。分支保护阻止合并；敏感路径清单从一开始就阻止快速路径资格，产物门禁在写入时执行。两份清单应同步，否则此处受保护但遗漏于清单的路径，可沿快速路径一直修改到合并门禁。`REVIEW.md` 自身列入清单，防止跳过前期阶段的变更扩大或清空它。

## 沙箱

### 沙箱防范什么

允许工具或生成命令行为异常时，沙箱限制影响范围。防止任意读取文件、无限制网络出口、访问长期凭据、特权进程，以及写入工作区之外。
填补仅按工具名授权、无法看到 shell 内部行为的漏洞。

### 沙箱的成本

隔离增加启动时间，使部分构建更难。网络允许清单需要依赖清单和代理支持。
容器或远程 runner 需要缓存、测试 fixture 和本地服务替代。
排查拒绝原因时，需要可观察策略决定，同时不泄露受保护数据。

### 示例

在具有以下属性的临时容器中运行非交互 Agent 任务：

```yaml
securityContext:
  runAsNonRoot: true
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
resources:
  limits:
    cpu: "2"
    memory: "4Gi"
volumeMounts:
  - name: workspace
    mountPath: /workspace
  - name: tmp
    mountPath: /tmp
env:
  - name: HOME
    value: /tmp/agent-home
```

仓库工作区读写挂载，不挂载主目录凭据，为指定仓库签发短期 token，在 pod 配置之外强制网络出口控制。
实现或审查任务绝不注入生产凭据。

## Git 审计轨迹

### Git 轨迹防范什么

Git 防止未记录的产物替换成为已接受历史。记录谁提出 intent、哪版 spec 和 plan 获批、实现如何偏离、修复了哪些发现、哪个提交进入生产。
签名提交和受保护标签强化身份与发布来源。Git 不证明真人理解了产物，必须结合有意义的评审。

### Git 轨迹的成本

产物增加审查范围和仓库历史。团队必须防止秘密、敏感事件数据和个人信息进入提交。
未明确保留策略时，amend 或 squash 可能抹去中间证据。Git 不是正式记录系统时，与外部系统需要双向链接。

### 示例

用提交 trailer 使批准和关系可由机器查询：

```text
sdlc(design): approve customer-claim-status specification

Artifact: .sdlc/customer-claim-status/spec.md
Derived-From: 4d3c2b1
Status: Approved
Approved-By: product-owner@example.com
Policy-Owners: security@example.com,privacy@example.com
Record: JIRA-1842
```

发布记录保存确切合并 SHA 和部署环境，不使用可变分支名作为发布来源证明。

## Eval

### Eval 防范什么

防止 Agent 配置变化悄然削弱后续行为。覆盖 `CLAUDE.md`、技能、hook、提示词、模型、工具权限和编排。
将生产事件和重复审查失败转为永久回归案例。可用代码检查的行为，优先使用确定性评分器。

### Eval 的成本

模型运行消耗时间和费用，仍可能有方差。代码库变化使 fixture 漂移；简单案例饱和造成虚高通过率。
量表评分器需校准并复查分歧。套件与生产测试一样需要负责人。

### 示例：实际 eval 触发器

以下 GitHub Actions 工作流在每个 Agent 配置 PR、每夜及手动派发时运行：

```yaml
name: Agent evals

on:
  pull_request:
    paths:
      - "CLAUDE.md"
      - "REVIEW.md"
      - "bands.yaml"
      - ".claude/**"
      - "evals/**"
  schedule:
    - cron: "17 2 * * *"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  evaluate:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - name: Run bounded eval suite
        env:
          ANTHROPIC_API_KEY: ${{ secrets.EVALS_ANTHROPIC_API_KEY }}
        run: ./evals/run.sh --non-interactive --threshold 0.90
```

Runner 逐案例输出结果，记录模型和配置版本，低于已批准阈值时使必需检查失败。
每次重大生产事件后，在关闭纠正措施前增加案例。

## 非交互 CI

### 非交互 CI 防范什么

防止自动化依赖未记录的本地对话，或工程师逐次点击工具提示。使输入、身份、允许工具、预算、超时和输出可复现。
适用于构建失败分诊、变更日志草拟、审查、eval 执行及通过 PR 提出修复等有界工作，不构成授予生产凭据的理由。

### 非交互 CI 的成本

任务消耗模型预算和 runner 容量。保留和脱敏不足时，日志会暴露敏感提示词或输出。
重试可能倍增成本或重复外部动作。长任务需要超时、幂等、取消及清晰的部分输出策略。

### 示例

构建失败分诊先执行只读步骤：

```yaml
- name: Triage failed build
  if: failure()
  timeout-minutes: 5
  env:
    ANTHROPIC_API_KEY: ${{ secrets.TRIAGE_ANTHROPIC_API_KEY }}
  run: |
    claude -p "Read out/build.log. Classify the failure as deterministic, flaky, or unknown. Cite the relevant lines and write a three-line PR summary. Do not edit files." \
      --allowedTools "Read" \
      --output-format json \
      > out/triage.json
```

任务使用专用身份、只读检出、无生产凭据、硬超时和输出 schema 校验。
以后增加写权限时，只允许功能分支，并必须经过受保护 PR 路径。

## 持续生效：流程如何保持活跃

安装流程还不够，必须经受新会话、上下文重置及普通任务切换。四层机制按强度排序：

1. **`PreToolUse` hook 强制执行。** 活动变更没有列出目标文件的 `plan.md` 时，`artifact-gate.sh` 阻止代码写入。`prod-guard.sh` 识别常见生产命令形式。二者在工具边界执行，不增加逐消息提示词成本。

   两者强度不同，不能混为一谈。产物门禁基于 Agent 无法伪造的仓库状态作判断，满足则放行，否则拒绝。生产防护只是对命令字符串做模式匹配，仅提供纵深防御：提高未经评审部署的成本并生成审计信号，但有意或巧妙改写的调用者仍可通过。不能因其存在而放宽 IAM、部署审批或分支保护；真正边界由这些控制执行。衡量它捕获诚实失误的频率，不声称它能阻止攻击者。
2. **`SessionStart` 恢复运行状态。** 每次会话开始重新注入简明流程说明、适用技能和待通过门禁，不能假定新上下文记得当前阶段。自动执行，无逐消息成本。
3. **`UserPromptSubmit` 提醒。** 有进行中工作时，每轮添加一行当前阶段和门禁；无工作时保持静默。这是唯一每条消息都承担成本的层，因此应尽量精简、默认静默。
4. **项目记忆块提供持久记忆。** 初始化从同一模板写入 Claude Code 的 `CLAUDE.md` 和 Codex 的 `AGENTS.md`，避免漂移；运行环境每次会话独立加载。Hook 上下文不可用时仍保留仓库流程契约，代价是少量持久上下文。

第一层执行，中间层恢复与提醒，最后一层记忆。共同让关键安全检查保持确定性，并尽量减少重复上下文。

一种可预见失败是善意清理：团队为改善体验停用噪声 hook，循环悄然失效。提醒应简短、门禁应可操作，并提供 `.sdlc/OPTOUT` 作为合法退出方式，让团队明确退出，而非逐步拆除控制。

## 运行环境差异

不同运行环境对四层机制的支持不同。忽略差异会让团队误以为指导性门禁正在强制执行。

| 层次 | Claude Code | Codex |
| --- | --- | --- |
| `PreToolUse` 强制执行 | 插件启用即生效 | 需一次性信任授权，仅能通过交互式 Codex TUI 获得 |
| `SessionStart`／`UserPromptSubmit` 上下文 | 随插件生效 | 同样需要信任授权 |
| 项目记忆 | `CLAUDE.md` | `AGENTS.md` |
| 子 Agent 定义 | 带 YAML 元数据的 `agents/*.md` | 带 `developer_instructions` 的 `agents/*.toml` |

Codex 信任门禁是保护机制。若插件可在无人确认时注册阻止工具的 hook，它本身就是攻击面。应在 TUI 中有意识授予信任，不用 `--dangerously-bypass-hook-trust` 禁用确保第三方 hook 安全的检查。

对纯 Codex 团队，授予信任前仅由最弱的项目记忆层维持流程，模型可能自行解释而偏离。此时应表述为“产物已就绪，门禁未启用”，在推广说明中明确，不声称机器未提供的强制执行。

## 威胁模型

| 失败 | 主要控制 | 配套控制 | 证据 |
| --- | --- | --- | --- |
| Agent 忽略组织标准 | 技能 | Eval、审查项、策略负责人 | 技能版本、eval 结果、PR 发现 |
| Agent 修改受保护或生成路径 | Hook | 托管设置、评审 | 阻止记录及尝试路径 |
| Agent 读取本地秘密 | 沙箱 | 托管拒绝规则、短期凭据 | 沙箱拒绝及任务身份 |
| Agent 通过 shell 网络外传数据 | 沙箱出口策略 | 托管设置、代理日志 | 被拒目标和进程日志 |
| 用户停用不可协商 hook | 托管设置 | 管理状态检查 | 生效托管策略 |
| Agent 直接推送 main | 分支保护 | 限定范围 token、无绕过角色 | 被拒 ref 更新 |
| Agent 自批变更 | 分支保护 | 独立身份、CODEOWNERS | 必需独立评审 |
| Agent 部署未经审查提交 | 生产 hook | 发布环境批准、SHA 绑定 | 批准 ID 和已部署 SHA |
| Agent 削弱测试使修复通过 | 测试路径 hook | PR 审查、先有失败测试 | 被阻修改或明确评审 |
| 提示词或技能变化导致行为回归 | Eval | 必需检查、定期执行 | 版本化案例结果 |
| CI Agent 无限运行或消费 | 非交互 CI 限制 | 预算告警、取消 | 超时和使用日志 |
| CI 重试重复外部动作 | 幂等任务设计 | 唯一操作键、审计 API | 操作键和服务响应 |
| 实现后补写产物 | Git 产物顺序检查 | 分支规则、审查策略 | 提交时间和失败检查 |
| 评审变为形式盖章 | CODEOWNERS、审查策略 | 质量抽样、事件反馈 | 发现、批准延迟、逃逸缺陷 |
| 无真实越界却概率性诊断生产漂移 | 确定性 `bands.yaml` 检测 | 版本基线、单元测试 | 指标、规则、阈值、越界时间 |
| 事件关闭后经验消失 | Eval 和新 intent 要求 | 复盘清单、Git 轨迹 | 关联事件、eval 和纠正 PR |

## 控制复查节奏

推广期间每周复查 hook 阻止和沙箱拒绝，稳定后每月。
上游策略变化时复查技能负责人和策略版本。
每季度复查分支绕过身份和 CI token 权限范围。
每月复查 eval 区分力、不稳定案例、成本和生产覆盖。
按计划在预发布环境演练回滚和生产授权。
移除已不对应威胁的控制，但保留说明原因的决定记录。
治理即代码不意味着无需判断：代码使边界可重复执行，负责的人选择边界并承担例外责任。
