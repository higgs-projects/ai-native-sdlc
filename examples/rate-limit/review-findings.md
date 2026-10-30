# Review findings: 公开 API 限流

Reviewer: sdlc-reviewer. Depth: Deep.
Round cap: 3.

## Round 1 — Plan — `a1b2c3d`

Passes run: Plan.

Scope: 完整 `plan.md`。

`.sdlc/rate-limit/plan.md:14 — Important — Proof 只写“中间件单元测试”，未说明断言；滑动窗口统计错误区间时可能没有测试失败 — 明确断言：窗口边界前一秒的请求计入，边界后一秒的请求不计入`

`.sdlc/rate-limit/plan.md:6 — Minor — Files that change 漏列 Order of work 第 4 步修改的 src/metrics/api.ts；门禁按清单放行，该步骤会被阻塞 — 将文件加入清单`

无其他 Plan 发现。

Verifier rejected: 1 — 有发现声称步骤 2 与 3 顺序错误，但步骤 3 不读取步骤 2 输出，因此失败不会发生。

## Round 2 — Code — `e4f5a6b`

Passes run: Bugs, Security, Compliance.

Scope: 整个变更，首轮代码审查。

历史轮次已报告，此处不重复：0。

`src/middleware/rateLimit.ts:84 — Important — Redis 键使用原始 API key，导致凭据出现在 Redis 检查和备份数据中 — 构造 Redis 键前使用 API-key ID 或 HMAC 摘要 — Response: fixed`

`src/middleware/rateLimit.ts:117 — Important — 拒绝请求缺少 RateLimit-Reset，客户端无法判断重试时间而激进重试 — 返回 429 前根据窗口内最早请求设置 RateLimit-Reset — Response: fixed`

`src/metrics/api.ts:42 — Minor — 拒绝指标以无界原始请求路径而非路由模板为标签，产生高基数可用性风险 — 改用路由器标准化路由模板 — Response: fixed`

`src/routes/public.ts:51 — Important — 处理器未验证代理链就读取 req.headers['x-forwarded-for']，客户端可伪造身份；虽然缺陷不是本次引入，但将它作为限流身份后可绕过限流 — 设置框架 trust-proxy 并读取推导后的客户端 IP — Response: fixed`

<!-- 已有缺陷，但属于安全发现：归入 Security，保留真实严重程度，照常阻塞合并。标签只改变责任归属，不改变能否交付。 -->

无其他 Bugs、Security 或 Compliance 发现。

Verifier rejected: 2.

## Round 3 — Code — `b7c8d9e`

Passes run: Bugs, Security, Compliance.

Scope: 从 `e4f5a6b` 到 `b7c8d9e` 的 diff。

历史轮次已报告，此处不重复：3。

No findings.

Verifier rejected: 0.

## Pre-existing

| 发现 | 位置 | 决定 |
| --- | --- | --- |
| 从不可信 `x-forwarded-for` 推导客户端身份 | `src/routes/public.ts:51` | 本次修复；以 `Important` 归入 Security，因为本次将可伪造头用作限流身份 |

若已有缺陷不属于安全问题，可在此记录待办引用或接受理由，不阻塞合并。

## Recurring

| 类别 | 出现过的变更 | 固化措施 |
| --- | --- | --- |
| 指标使用原始请求路径而非路由模板 | `rate-limit`、`auth-throttle` | `CLAUDE.md` 的“Claude 容易犯的错误”：指标使用标准化路由模板，原始路径基数无界 |

## Round summary

| 轮次 | 阶段 | 发布发现数 | 去重数 | 复核拒绝数 |
| --- | --- | --- | --- | --- |
| 1 | Plan | 2 | 0 | 1 |
| 2 | Code | 4 | 0 | 2 |
| 3 | Code | 0 | 3 | 0 |
