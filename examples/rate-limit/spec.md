# Specification: 公开 API 限流

## Requirements

- 对 `/v1/public` 下所有路由采用滚动 60 秒窗口，固定额度 120 次。
- 有有效 key 时按 API-key ID 标识调用者，否则使用客户端 IP 的加盐哈希。
- 额度耗尽时，在应用执行工作前返回 `429`，携带 `Retry-After`、`RateLimit-Limit`、`RateLimit-Remaining` 和 `RateLimit-Reset`。
- 增加 `public_api_rate_limit_rejections_total` 指标，仅以路由模板和身份类型为标签。
- Redis 不可用时放行，记录 `public_api_rate_limit_store_error_total`，不在日志记录 key 或原始 IP。

## Design

网关中间件推导身份 token，再原子更新 Redis 有序集合滑动窗口，TTL 为 65 秒。键由路由模板和身份 token 组成。对允许和拒绝请求均写标准响应头。通过功能开关按路由组启用，初始覆盖 10% 公开流量。

## Organization skill constraints

- Security：限流键使用 API-key ID，或以服务端持有的轮换秘密对 IP 做 HMAC-SHA-256 哈希；不记录原始身份值。
- Compliance：IP 哈希配额键 65 秒内过期，不导出到分析系统。
- Data：指标仅使用有界路由模板和身份类型，避免高基数身份标签。

## Flagged concerns

- Redis 故障放行保护可用性，但可能临时允许滥用；API Platform 负责告警和故障复盘。
- IPv6 隐私地址可能频繁变化；Security 必须批准是否需要独立策略。

## Extension contract

- Extension：网关中间件契约 v1；输入为请求上下文，输出为允许／拒绝及限流响应头；Redis 错误时放行并产生运维指标。
