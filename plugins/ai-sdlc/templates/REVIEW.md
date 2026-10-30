# 审查指导

## Passes

每次审查分别执行独立审查项，仅报告变更代码、变更计划或其直接行为中有证据支持的问题。

**Plan**：阶段 3 编码前审查 `plan.md`，且该阶段仅执行这一项。检查已接受 spec 中每项需求是否纳入工作；快速路径没有 spec，则工作必须限于 `## Fast path` 声明范围和原因，不触及敏感路径。`Proof` 必须指出需求破坏时确实会失败的验证，不仅声称有测试；`Order of work` 不得有步骤依赖后续步骤；`Risks` 覆盖迁移、兼容和回退；`Files that change` 与真实范围一致。文件清单不是形式要求：门禁据此放行源代码写入，漏项会中途阻塞实施，过宽则扩大放行范围。

**Bugs**：可能返回错误结果、丢失或破坏数据、破坏已有受支持流程、错误处理重试或并发、使失败路径不安全的行为。核查边界、默认值、错误处理及与已接受 spec 的兼容性。

**Security**：信任边界缺少授权、注入、秘密暴露、不安全反序列化、不安全密码算法、权限提升、敏感日志或外部可触达的拒绝服务路径。新增依赖和公开端点均与安全相关。

**Compliance**：违反已声明的数据分级、同意、保留期限、审计日志、访问控制、无障碍或监管控制。若无适用项目规则，说明未发现适用要求，不编造要求。

## Reviewer

Stage 3 plan review: `codex-plan-review`
Stage 5 code review: `sdlc-reviewer`

指定各阶段评审者。插件内置的 `sdlc-reviewer` 始终可用。已安装的外部评审者（如 `codex-plan-review`）可提供更强评审；不可用时回退至 `sdlc-reviewer` 执行 `Plan`，在 `review-findings.md` 记录回退，不跳过评审。

## Depth

Depth: Standard

这是仓库默认值。可按区域覆盖：每行写路径和级别，多个匹配时取最深级别：

```text
src/billing/*        Deep
docs/*               Quick
```

**Quick**：阶段 3 执行 Plan，阶段 5 执行 Bugs 和 Security。仅一轮，不报告 Nit。快速路径默认采用 Quick，除非触及敏感路径。

**Standard**：执行全部审查项，Nit 数量按下述上限，使用完整轮次预算。

**Deep**：执行全部审查项，另外追踪每个变更函数的调用者，对照该区域最近两次事件，报告 Standard 会省略的 Minor。适用于漏掉一个缺陷就代价高昂的代码。

所有深度均执行 Security，不得削减。触及 **Sensitive paths** 的任何变更至少采用 Standard，不受此处低级别设置影响。

## Sensitive paths

触及以下任一路径的变更都不是低风险，不能采用快速路径，且始终需要人工批准：

```text
CLAUDE.md
REVIEW.md
bands.yaml
.claude/settings.json
.claude/skills/*
.claude/hooks/*
.github/workflows/*
.github/actions/*
```

补充本项目必须由真人阅读 diff 才能修改的路径：认证、授权、计费、迁移、安装和更新路径。`REVIEW.md` 自身在清单中，防止快速路径扩大或清空清单。

## Rounds

Round cap: 3.

一轮审查包含一次评审及作者修复，记录在 `.sdlc/<slug>/review-findings.md`。

**复审 diff，不重复审查整个变更。** 第 1 轮之后只检查相较上一轮记录 SHA 的改动。

**同一发现不发布两次。** 先检查历史轮次，报告抑制数量，不重复问题。

**按类别报告，不按代码行重复报告。** 同一缺陷出现在多处调用点时，报告一次并要求修复全部实例。只修一处、其余仍有缺陷，不算解决。

**达到上限即停止。** 需要第 4 轮时不再审查，说明原因，让作者返回 `plan.md` 重新考虑方案。连续轮次不断新增问题，意味着方案有问题，而不是审查有效。

## Verifier

发布任何发现前（阶段 3 的计划发现、阶段 5 的 diff 发现），第二位只读评审者仅查看发现及引用的代码或计划，不接触产生发现的推理，判断失败是否真实。拒绝的发现不发布，每轮记录拒绝数。

复核者只判断真实性，不判断重要性，不升级、降级、改写或新增发现。

## What Important means here

**Important**：会影响正确性、安全、合规、可用性或客户数据的现实生产失败。修复或由负责真人明确接受前，阻塞合并。

**Minor**：范围有限、实际可行时应在发布前修复的问题。

**Nit**：不阻塞交付的清晰度改善。

**Pre-existing**：不是本次变更引入的真实缺陷。不阻塞合并，不计入作者责任，但始终在 PR 列出供真人决定。已有安全缺陷归入 Security，保留真实严重程度并照常阻塞合并：标签改变责任归属，不改变能否交付。

## Cap the nits

最多报告五项 Nit。Important 不计入上限，也不因上限而抑制。两项 Important、零项 Nit 的审查优于返回二十条的审查。

## Fix a repeat at its source

同类问题出现在至少两项变更时，必须固化到能防止再次发生的位置：`CLAUDE.md` 条目、lint 规则或本文件规则。在 `review-findings.md` 的 **Recurring** 列出类别和固化措施。未固化的重复类别会阻塞阶段 5 退出门禁。

## Do not report

生成代码、第三方内置依赖、配置的格式化工具或 linter 已处理的格式，以及对正确性、安全、合规或维护无影响的主观风格偏好。
