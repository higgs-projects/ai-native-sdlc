# Intent: 公开 API 限流
Author: API Platform. Status: accepted.

## Problem
匿名客户端可无限请求公开 API。单个高噪声客户端就能耗尽应用 worker，使合法客户请求缓慢或不可用。

## Proposed outcome
每个公开 API 客户端获得清晰、可预测的请求额度。超额请求返回 `429 Too Many Requests` 及重置元数据，正常客户流量维持在延迟 SLO 内。

## Affected users and systems
影响公开 API 使用者、API 网关中间件、Redis 配额存储、应用指标、支持 runbook 及值班响应人员。

## Constraints
存在 API key 时使用其身份，否则使用来源 IP。原始 IP 保留时间不得超过配额窗口。发布期间保留已有认证端点行为。首版支持每身份每分钟 120 次请求，仅当 Redis 不可用时故障放行，并告警。

## Open questions
首版是否为企业 API key 提供有文档说明的更高限额，还是同样每分钟 120 次？
