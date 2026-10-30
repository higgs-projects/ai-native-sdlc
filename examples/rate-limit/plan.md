# Plan: 公开 API 限流 (from intent.md 2026-09-02)

## Files that change

- `src/middleware/rateLimit.ts`：身份推导、Redis 滑动窗口检查及响应头。
- `src/routes/public.ts`：在公开路由功能开关后安装中间件。
- `src/config/rateLimit.ts`：额度、窗口、Redis 前缀及发布开关设置。
- `src/metrics/api.ts`：有界拒绝指标和存储错误指标。
- `test/middleware/rateLimit.test.ts`：额度、响应头、身份、Redis 故障及并发覆盖。
- `docs/public-api.md`：公开限额及 `429` 响应契约。

## Order of work

1. 增加带校验的限流配置和默认关闭的功能开关。
2. 实现原子 Redis 滑动窗口及身份哈希，不记录身份值。
3. 增加中间件和标准响应头，仅接入 `/v1/public`。
4. 增加指标及结构化、脱敏的运维日志。
5. 增加单元和集成测试，发布 API 文档。
6. 真人审查看板及回滚说明后，为 10% 公开流量启用开关。

## Risks

Redis 故障放行会降低防滥用能力。错误路由模板可能产生高基数指标。代理配置可能使来源 IP 不可靠。功能开关回滚必须移除限流，同时不改变已有认证。

## Proof

测试证明第 121 次请求被拒绝、响应头正确、不同 API key 配额独立、原始 IP 和 key 不进入日志或指标、Redis 故障时放行并增加存储错误指标，以及并发不会突破额度。预发布压测验证公开路由 p99 低于 400 ms。

## Deviations
None.
