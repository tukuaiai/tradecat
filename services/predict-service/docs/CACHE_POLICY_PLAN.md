# 信号缓存与清理策略：配置评估与执行方案
时间：2025-12-17  
范围：`services/telegram-service` 内的信号检测、市场数据与翻译缓存

## 1. 目标与原则
- 保证套利/风控信号的新鲜度，优先时效再追求覆盖面。
- 所有状态有界：每个缓存/队列必须具备 TTL 与容量上限，极端行情不导致 OOM。
- 监控驱动调参：暴露命中率、丢弃量、队列深度指标，依据数据迭代。

## 2. 推荐配置对照表（最优方案）
+------------------------------+----------------------+-------------------------------+------------------------------------+
| 模块                         | 现状                 | 建议/已落地                    | 目的                               |
|------------------------------+----------------------+-------------------------------+------------------------------------|
| 套利检测器 priceCache        | TTL 2h / 50万 / Δt≤5s | TTL 60s / 上限20万 / Δt≤1.5s     | 确保报价同步，限制内存             |
| 订单簿缓存                   | TTL 2h / 无上限      | TTL 30m / 全局20万市场          | 高频数据有界，避免极端膨胀         |
| 价格突变缓存                 | 无上限 / 日志新增     | TTL 30m / 全局20万 / 触发时记日志 | 控制高频波动缓存，降低噪声         |
| 新市场 seenMarkets           | 阈值5万 / 保留3万    | 按交易所分桶：阈10k/桶、保5k/桶、TTL 24h | 避免单桶哈希膨胀                   |
| 市场数据 marketData          | 无TTL / 无上限       | TTL 30m / 全局20万 / 5m cleanup   | 热数据保鲜，限制内存               |
| 翻译缓存 TranslationCache    | LRU 2000 / 无TTL      | LRU 2000 + TTL 60m               | 防止长期冷数据占用                 |
| 主进程队列 activeTokens/msg  | 无上限               | 全局活跃token≤10k；消息类型≤10k  | backpressure，防止消息堆积         |
+------------------------------+----------------------+-------------------------------+------------------------------------+

## 3. 执行步骤（按优先级落地）
1) 套利检测 (`signals/arbitrage/detector.js`)
   - 调整 `CACHE_TTL=60000`、`MAX_CACHE_SIZE=200000`、时间差阈值 `<=1500ms`。
   - cleanup 周期 5 分钟；拒收无撮合时间戳或时间戳过旧的报价。
2) 高频缓存有界化
   - `signals/orderbook/detector.js`：TTL 30 分钟；每市场 5000、全局 20 万；溢出丢旧并计数告警。
   - `signals/price-spike/detector.js`：TTL 30 分钟；全局 20 万；仅在触发或丢弃时记录日志。
   - `utils/marketData.js`：TTL 30 分钟；全局 20 万；cleanup 间隔 5 分钟；命中率 <80% 时自动收紧 TTL/容量（可选）。
3) 新市场检测 (`signals/new-market/detector.js`)
   - seenMarkets 按交易所分桶；每桶阈值 10000，保留 5000；TTL 24h；每日滚动清理。
4) 翻译缓存 (`translation/cache.js`)
   - 保持 `maxSize=2000`，新增 `TTL=60m`；持久化写盘节流（如 5 分钟一次）防止频繁 I/O。
5) 主进程 backpressure (`bot.js`)
   - 为 activeTokens/message 队列设置 per-exchange/market 上限（建议 10k）与令牌桶速率。
   - 超限策略：丢弃最旧 + 告警；告警暴露队列长度与丢弃数。

## 4. 监控与验收标准
- 内存：RSS 稳定在预期范围，GC Pause 不超过基线 20%。
- 新鲜度：套利信号时间差 P95 ≤ 1.5s；有效信号命中率不下降超过 5%。
- 丢弃率：各缓存溢出丢弃率 < 1%；队列丢弃触发告警但不影响主流程。
- 命中率：marketData/translation 缓存命中率 ≥ 80%，低于阈值时自动调参或给出告警。

## 5. 风险与回滚
- 若信号量显著下降（>15%），优先放宽套利 `timeDiff` 到 2s 或 `CACHE_TTL` 到 120s。
- 若内存仍飙升，进一步收紧各全局上限或缩短 TTL；必要时临时关闭 price-spike 日志。
- 回滚路径：保留原参数为环境变量/配置项，直接回退为当前值（详见代码中的默认配置）。

## 6. 代码触点清单
- `services/telegram-service/signals/arbitrage/detector.js`
- `services/telegram-service/signals/orderbook/detector.js`
- `services/telegram-service/signals/price-spike/detector.js`
- `services/telegram-service/signals/new-market/detector.js`
- `services/telegram-service/utils/marketData.js`
- `services/telegram-service/translation/cache.js`
- `services/telegram-service/bot.js`

以上为落地执行的最小闭环文档，可直接据此按步骤修改并联调。***
