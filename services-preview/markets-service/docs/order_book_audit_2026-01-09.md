# 订单簿采集系统审计报告（保存版）
> 审计日期：2026-01-09  
> 范围：`raw.crypto_order_book`、`raw.crypto_order_book_tick`、`services-preview/markets-service/src/crypto/collectors/order_book.py`  
> 状态：修复完成（剩余 1 个待完善项）

## 1. 摘要
- 总体风险：低（核心幂等与观测已补齐，仍缺交易时间 T 采集）
- 计分：Critical 0 / High 0 / Medium 0 / Low 1
- 关键修复：`lastUpdateId` 采集与乱序检测、列顺序一致、写库错误可观测
- 待处理：`transaction_time (T)` 未采集，消费侧需降级或改用原生 WS 获取

## 2. 表结构要点
- `raw.crypto_order_book_tick`：PK `(exchange,symbol,timestamp)`；chunk 6h，compress 6h；索引 `symbol_time/time/batch/spread/imbalance`。
- `raw.crypto_order_book`：PK `(exchange,symbol,timestamp)`；含 `last_update_id`、`transaction_time` 预留；chunk 1d，compress 1d；索引 `symbol_time/time/batch/spread`。
- 两表血缘字段与 `crypto_kline_1m` 对齐：`source/ingest_batch_id/source_event_time/ingested_at/updated_at`。

## 3. 代码要点（采集器）
- `_on_book`：提取 `book.sequence_number` 写入 `last_update_id`；若序号倒退则跳过并计数 `order_book_out_of_order`。
- Tick/Full 双缓冲；列顺序统一为 `exchange, symbol, timestamp, ...`。
- 错误处理：写库异常计数 `order_book_write_errors` 并输出堆栈。

## 4. 观测与验证
- 新增指标：`order_book_tick_written`、`order_book_full_written`、`order_book_write_errors`、`order_book_out_of_order`。
- 推荐验证：
  - 抽样 SQL：检查 `last_update_id` 非空、档位数、原始格式 `"[\"price\",\"qty\"]"`。
  - 乱序模拟：重复/倒序 `lastUpdateId` 事件应被拒。
  - 语法检查：`cd services-preview/markets-service && .venv/bin/python -m py_compile src/crypto/collectors/order_book.py`
  - 运行测试（需 DB/代理）：`ORDER_BOOK_SYMBOLS=BTC .venv/bin/python -m src.crypto.collectors.order_book`

## 5. 残留风险与行动项
| 优先级 | 项目 | 说明 | 建议 |
|:--|:--|:--|:--|
| P1 | 采集 `transaction_time (T)` | cryptofeed 不提供 | 若需严格顺序，用 Binance 原生 WS 获取 T；否则在消费端明确忽略 |
| P2 | 历史数据抽样 | 修复前可能有列错位或空序号 | 抽样比对修复前窗口；必要时回填/截断 |
| P2 | 指标告警 | 需接入 Prometheus/告警 | 对 `order_book_out_of_order` 与写入错误设阈值告警 |

## 6. 存储估算（4 币种，压缩后）
- Tick（1s）：~17 MB/天；Full（5s）：~0.5 GB/天；约 15 GB/月。

## 7. 参考 SQL 片段
```sql
-- 表结构与索引
\\d raw.crypto_order_book_tick;
\\d raw.crypto_order_book;
SELECT indexname FROM pg_indexes WHERE tablename IN ('crypto_order_book_tick','crypto_order_book');
-- 压缩策略
SELECT * FROM timescaledb_information.jobs WHERE proc_name = 'policy_compression';
-- 数据抽样
SELECT symbol, timestamp, last_update_id, jsonb_array_length(bids) AS bid_levels
FROM raw.crypto_order_book ORDER BY timestamp DESC LIMIT 5;
```

## 8. 变更快照
- DDL：`services-preview/markets-service/scripts/ddl/03_raw_crypto.sql`
- 代码：`services-preview/markets-service/src/crypto/collectors/order_book.py`

（完）
