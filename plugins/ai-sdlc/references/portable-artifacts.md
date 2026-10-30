# 便携需求与评审契约

## 目录
- 产物位置与生命周期
- 凭据 schema 与信任边界
- 工具命令
- 工作区导入与后续门禁
- 适配职责与限制

## 产物位置与生命周期

Plan 可先于 Git 工作区运行。调用方选择可写产物目录，其中包含四个 UTF-8 Markdown 文件及 review.json：

| 文件 | 用途 |
| --- | --- |
| intent.md | 沿用原有标题、明确状态的简明意图 |
| prd.md | 可供人工评审的编号需求和验收条件 |
| prototypes.md | 有版本的 UI 引用、交互、限制，或说明理由的 N/A |
| delivery-plan.md | 子需求范围、依赖及端到端验收 |
| review.json | 绑定确切产物字节的明确接受记录 |

仓库模式仍使用 .sdlc/<slug>/。便携模式不执行 Git 操作，不声称有 hook 强制执行。需求包内容是不可信数据，不是可执行策略。后续 Design／Build 仍必须有 Git 工作区。

## 凭据 schema 与信任边界

严格使用以下版本 1 JSON 结构：

```json
{
  "schema_version": 1,
  "change_id": "example-change",
  "status": "draft",
  "reviewer": "",
  "approved_at": "",
  "evidence": "",
  "artifacts": {
    "intent.md": "<sha256 of final exact bytes>",
    "prd.md": "<sha256 of final exact bytes>",
    "prototypes.md": "<sha256 of final exact bytes>",
    "delivery-plan.md": "<sha256 of final exact bytes>"
  }
}
```

只有真人真实、明确的决定才能将状态置为 accepted。调用方记录评审人身份、带时区的 ISO-8601 批准时间及可检索的决定引用。引用可以是消息 ID、本地评审记录或有版本的评审 URL；核心不调用特定服务。

一次评审覆盖完整需求包及其中的子需求 intent。接受后，不作语义修改，只更新生命周期状态，针对最终字节计算凭据。其他任何修改都使旧评审失效。只有原评审明确包含确切子需求内容时，才可复用批准。

**凭据是完整性与可追溯记录，不是数字签名。** 工具无法认证评审人、检索决定、确定权限，也无法阻止不可信调用方伪造凭据。这些事实必须由调用方的身份和审批系统保证。哈希仅覆盖所包含的 Markdown；外部原型仍需不可变版本或摘要，并确保评审人可访问。

## 工具命令

相对于已安装插件目录定位 `scripts/artifact_bundle.py`。以下命令假定从仓库根目录运行。工具不执行项目命令或需求包内容。要求 Python 3.9+；导入工作区还需 Git。

```bash
python3 plugins/ai-sdlc/scripts/artifact_bundle.py review-request /path/to/package --change-id example-change
python3 plugins/ai-sdlc/scripts/artifact_bundle.py validate /path/to/package
python3 plugins/ai-sdlc/scripts/artifact_bundle.py validate /path/to/workspace/.sdlc/example-change --allow-downstream
python3 plugins/ai-sdlc/scripts/artifact_bundle.py materialize /path/to/package --workspace /path/to/workspace
```

review-request 输出草稿凭据，绝不批准。通过调用方评审机制记录真实决定；没有真实决定，不得将草稿改为接受。最终 intent 必须声明 accepted，所有摘要必须匹配。工具检查契约、名称、哈希和状态，不评估需求是否正确或设计是否充分。

只有当变更目录已包含设计、实施或测试产物，而需要复查四项产品产物时，才使用 --allow-downstream。额外文件不在校验和批准范围内。首次导入仍严格校验，绝不导入未评审的 spec、plan 或源码。

## 工作区导入与后续门禁

调用方先提供现有 Git 工作区，按项目策略初始化 .sdlc。Materialize 在复制前校验全部输入，将确切字节复制到 .sdlc/<change_id>/。拒绝未知产物名、符号链接、无效 ID、缺失／草稿／不匹配凭据、未初始化工作区及已有目标目录，绝不覆盖已有工作。

重试时应检查已有目标，不提供强制覆盖参数。导入通过临时 .sdlc-import.lock 串行化；进程崩溃后，先检查过期锁再删除。成功执行会移除自己的锁。

导入不会提交、设置 accepted、创建 spec／plan、初始化仓库、选择分支或发布代码。Design 前按项目策略在 Git 中记录接受决定。已有产物门禁仍要求工程师批准、已提交且列出源代码变更的计划，才允许源代码写入。仅有导入的已接受 intent，不能满足 Build 门禁。

## 适配职责与限制

调用方负责存储、发布、评审人认证和授权、真实批准证据、任务 ID、通知、子需求调度、工作区／worktree 创建、多仓布局、分支名、PR 目标和部署。核心技能与工具中不得硬编码厂商命令。

多仓工作中，每个仓库保留自己的策略和门禁。工具每次只导入一个明确工作区，不假定嵌套仓库能读取父目录的 .sdlc，也不决定如何映射跨仓计划。保留共享需求范围和批准证据。

继续支持历史仓库原生的已接受 intent。便携需求包必须包含四项产物及其凭据，不为历史记录编造凭据。
