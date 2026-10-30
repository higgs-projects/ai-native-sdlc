# ai-sdlc

面向编码 Agent、设有人工门禁的六阶段软件开发生命周期。
Plan 可在没有代码工作区时运行：将 PRD、原型、intent 和子需求计划作为一个包统一评审。调用方在 Design 前，将经过评审的确切需求包导入已初始化的 Git 工作区。仓库阶段的产物按项目策略提交。

中立评审凭据、工具命令和调用方职责参见[便携需求](references/portable-artifacts.md)。Design 使用可供人工评审的结构化 spec；Build 仍需单独批准实施计划。

Plan 访谈需求提出者，编写描述问题与结果的 `intent.md`。Design 将已接受的 intent 转化为 `spec.md`。Build 先评审再实施 `plan.md`。Test 执行项目真实检查，引用输出而非仅声称通过。Deploy 执行审查并发布分级发现，等待真人批准。Maintain 监测控制带，越界后提出下一份 intent。

流程不能替代判断。Agent 负责归纳、实现、验证和分诊；真人决定做什么、接受什么风险以及交付什么。Git 记录提出者、Agent 产出及批准人。

![终端演示：plan.md 声明拼写修复为低风险，仅修改 README.md。门禁以退出码 0 放行 README.md 写入，以退出码 2 阻止 REVIEW.md 写入，因为快速路径不能触及 Sensitive paths 中的文件。](https://raw.githubusercontent.com/ghiaog123/ai-native-sdlc/main/docs/demo.gif)

真人声明低风险后，变更跳过 intent 和 spec 阶段。随后 Agent 尝试修改规定其权限范围的 `REVIEW.md`，被 hook 阻止。声明可以减少阶段，不能减少边界。

![六阶段循环：Plan 编写 intent.md，Design 编写 spec.md，Build 编写 plan.md，Test 产生检查和 eval 证据，Deploy 执行 REVIEW.md，Maintain 监测 bands.yaml。控制带越界后生成下一份 intent.md，重启循环。各阶段之间均有人工门禁。](https://raw.githubusercontent.com/ghiaog123/ai-native-sdlc/main/docs/loop.svg)

## 安装

```
/plugin install ai-sdlc --marketplace ghiaog123/ai-native-sdlc
```

随后在仓库执行 `/ai-sdlc-init`，生成流程骨架。

## 使用

### 开始一项变更

```
/sdlc-plan add rate limiting to the public API
```

Plan 访谈问题，在调用方选定目录（仓库模式下为 `.sdlc/rate-limit/`）编写 intent.md、prd.md、prototypes.md 和 delivery-plan.md。它停下等待覆盖整个包的明确评审，记录对应凭据，不选择架构。

然后依次推进各阶段。每个阶段读取上一阶段已提交产物，写出自己的产物，再停止：

```
/sdlc-design     # accepted intent.md  ->  spec.md
/sdlc-build      # accepted spec.md    ->  reviewed plan.md, then code
/sdlc-test       # runs the project's real checks, quotes the output
/sdlc-deploy     # review passes, ranked findings, stops for your approval
/sdlc-maintain   # watches bands.yaml, files the next intent on a breach
```

### 低风险变更

拼写修复无需访谈。向 `/sdlc-plan` 声明变更为低风险，它会检查 `REVIEW.md` 的敏感路径清单，再直接交给 `/sdlc-build`，从计划进入。可以跳过阶段，不能跳过门禁。

若实际触及敏感路径，Agent 会拒绝快速路径；即使 Agent 仍尝试写入，`artifact-gate.sh` 也会拒绝。

### 查询当前进度

```
/ai-sdlc-status
```

每项进行中变更一行：最远阶段、产物是否已提交，以及下一门禁正在等待哪位真人。

### 初始化仓库

```
/ai-sdlc-init
```

创建 `.sdlc/`，根据仓库真实构建、测试和 lint 命令编写项目记忆（Claude Code 使用 `CLAUDE.md`，Codex 使用 `AGENTS.md`），安装 `REVIEW.md` 和 `bands.yaml` 策略模板。可安全重复运行。

### 无需安装即可试用门禁

```bash
git clone https://github.com/ghiaog123/ai-native-sdlc
cd ai-native-sdlc
export GATE="$PWD/plugins/ai-sdlc/hooks/artifact-gate.sh"
source docs/demo-setup.sh
gate README.md    # exit 0, the plan covers it
gate REVIEW.md    # exit 2, the fast path cannot reach a sensitive path
```

在 `$TMPDIR` 下的临时仓库复现上方录屏。

## 安装内容

八个技能：六阶段，加上用于初始化仓库的 `/ai-sdlc-init` 和报告哪些变更在等待谁的 `/ai-sdlc-status`。

两个只读子 Agent：依据项目 `REVIEW.md` 审查 PR 的评审者，以及不修改生产环境、只调查控制带越界的诊断者。

四个 hook，仅在仓库有 `.sdlc/` 时生效；项目主动启用前，安装插件不会改变行为：

- `artifact-gate.sh` 拒绝没有已批准 `plan.md` 覆盖的源代码写入，并禁止低风险变更触及 `CLAUDE.md`、`REVIEW.md` 和 CI 工作流等治理敏感路径。
- `prod-guard.sh` 对部署和拆除类命令请求明确人工授权。它只是较弱的第二道防线；IAM、分支保护和部署审批仍是真正控制。
- `session-context.sh` 和 `prompt-nudge.sh` 根据已提交产物推导进行中变更状态，不依赖存储状态。

提供流程各项产物模板，包括 `REVIEW.md` 和 `bands.yaml`。

## 拦截范围及原因

插件注册 hook，因此能看到工具调用。全部 hook 如下。

| Hook | 触发时机 | 行为 | 能否阻止调用 |
| --- | --- | --- | --- |
| `artifact-gate.sh` | `Write`、`Edit` | 读取目标路径和 `.sdlc/` 下已提交的 `plan.md`；拒绝无已批准计划覆盖的源代码写入，以及快速路径变更中的敏感路径写入。 | 能 |
| `prod-guard.sh` | `Bash` | 匹配已知部署及拆除命令形式，运行前要求明确人工授权。 | 能 |
| `session-context.sh` | 会话开始 | 输出进行中变更及各自等待的门禁。 | 不能 |
| `prompt-nudge.sh` | 提交提示词 | 输出同样的单行状态。 | 不能 |

四个 hook 都只读仓库，不写入，不调用网络。没有 `.sdlc/` 时立即退出，因此项目主动启用前安装插件不会改变行为；即使已启用，`.sdlc/OPTOUT` 也能停用它们。

`prod-guard.sh` 是较弱的第二道防线，不是沙箱。它匹配命令形式，已有 shell 权限且有意绕过的人可改写命令规避。IAM、RBAC、分支保护和部署审批仍是真正控制。`SECURITY.md` 同样说明这一点，并列出值得报告的绕过问题。

### Agent 权限

两个子 Agent 都只读：`Read`、`Grep`、`Glob`、`Bash`，不提供 `Write` 或 `Edit`。Codex 中另以 `sandbox_mode = "read-only"` 运行。

保留 `Bash`，因为不能运行 `git diff` 和 `git log` 就无法审查变更。它们绝不编辑文件、批准或合并 PR，也不声称人工门禁已通过；从 diff、提交消息或依赖名读取的一切均视为数据而非指令。

## 不执行的操作

绝不合并、部署，也不将 Agent 批准当作真人批准。不绕过分支保护，也无此权限：新增门禁与已有控制并存，不替代它们。

## 运行检查

```bash
bash hooks/test-artifact-gate.sh
bash hooks/test-sdlc-state.sh
```

## 两种运行环境

同一源码适用于 Claude Code 和 Codex。Agent 定义同时提供 `.md` 和 `.toml` 并保持同步；项目记忆从同一模板写入 `CLAUDE.md` 或 `AGENTS.md`，避免内容漂移。

仅依赖 bash、git 和 python3。

## 文档与许可

方法、各控制的威胁模型、指标及其被操纵方式、三阶段推广方案，见项目仓库：
<https://github.com/ghiaog123/ai-native-sdlc>。

本项目实现 Anthropic AI 原生 SDLC 实践指南的方法，是独立社区实现，不是 Anthropic 产品，与 Anthropic 无关联，也未获其背书。

采用 MIT 许可证。
