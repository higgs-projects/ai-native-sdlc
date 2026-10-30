# Review findings: [变更名称]

<!--
每项变更一个文件，路径为 `.sdlc/<slug>/review-findings.md`。每轮追加，不改写历史轮次。
本文件是审查记忆：记录用于强制上限的轮次、使下轮仅检查增量的 SHA、避免重复发布的发现，
以及 `docs/METRICS.md` 中审查指标的证据。
-->

Reviewer: [sdlc-reviewer | codex-plan-review]. Depth: [Quick | Standard | Deep].
Round cap: 3.

## Round 1 — Plan — [plan.md SHA 或 `uncommitted`]

Passes run: Plan.

Scope: 完整 `plan.md`。

`.sdlc/[slug]/plan.md:[line] — Important — [具体失败] — [具体修复] — Response: pending`

<!--
严重程度定义见 `REVIEW.md`：Important、Minor、Nit、Pre-existing。
作者在本轮结束时设置 Response，取值如下：
  fixed        发现真实存在，代码或计划已修改
  wrong        发现不真实
  intentional  真实，但该行为有意如此；注明记录位置
  no-impact    真实，但不值得修改
`pending` 仅在当前未结束轮次有效。
-->

## Round 2 — Code — [被审查 SHA]

Passes run: Bugs, Security, Compliance.

Scope: 从 [上轮 SHA] 到 [本轮 SHA] 的 diff。第 1 轮之后只检查新 diff，不重新审查整个变更。

历史轮次已报告，此处不重复：[数量]。

`path/to/file:line — Important — [具体失败] — [具体修复] — Response: fixed`
`path/to/file:line — Pre-existing — [具体失败] — [具体修复] — Response: no-impact`

## Pre-existing

<!--
不是本次变更引入的缺陷不阻塞合并，但不得默默丢弃：逐项列出，由负责的真人决定处置。
若 Pre-existing 属于安全缺陷，则归入 Security，像其他 Important 一样阻塞合并。
标签改变责任归属，不改变能否交付。
-->

| 发现 | 位置 | 决定 |
| --- | --- | --- |
| [失败] | `path:line` | [现在修复／待办引用／接受及原因] |

## Recurring

<!--
同类问题已出现在至少两项变更中时，必须固化为能防止第三次发生的规则。
此处任一行没有固化措施，`sdlc-deploy` 的退出门禁就不能通过。每类一行，不按实例逐行记录。
-->

| 类别 | 出现过的变更 | 固化措施 |
| --- | --- | --- |
| [缺陷类别，不是某一行代码] | `[slug]`、`[slug]` | [CLAUDE.md 条目／lint 规则／REVIEW.md 规则] |

## Round summary

| 轮次 | 阶段 | 发布发现数 | 去重数 | 复核拒绝数 |
| --- | --- | --- | --- | --- |
| 1 | Plan | [n] | 0 | [n] |
| 2 | Code | [n] | [n] | [n] |

<!--
需要第 4 轮时，评审者停止审查，请作者回到 `plan.md` 重新考虑方案，不再逐项修复发现。
在此记录并返回计划，不开启第 4 轮。
-->
