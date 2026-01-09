# 订单簿采集系统审计报告

> 审计日期: 2026-01-09  
> 范围: `raw.crypto_order_book`, `raw.crypto_order_book_tick`, `order_book.py`  
> 状态: **修复完成** (剩余 1 个待完善项)

---

## 1. 摘要

| 项目 | 内容 |
|:---|:---|
| 总体风险 | 低 (核心幂等与观测已补齐) |
| 风险计分 | Critical 0 / High 0 / Medium 0 / Low 1 |
| 关键修复 | `lastUpdateId` 采集与乱序检测、列顺序一致、写库错误可观测 |
| 待处理 | `transaction_time (T)` 未采集 (cryptofeed 限制) |

---

## 2. 表结构

### 2.1 raw.crypto_order_book_tick (L1 Tick)

| 分类 | 字段 | 类型 | 说明 |
|:---|:---|:---|:---|
| 主键 | exchange | TEXT | 交易所 |
| 主键 | symbol | TEXT | 交易对 |
| 主键 | timestamp | TIMESTAMPTZ | 快照时间 |
| 价格 | mid_price | NUMERIC(38,18) | 中间价 |
| 价格 | spread_bps | NUMERIC(10,4) | 价差基点 |
| 最优档 | bid1_price/size | NUMERIC | 最优买价/量 |
| 最优档 | ask1_price/size | NUMERIC | 最优卖价/量 |
| 深度 | bid/ask_depth_1pct | NUMERIC(38,8) | 1%内深度 |
| 深度 | imbalance | NUMERIC(10,6) | 买卖失衡 |
| 血缘 | source, ingest_batch_id, source_event_time, ingested_at, updated_at | - | 与 kline 一致 |

**存储**: chunk=6h, compress=6h, segmentby=exchange,symbol

### 2.2 raw.crypto_order_book (L2 Full)

| 分类 | 字段 | 类型 | 说明 |
|:---|:---|:---|:---|
| 主键 | exchange, symbol, timestamp | - | 同上 |
| 元数据 | last_update_id | BIGINT | Binance lastUpdateId |
| 元数据 | transaction_time | TIMESTAMPTZ | Binance T (待采集) |
| 元数据 | depth | INT | 档位数 |
| 价格 | mid_price, spread, spread_bps | NUMERIC | 预计算指标 |
| 最优档 | bid1/ask1_price/size | NUMERIC | 最优档位 |
| 深度 | bid/ask_depth_1pct/5pct | NUMERIC | 深度统计 |
| 深度 | bid/ask_notional_1pct/5pct | NUMERIC | 名义价值 |
| 深度 | imbalance | NUMERIC | 买卖失衡 |
| 原始 | bids, asks | JSONB | `[["price","qty"],...]` |
| 血缘 | 5字段 | - | 与 kline 一致 |

**存储**: chunk=1d, compress=1d, segmentby=exchange,symbol

### 2.3 原始格式对照

| Binance 字段 | 数据库字段 | 状态 |
|:---|:---|:---|
| `lastUpdateId` | `last_update_id` | OK (sequence_number) |
| `E` (event_time) | `timestamp` | OK |
| `T` (transaction_time) | `transaction_time` | 待采集 |
| `bids/asks` | `bids/asks` (JSONB) | OK (原始格式) |

---

## 3. 代码要点

### 3.1 数据完整性

```python
# 提取 lastUpdateId
last_update_id = getattr(book, 'sequence_number', None)

# 乱序检测
if last_update_id < prev_id:
    self._stats["out_of_order"] += 1
    metrics.inc("order_book_out_of_order")
    return  # 跳过乱序数据
```

### 3.2 双层采样

- **Tick 层 (1s)**: 轻量行，仅 top-of-book + 核心指标
- **Full 层 (5s)**: 完整盘口 + 深度统计

### 3.3 可观测性

| 指标 | 说明 |
|:---|:---|
| `order_book_tick_written` | tick 写入行数 |
| `order_book_full_written` | full 写入行数 |
| `order_book_write_errors` | 写入错误次数 |
| `order_book_out_of_order` | 乱序跳过次数 |

---

## 4. 验证清单

### 4.1 DDL

```sql
\d raw.crypto_order_book_tick
\d raw.crypto_order_book
SELECT indexname FROM pg_indexes 
WHERE tablename IN ('crypto_order_book_tick','crypto_order_book');
```

### 4.2 数据

```sql
-- lastUpdateId 非空
SELECT symbol, timestamp, last_update_id 
FROM raw.crypto_order_book 
WHERE last_update_id IS NOT NULL
ORDER BY timestamp DESC LIMIT 5;

-- 档位数
SELECT symbol, depth, jsonb_array_length(bids) AS bid_levels
FROM raw.crypto_order_book ORDER BY timestamp DESC LIMIT 5;

-- 原始格式
SELECT bids->0->0 AS price, bids->0->1 AS qty
FROM raw.crypto_order_book LIMIT 1;
-- 预期: "91114.00", "16.841"
```

### 4.3 代码

```bash
cd services-preview/markets-service
.venv/bin/python -m py_compile src/crypto/collectors/order_book.py
ORDER_BOOK_SYMBOLS=BTC .venv/bin/python -m src.crypto.collectors.order_book
```

---

## 5. 残留风险

| 优先级 | 项目 | 说明 | 建议 |
|:---|:---|:---|:---|
| P1 | transaction_time | cryptofeed 不提供 | 改用原生 WS 或接受缺失 |
| P2 | 历史数据校验 | 修复前可能错位 | 抽样比对 |
| P2 | 指标告警 | 需接入监控 | Prometheus 阈值告警 |

---

## 6. 存储估算

| 表 | 采样 | 日存储 (压缩) | 月存储 (4币) |
|:---|:---|:---|:---|
| tick | 1s | ~17 MB | ~0.5 GB |
| full | 5s | ~500 MB | ~15 GB |

---

## 7. 配置

```bash
ORDER_BOOK_TICK_INTERVAL=1     # tick 采样 (秒)
ORDER_BOOK_FULL_INTERVAL=5     # full 采样 (秒)
ORDER_BOOK_DEPTH=1000          # 每侧档位数
ORDER_BOOK_SYMBOLS=            # 可选，逗号分隔
```

---

## 8. 变更历史

| 日期 | 变更 |
|:---|:---|
| 2026-01-09 | 初始设计: 双层采样架构 |
| 2026-01-09 | 修复: 字段顺序、血缘字段、索引 |
| 2026-01-09 | 修复: 原始格式 `[["price","qty"],...]` |
| 2026-01-09 | 修复: lastUpdateId 采集、乱序检测 |
| 2026-01-09 | 增强: 错误日志、统计指标 |
