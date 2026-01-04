# 性能调优报告（不中断覆盖/信号质量版）
日期：2025-12-17
范围：services/telegram-service

## 目标
- 在不缩短监控窗口、不降低信号覆盖的前提下，降低内存占用与清理抖动。
- 通过更聪明的淘汰策略、精简存储和水位自适应，保持低 GC 压力和稳定延迟。

## 现状风险点
- orderbook/price-spike 使用全局 Map + 数组，市场数多时清理需排序，偶发长 STW。
- marketData 每条含 question/description，单条占用大；无容量分桶，仅按时间清理。
- priceCache/price-spike 存全量序列，活跃度低的市场也保留，浪费内存。
- activeTokens/messageCount 仅全局上限，无冷热区分，冷 token 可能长期占位。

## 不降覆盖的调优思路
1) **聪明淘汰（活跃优先）**
   - 为 priceCache/orderbook/price-spike 引入 `lastAccess`，清理时按最久未访问淘汰，优先保留活跃市场。
   - 清理分批 chunk（如 5k 一批），避免一次性大删除导致事件循环停顿。

2) **精简存储**
   - marketData 仅缓存 slug/eventSlug/question/token_ids/timestamp，description 不入内存；需要时临时拉取。
   - price-spike 历史改存「首价/末价/极值」摘要而非完整序列，保持涨跌幅检测准确性。

3) **分桶有界化（不减总覆盖）**
   - activeTokens/orderbook/price-spike 按 exchange/chain 分桶；每桶上限（如 3k），超限淘汰冷门 token/市场。
   - new-market 已分桶：保持 TTL 24h 与桶上限 10k/保留 5k。

4) **水位自适应**
   - 设内存水位阈值（如 heapUsedMB > 400）：临时把 TTL/上限收紧 2x，回落后恢复，避免持久“阉割”。
   - 清理日志记录水位与收紧状态，便于回溯。

5) **监控与指标**
   - 暴露：cache hit/miss、丢弃数、per-bucket size、清理耗时、heap 水位；用于判断是否需要进一步收紧。

## 建议的实现顺序
1) marketData 精简字段（去 description）并保留 slug/question；仍保持 TTL 30m/上限 20 万。
2) price-spike 改为摘要存储，保持窗口与检测逻辑不变。
3) priceCache/orderbook/price-spike 清理：改为 LRU/最久未访问 + 分批删除。
4) activeTokens/orderbook/price-spike 分桶上限，淘汰冷 token；不动总窗口。
5) 内存水位自适应收紧/回弹；增加清理耗时与水位日志。

## 验收标准
- RSS/heap 在高峰不超过现有基线 +20%；GC Pause 明显下降（可用 `--trace_gc` 或采样）。
- 信号数量与覆盖不下降超 5%；如下降，回溯是否收紧误杀活跃市场。
- 清理日志显示分批删除，单次清理耗时可控（目标 <50ms）。

## 回滚策略
- 保留旧参数为配置项：若信号下降或覆盖不足，关闭水位收紧、恢复 FIFO 淘汰策略。
- marketData 如需 description，可通过配置开关重新持久化该字段。

