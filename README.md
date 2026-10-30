# AI 原生 SDLC — Claude Code 与 Codex 插件

**可实际运行的 AI 原生软件开发生命周期**：六个阶段、可评审产物，每次交接都有人工批准门禁。Plan 可先于代码工作区运行；工作区就绪后，导入并提交已接受需求。本独立社区实现将 [Anthropic 的 AI 原生 SDLC 实践指南](https://claude.com/blog/the-ai-native-sdlc-playbook)封装为 [Claude Code](https://claude.com/product/claude-code) 与 Codex 插件。

[![许可证：MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)
![Claude Code 插件](https://img.shields.io/badge/Claude%20Code-plugin-black)
![Codex 插件](https://img.shields.io/badge/Codex-plugin-black)
![阶段数](https://img.shields.io/badge/stages-6-black)
[![HOL 注册表](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Dghiaog123%252Fai-native-sdlc%26metric%3Dtrust)](https://hol.org/registry/plugins/ghiaog123%2Fai-native-sdlc)

![终端演示：plan.md 声明拼写修复为低风险，仅修改 README.md。门禁以退出码 0 放行 README.md 写入，以退出码 2 阻止 REVIEW.md 写入，因为快速路径不能触及 Sensitive paths 中的文件。](docs/demo.gif)

真人将变更声明为低风险，因而跳过 intent 和 spec。随后 Agent 尝试修改规定其权限范围的 `REVIEW.md`，被 hook 阻止。核心原则是：**声明可以减少阶段，不能减少边界。**

克隆项目后，可在临时仓库中复现，无需安装插件：

```bash
git clone https://github.com/ghiaog123/ai-native-sdlc.git
cd ai-native-sdlc
export GATE="$PWD/plugins/ai-sdlc/hooks/artifact-gate.sh"
source docs/demo-setup.sh
gate README.md    # exit 0
gate REVIEW.md    # exit 2
```

![AI 原生 SDLC 循环：Plan 编写 intent.md，Design 编写 spec.md，Build 编写 plan.md，Test 产生测试及 eval，Deploy 执行 REVIEW.md，Maintain 监测 bands.yaml。控制带越界后生成下一份 intent.md。各阶段之间均有人工门禁。](docs/loop.svg)

Agent 负责生成、调查、实现和验证；真人批准需要判断的决定。Git 记录提出者、Agent 产出及批准人。

> 名称描述本项目实现的方法：Anthropic 的 AI 原生 SDLC 实践指南。
> 本项目是独立社区实现，不是 Anthropic 产品，与 Anthropic 无关联，也未获其背书。

---

## 什么是 AI 原生 SDLC？

AI 原生 SDLC 围绕一个事实设计软件生命周期：**代码生成不再是瓶颈**。Agent 能在几分钟内实现定义清晰的变更时，制约因素转向 Build 前后：决定做什么、落实策略、验证结果、审查、授权发布，以及从生产环境学习。

传统 SDLC 在分析、设计、工程、QA 和运维角色之间交接工作。AI 原生 SDLC 用**产物循环**替代角色交接：每阶段输出可版本管理、供人工阅读及机器执行的 Markdown，与应用代码一同提交。真人不必亲自编写产物，但必须**接受**它。仓库成为审计轨迹。

这也称为 Agent 驱动的 SDLC、AI 驱动的 SDLC 或规格驱动开发。区别不在 Markdown，而在于**每次交接都停在 Agent 无法自行放行的门禁前**。

## 工作区尚不存在时的需求阶段

Plan 现在产出可供人工评审的 PRD、原型引用（或说明理由的 N/A）、子需求计划和 intent，统一评审一次。没有仓库或 worktree 时，文件保存在调用方指定目录，以明确评审凭据绑定确切字节。核心不向指定存储服务发布，不认证评审人，也不调度工作。

调用方准备并初始化 Git 工作区后，使用 `plugins/ai-sdlc/scripts/artifact_bundle.py` 校验并导入需求包。按项目策略提交已接受输入，再运行 Design。历史上已接受的仓库原生 intent 继续受支持。Design 使用结构化摘要、架构与流程图、数据与接口契约、风险、评审记录和验证映射；Build 仍需单独批准实施计划。

命令、凭据的信任边界、确切文件名和适配职责，见[便携产物契约](plugins/ai-sdlc/references/portable-artifacts.md)。已有源代码写入和生产防护不变。便携产品阶段不声称在未初始化仓库之外有 hook 强制执行。

## 六个阶段

| 阶段 | 驱动技能 | 目标 | 已提交产物 | 人工门禁 |
| --- | --- | --- | --- | --- |
| **1. Plan 需求规划** | `sdlc-plan` | 捕获提出者的问题、结果和约束 | `.sdlc/<slug>/intent.md` | 产品负责人接受 intent |
| **2. Design 技术设计** | `sdlc-design` | 将已接受 intent 转为需求及受策略约束的设计 | `.sdlc/<slug>/spec.md` | 评审人接受范围和已标记疑虑 |
| **3. Build 构建实现** | `sdlc-build` | 修改代码前确定实施路径 | `.sdlc/<slug>/plan.md`，再编写代码 | 工程师接受计划 |
| **4. Test 测试验证** | `sdlc-test` | 产生确定性证据，并回归验证 Agent 配置 | 测试输出、eval 结果、PR 检查 | 检查通过，负责人评估残余风险 |
| **5. Deploy 审查交付** | `sdlc-deploy` | 一致地审查，在生产边界停止 | PR、审查发现、发布记录 | 代码负责人和发布授权人批准 |
| **6. Maintain 运维反馈** | `sdlc-maintain` | 检测并诊断漂移，将经验反馈给 Plan | 事件记录或新的 `intent.md` | 服务负责人分诊发现 |

阶段 6 反馈给阶段 1，形成循环。

两个子 Agent 提供支持：`sdlc-reviewer` 在阶段 3 评审计划、阶段 5 执行 `REVIEW.md` 审查，并在发现发布前复核真实性；`sdlc-diagnostician` 在阶段 6 将控制带越界转为 `intent.md` 草稿。

真人声明低风险的变更采用**快速路径**，从 Build 进入，仅跳过阶段 1、2。Agent 依据 `REVIEW.md` 敏感路径清单检查声明，触及时拒绝；`REVIEW.md` 自身也在清单上，因此不能在快速路径清空清单。产物门禁强制拒绝，阶段 5 再核查真实 diff，因为事前文件清单只是对未完成工作的主张。

审查最多三轮，记录在 `.sdlc/<slug>/review-findings.md`。第 1 轮后只检查新 diff，不重复报告已发布发现；多处调用点的同类缺陷只报告一次。达到上限即停止，让变更回到计划：连续审查仍不断发现问题，说明方案需要调整。

## 安装

支持 **Claude Code** 和 **Codex**。二者读取同一插件目录，共享六阶段技能、hook 和产物模板，仅 manifest 与子 Agent 格式不同，两种均已提供。

两种运行环境的 manifest 使用相同插件版本。以下命令跟随 marketplace 源；带标签快照及版本变化见 [GitHub Releases](https://github.com/ghiaog123/ai-native-sdlc/releases)。

marketplace 源可以是 GitHub 仓库、URL 或本地路径，因此本地克隆与发布仓库的安装方式相同。

### Claude Code

在交互会话中从 GitHub 安装：

```text
/plugin marketplace add ghiaog123/ai-native-sdlc
/plugin install ai-sdlc@ai-native-sdlc
```

在终端从 GitHub 安装，适用于包括无法打开 `/plugin` 对话框的界面：

```bash
claude plugin marketplace add ghiaog123/ai-native-sdlc
```

```bash
claude plugin install ai-sdlc@ai-native-sdlc --scope user
```

修改插件本身时，从本地克隆安装：

```bash
claude plugin marketplace add ./ai-native-sdlc
```

仅在单次会话中试用，无需安装：

```bash
claude --plugin-dir ./ai-native-sdlc/plugins/ai-sdlc
```

`ai-sdlc` 是插件，`ai-native-sdlc` 是其 marketplace。安装保存在 `~/.claude/plugins/`，由 CLI 和桌面应用共享，安装一次即可。后续更新使用 `claude plugin marketplace update ai-native-sdlc`。

### Codex

从 GitHub 安装：

```bash
codex plugin marketplace add ghiaog123/ai-native-sdlc --ref main
```

```bash
codex plugin add ai-sdlc@ai-native-sdlc
```

源参数也接受 `owner/repo@ref`、HTTPS 或 SSH Git URL，因此可使用 `codex plugin marketplace add git@github.com:ghiaog123/ai-native-sdlc.git`。添加 `--sparse .claude-plugin --sparse plugins` 可在检出时跳过文档和示例。

后续更新使用：

```bash
codex plugin marketplace upgrade ai-native-sdlc
```

该命令仅适用于 Git marketplace。本地路径添加的 marketplace 没有可升级的 revision，需要重新添加。

修改插件本身时，从本地克隆安装：

```bash
codex plugin marketplace add ./ai-native-sdlc
```

Codex 读取 `plugins/ai-sdlc/.codex-plugin/plugin.json`，指向同一 `skills/`、通过 `hooks/hooks.codex.json` 使用的相同 hook 脚本，以及 `agents/*.toml` 子 Agent 定义，无需转换。

有一项重要差异：**Codex 在运行插件 hook 前要求明确授予信任，需通过交互式 Codex CLI 的 `/hooks` 完成。** 未授权前，技能和子 Agent 可用，但门禁仅提供指导，强制执行层未启用。安装或更新后检查 hook 状态；定义变化需要重新批准。不要用 `--dangerously-bypass-hook-trust` 跳过，信任提示是确保 hook 可安全运行的步骤。

项目记忆也不同：Codex 读取 `AGENTS.md`，Claude Code 读取 `CLAUDE.md`。`ai-sdlc-init` 检测项目环境，必要时从同一模板向两份文件写入相同内容，避免漂移。

安装前请阅读下一节，因为插件会注册 hook。

## 安装对本机的影响

请在安装前阅读。插件包含自动执行的 hook。

启用插件后，每次会话注册四个 hook（Claude Code 立即生效；Codex 在 TUI 中授予信任后生效）：

| Hook | 触发时机 | 行为 |
| --- | --- | --- |
| `artifact-gate.sh` | 每次 `Write`／`Edit` 前 | 若没有已接受且列明目标文件的 `plan.md`，阻止源代码写入 |
| `prod-guard.sh` | 每次 `Bash` 前 | 阻止看起来像生产部署或拆除的命令 |
| `session-context.sh` | 会话开始 | 输出当前阶段和待通过门禁 |
| `prompt-nudge.sh` | 每条用户消息 | 输出一行待通过门禁 |

**仓库没有 `.sdlc/` 时，所有 hook 均立即静默退出。** 这就是主动启用开关，且行为已验证：未执行 `/ai-sdlc-init` 的仓库，安装插件不会改变 Claude Code 行为。

已启用的仓库中，门禁确实会阻止操作。这正是其目的，也提供三种退出方式：

- `.sdlc/OPTOUT`：持续停用该仓库所有 hook，无需其他修改。
- `AI_SDLC_ALLOW_PROD=1`：真人批准后，授权执行一次生产命令。
- `/plugin uninstall ai-sdlc`（Claude Code）或 `codex plugin remove ai-sdlc@ai-native-sdlc`（Codex）：彻底移除 hook。

每条阻止消息会说明匹配规则与退出方式，不让阻止原因成为谜。

## 使用

在要运行生命周期的仓库中执行：

```text
/ai-sdlc-init
```

生成 `.sdlc/`，检查真实构建、测试和 lint 命令后编写项目 `CLAUDE.md`，复制 `REVIEW.md` 和 `bands.yaml` 策略模板。

然后直接描述问题，无需流程关键词，`sdlc-plan` 会识别：

```text
Customers keep calling support to ask where their claim is.
We should show them the status themselves.
```

流程写出 `.sdlc/<slug>/intent.md` 并等待接受。接受后依次写 spec、plan，再实施与验证，每道门禁都停下。绝不将自身输出视为人工批准。

随时查询变更所在阶段：

```text
/ai-sdlc-status
```

## 安装后持续生效

技能自动触发具有概率性。此处持续生效不依赖自动触发，四层机制按强度从高到低维持流程：

| 层次 | 机制 | 模型“忘记”后仍生效 |
| --- | --- | --- |
| 强制执行 | `PreToolUse` hook 阻止无已接受 `plan.md` 的源代码写入，拦截常见生产命令 | 是 |
| 恢复 | `SessionStart` 每次会话开始重新注入流程状态 | 是 |
| 提醒 | `UserPromptSubmit` 添加当前阶段及待通过门禁 | 是 |
| 记忆 | `/ai-sdlc-init` 向项目 `CLAUDE.md` 写入幂等标记块 | 是 |

启用开关是一个目录。`/ai-sdlc-init` 创建 `.sdlc/` 后，流程持续作用于该仓库。没有此目录的仓库中，所有 hook 静默退出，因此安装插件不改变其他项目行为。`.sdlc/OPTOUT` 是停用开关。

阶段状态始终**推导而非存储**：依据产物是否存在及 Git 状态计算，不存在会过时的状态文件。

## 与其他方案比较

| | 本仓库 | [GitHub Spec Kit](https://github.com/github/spec-kit) | BMAD-METHOD | OpenSpec |
| --- | --- | --- | --- | --- |
| 覆盖 Plan → Build | 是 | 是 | 是 | 是 |
| 覆盖 Test、Deploy、Maintain | 是 | 否 | 部分 | 否 |
| Hook 强制执行人工门禁 | 是 | 否 | 否 | 否 |
| 生产命令防护 | 尽力而为 | 否 | 否 | 否 |
| 控制带监控并提出下一份 intent | 是 | 否 | 否 | 否 |
| Agent 配置 eval | 是 | 否 | 否 | 否 |
| 多 Agent 工具支持 | Claude Code 与 Codex | 30 多种 Agent | 不限定模型 | 不限定模型 |

规格驱动开发工具在生命周期前半段已较成熟。本仓库聚焦后半段：验证证据、审查策略、发布授权和生产反馈；这些是实践指南的关键主张，也是鲜有方案完整实现的部分。

## 常见问题

### AI 原生 SDLC 实际如何运行？

每阶段产出 Markdown，提交到 Git，并由指定真人接受后再进入下一阶段：`intent.md` → `spec.md` → `plan.md` → PR → 生产 → 控制带越界 → 下一份 `intent.md`。

### 是否允许 AI Agent 部署生产？

不允许。`sdlc-deploy` 明确禁止合并或部署；阶段 6 通过 PR 提出修复，不直接实施。

`prod-guard.sh` 提供较弱的第二道防线：识别常见部署和拆除命令，要求明确人工授权。它只是减速带，不是安全边界。改写部署命令的调用者可绕过正则。IAM 权限、部署审批和分支保护仍是真正控制，不能因 hook 而放松。

### 与规格驱动开发有何区别？

规格驱动开发覆盖 spec 编写及基于 spec 的规划。本项目覆盖完整生命周期，包括验证证据、Agent 必须遵守的审查策略、发布授权，以及服务漂移时提出下一份 intent 的监控。

### 什么是 eval，为什么重要？

Eval 是 **Agent 配置**的回归测试，不是代码回归测试。`CLAUDE.md`、技能或 hook 变化时重新运行，因为配置变化可能悄然削弱 Agent 行为，而单元测试不会失败。

### 安装会影响其他仓库吗？

不会。所有 hook 首先检查 `.sdlc/`，不存在时静默退出。这是已验证行为。

### 支持 Codex，还是仅支持 Claude Code？

两者均支持。插件并列提供两种 manifest，技能、hook 脚本和模板完全共享。差异已处理：子 Agent 分别采用 `.md`（Claude Code）与 `.toml`（Codex），项目记忆按运行环境写入 `CLAUDE.md` 或 `AGENTS.md`。Codex 中唯一需自行完成的是在 TUI 授予 hook 信任，否则门禁仅提供指导。

其他 Agent 也可参考工具中立的 [`docs/PLAYBOOK.md`](docs/PLAYBOOK.md)，产物模板是普通 Markdown。

### 能沿用 Jira 或 ServiceNow 流程吗？

可以。只要提交双向关联，它们可继续作为记录系统。产物用于保留决策轨迹，不替代任务系统。

## 仓库结构

```text
.
├── README.md
├── docs/
│   ├── loop.svg          # The six-stage loop diagram
│   ├── PLAYBOOK.md       # Stage-by-stage operating model and artifact contract
│   ├── GOVERNANCE.md     # Enforceable controls and threat model
│   ├── METRICS.md        # Process health signals and how to compute them
│   └── ADOPTION.md       # Three-phase rollout
├── examples/rate-limit/  # One change walked through all six stages
├── plugins/ai-sdlc/
│   ├── .claude-plugin/   # Plugin manifest
│   ├── .codex-plugin/    # Codex plugin manifest
│   ├── skills/           # Six stage procedures plus ai-sdlc-init and ai-sdlc-status
│   ├── agents/           # sdlc-reviewer, sdlc-diagnostician (.md for Claude, .toml for Codex)
│   ├── hooks/            # Artifact gate, production guard, state, session context, and their checks
│   └── templates/        # intent, spec, plan, review-findings, CLAUDE, REVIEW, bands, settings
└── .claude-plugin/       # Marketplace catalog
```

## 文档

- [**实践指南**](docs/PLAYBOOK.md)：核心理念、循环、产物模板、责任归属和门禁。
- [**治理**](docs/GOVERNANCE.md)：让策略可执行的控制及其威胁模型。
- [**指标**](docs/METRICS.md)：领先和滞后指标、计算方法及被操纵方式。
- [**推广**](docs/ADOPTION.md)：从志愿者到全组织的推广路径及常见失败模式。

## 使用边界

- 不授权 Agent 合并、批准或部署自身工作。
- 不替代产品判断、代码责任、事件指挥或监管责任。
- 不强迫每个团队更换记录系统。
- 不保证 Markdown 能改善薄弱需求；只有评审者拒绝含糊表述，产物才有效。
- 不用于按 Agent 使用、产量或速度给开发者排名。
- 不构成移除确定性测试、静态分析、分支保护、沙箱或回滚演练的理由。

从产物开始，先证明门禁改善决定，再自动化团队能够解释和审计的路径。

## 致谢

方法来源：[AI 原生 SDLC 实践指南](https://claude.com/blog/the-ai-native-sdlc-playbook)，Anthropic Applied AI。本仓库是独立实现，与 Anthropic 无关联，也未获其背书。

采用 [MIT 许可证](LICENSE)。
