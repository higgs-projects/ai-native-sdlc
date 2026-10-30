# Intent: 调查公开 API 限流延迟回归
Author: API Platform on-call. Status: draft.

## 越界报告
2026-09-02 14:20 UTC，限流覆盖达到 100% 后，`public_api_p99_latency_ms` 连续 14 分钟保持 860 ms，超过 700 ms 的第 2 级阈值。错误率低于 0.4%。链路样本显示新增 Redis 配额命令在受影响请求中耗时 390–510 ms。14:05 UTC 的部署是越界窗口内唯一部署。

## Problem
公开 API 请求虽然成功，但客户在启用限流后经历超过已批准 p99 控制带的延迟。

## Proposed outcome
确定配额存储延迟上升原因，形成安全、可衡量的变更，使公开 API p99 恢复到 400 ms 以下，不削弱已批准的 120 次请求限额。

## Affected users and systems
影响公开 API 使用者、网关中间件、Redis 配额集群、API Platform 看板及值班事件响应。

## Constraints
未经人工事件授权，不改变生产限流、Redis 拓扑或功能开关。保留身份哈希、响应头及故障放行策略。诊断仅使用只读链路、Redis 指标和部署历史。

## Open questions
回归由跨区域 Redis 路由、连接池饱和还是有序集合操作导致？是否仅某个可用区的 Redis 命令耗时上升？

Confidence: medium — 部署时间和链路 span 强烈关联配额调用与延迟，但尚无法区分网络路由和 Redis 饱和。

Evidence: 14:20–14:34 UTC 看板窗口；`/v1/public/search` 链路样本；Redis 命令延迟看板；14:05 UTC 部署记录。
