# AI 原生 SDLC 示例：公开 API 限流

此示例从客户问题出发，贯穿循环，直到从运维中学习。

1. **Plan 需求规划**：[intent.md](rate-limit/intent.md) 描述匿名客户端为何可压垮公开 API，以及期望客户结果。
2. **Design 技术设计**：[spec.md](rate-limit/spec.md) 将意图转化为端点、身份、存储和安全要求。
3. **Build 构建实现**：[plan.md](rate-limit/plan.md) 在编码前列出实施顺序、风险和证明方式。
4. **Review 审查**：项目评审者对照已接受产物执行 Bugs、Security 和 Compliance。
5. **Deploy 审查交付**：[review-findings.md](rate-limit/review-findings.md) 展示可操作的发现，发布前必须解决或由真人接受。
6. **Maintain 运维反馈**：[band-breach-intent.md](rate-limit/band-breach-intent.md) 展示 p99 越界如何形成新 intent，而非变成未跟踪的生产修改。

产物刻意具体：描述一个合理的公开 API 功能，而不是待填写空表。
