# 订单簿采集系统审计报告

> 审计日期: 2026-01-09  
> 审计范围: `raw.crypto_order_book`, `raw.crypto_order_book_tick`, `order_book.py`  
> 审计状态: **已修复**

---

## 1. 摘要

| 项目 | 内容 |
|:---|:---|
| 审计输入 | DDL + 采集器代码 |
| 总体风险 | 低 (修复后) |
| 风险计分 | Critical 0 / High 0 / Medium 0 / Low 1 |
| 关键修复 | lastUpdateId 采集、乱序检测、错误可观测性 |

---

## 2. 表结构设计

### 2.1 raw.crypto_order_book_tick (L1 Tick 层)

```
+-----+-------------------+---------------+----------+---------+---------------------------+
| No. | Column            | Type          | Nullable | Default | Description               |
+-----+-------------------+---------------+----------+---------+---------------------------+
|  1  | exchange          | TEXT          | NOT NULL |         | 交易所                    |
|  2  | symbol            | TEXT          | NOT NULL |         | 交易对                    |
|  3  | timestamp         | TIMESTAMPTZ   | NOT NULL |         | 快照时间                  |
+-----+-------------------+---------------+----------+---------+---------------------------+
|  4  | mid_price         | NUMERIC(38,18)|          |         | 中间价                    |
|  5  | spread_bps        | NUMERIC(10,4) |          |         | 价差基点                  |
|  6  | bid1_price        | NUMERIC(38,18)|          |         | 最优买价                  |
|  7  | bid1_size         | NUMERIC(38,18)|          |         | 最优买量                  |
|  8  | ask1_price        | NUMERIC(38,18)|          |         | 最优卖价                  |
|  9  | ask1_size         | NUMERIC(38,18)|          |         | 最优卖量                  |
| 10  | bid_depth_1pct    | NUMERIC(38,8) |          |         | 买侧1%深度                |
| 11  | ask_depth_1pct    | NUMERIC(38,8) |          |         | 卖侧1%深度                |
| 12  | imbalance         | NUMERIC(10,6) |          |         | 买卖失衡 [-1,1]           |
+-----+-------------------+---------------+----------+---------+---------------------------+
| 13  | source            | TEXT          | NOT NULL | binance_ws | 数据源                 |
| 14  | ingest_batch_id   | BIGINT        |          |         | 采集批次ID                |
| 15  | source_event_time | TIMESTAMPTZ   |          |         | 源事件时间                |
| 16  | ingested_at       | TIMESTAMPTZ   | NOT NULL | now()   | 入库时间                  |
| 17  | updated_at        | TIMESTAMPTZ   | NOT NULL | now()   | 更新时间                  |
+-----+-------------------+---------------+----------+---------+---------------------------+
| PK: (exchange, symbol, timestamp)                                                      |
| Indexes: symbol_time, time, batch_id, spread(partial), imbalance(partial)              |
| Chunk: 6h | Compress: 6h | Segmentby: exchange,symbol                                 |
+----------------------------------------------------------------------------------------+
```

### 2.2 raw.crypto_order_book (L2 Full 层)

```
+-----+-------------------+---------------+----------+---------+---------------------------+
| No. | Column            | Type          | Nullable | Default | Description               |
+-----+-------------------+---------------+----------+---------+---------------------------+
|  1  | exchange          | TEXT          | NOT NULL |         | 交易所                    |
|  2  | symbol            | TEXT          | NOT NULL |         | 交易对                    |
|  3  | timestamp         | TIMESTAMPTZ   | NOT NULL |         | 事件时间 (E)              |
+-----+-------------------+---------------+----------+---------+---------------------------+
|  4  | last_update_id    | BIGINT        |          |         | 序列号 (lastUpdateId)     |
|  5  | transaction_time  | TIMESTAMPTZ   |          |         | 交易时间 (T)              |
|  6  | depth             | INT           | NOT NULL |         | 档位数                    |
+-----+-------------------+---------------+----------+---------+---------------------------+
|  7  | mid_price         | NUMERIC(38,18)|          |         | 中间价                    |
|  8  | spread            | NUMERIC(38,18)|          |         | 价差                      |
|  9  | spread_bps        | NUMERIC(10,4) |          |         | 价差基点                  |
| 10  | bid1_price        | NUMERIC(38,18)|          |         | 最优买价                  |
| 11  | bid1_size         | NUMERIC(38,18)|          |         | 最优买量                  |
| 12  | ask1_price        | NUMERIC(38,18)|          |         | 最优卖价                  |
| 13  | ask1_size         | NUMERIC(38,18)|          |         | 最优卖量                  |
+-----+-------------------+---------------+----------+---------+---------------------------+
| 14  | bid_depth_1pct    | NUMERIC(38,8) |          |         | 买侧1%深度                |
| 15  | ask_depth_1pct    | NUMERIC(38,8) |          |         | 卖侧1%深度                |
| 16  | bid_depth_5pct    | NUMERIC(38,8) |          |         | 买侧5%深度                |
| 17  | ask_depth_5pct    | NUMERIC(38,8) |          |         | 卖侧5%深度                |
| 18  | bid_notional_1pct | NUMERIC(38,8) |          |         | 买侧1%名义价值(USDT)      |
| 19  | ask_notional_1pct | NUMERIC(38,8) |          |         | 卖侧1%名义价值            |
| 20  | bid_notional_5pct | NUMERIC(38,8) |          |         | 买侧5%名义价值            |
| 21  | ask_notional_5pct | NUMERIC(38,8) |          |         | 卖侧5%名义价值            |
| 22  | imbalance         | NUMERIC(10,6) |          |         | 买卖失衡                  |
+-----+-------------------+---------------+----------+---------+---------------------------+
| 23  | bids              | JSONB         | NOT NULL |         | 买盘 [["price","qty"],...] |
| 24  | asks              | JSONB         | NOT NULL |         | 卖盘 [["price","qty"],...] |
+-----+-------------------+---------------+----------+---------+---------------------------+
| 25  | source            | TEXT          | NOT NULL | binance_ws | 数据源                 |
| 26  | ingest_batch_id   | BIGINT        |          |         | 采集批次ID                |
| 27  | source_event_time | TIMESTAMPTZ   |          |         | 原始事件时间              |
| 28  | ingested_at       | TIMESTAMPTZ   | NOT NULL | now()   | 入库时间                  |
| 29  | updated_at        | TIMESTAMPTZ   | NOT NULL | now()   | 更新时间                  |
+-----+-------------------+---------------+----------+---------+---------------------------+
| PK: (exchange, symbol, timestamp)                                                      |
| Indexes: symbol_time, time, batch_id, spread(partial)                                  |
| Chunk: 1d | Compress: 1d | Segmentby: exchange,symbol                                 |
+----------------------------------------------------------------------------------------+
```

### 2.3 原始数据格式对照

| Binance 原始字段 | 数据库字段 | 说明 |
|:---|:---|:---|
| `lastUpdateId` | `last_update_id` | 序列号，用于乱序检测 |
| `E` (event_time) | `timestamp` | 事件时间，主键 |
| `T` (transaction_time) | `transaction_time` | 交易时间 (待采集) |
| `bids` | `bids` (JSONB) | 原始格式 `[["price","qty"],...]` |
| `asks` | `asks` (JSONB) | 原始格式 `[["price","qty"],...]` |

---

## 3. 规范对齐检查

### 3.1 与 crypto_kline_1m 对比

| 设计项 | crypto_kline_1m | crypto_order_book | 状态 |
|:---|:---|:---|:---|
| 字段顺序 | exchange,symbol,open_time | exchange,symbol,timestamp | OK |
| 主键 | (exchange,symbol,open_time) | (exchange,symbol,timestamp) | OK |
| 血缘字段 | 5字段 | 5字段 (相同) | OK |
| 索引 | symbol_time,time,batch_id | symbol_time,time,batch_id | OK |
| 压缩分段 | exchange,symbol | exchange,symbol | OK |
| 保留策略 | 注释 (不自动删除) | 注释 (不自动删除) | OK |

### 3.2 数据完整性

| 检查项 | 状态 | 说明 |
|:---|:---|:---|
| 原始档位数 | OK | 1000档/侧，可配置 |
| 原始格式 | OK | `[["price","qty"],...]` 字符串保留精度 |
| lastUpdateId | OK | 从 cryptofeed sequence_number 提取 |
| transaction_time | 待完善 | cryptofeed 不提供，字段预留 |
| 多交易所支持 | OK | exchange 字段区分 |

---

## 4. 安全审计发现与修复

### 4.1 已修复 (Medium → Resolved)

#### 4.1.1 缺失去重与序号校验

- **风险**: 重放/乱序数据可能污染订单簿
- **修复**: 
  - 提取 `book.sequence_number` 作为 `lastUpdateId`
  - 添加单调递增校验，拒绝乱序数据
  - 添加 `order_book_out_of_order` 指标

```python
# 乱序检测
if last_update_id < prev_id:
    self._stats["out_of_order"] += 1
    metrics.inc("order_book_out_of_order")
    logger.warning("乱序跳过: %s seq %d < %d", sym, last_update_id, prev_id)
    return
```

#### 4.1.2 错误静默吞掉

- **风险**: 写库失败时数据缺口无感知
- **修复**:
  - 添加 `exc_info=True` 输出完整堆栈
  - 添加丢失数据计数
  - 添加 `order_book_write_errors` 指标

```python
except Exception as e:
    self._stats["errors"] += 1
    metrics.inc("order_book_write_errors")
    logger.error("写入失败 (%d 条丢失): %s", len(rows), e, exc_info=True)
```

### 4.2 已修复 (Low → Resolved)

#### 4.2.1 采集列顺序不一致

- **风险**: 历史数据可能存在列错位
- **修复**: 统一 tick/full 表列顺序为 `exchange,symbol,timestamp,...`

### 4.3 待处理 (Low)

| 项目 | 说明 | 建议 |
|:---|:---|:---|
| transaction_time | cryptofeed 不提供 | 改用原生 WebSocket 或接受缺失 |
| 历史数据校验 | 修复前数据可能错位 | 手动抽样比对 |

---

## 5. 可观测性增强

### 5.1 新增指标

| 指标名 | 类型 | 说明 |
|:---|:---|:---|
| `order_book_tick_written` | Counter | tick 表写入行数 |
| `order_book_full_written` | Counter | full 表写入行数 |
| `order_book_write_errors` | Counter | 写入错误次数 |
| `order_book_out_of_order` | Counter | 乱序跳过次数 |

### 5.2 统计日志

每 60 秒输出一次运行统计:

```
INFO 统计: received=12000, tick=4000, full=800, errors=0, out_of_order=0
```

退出时输出最终统计:

```
INFO 采集结束统计: received=120000, tick=40000, full=8000, errors=0, out_of_order=0
```

---

## 6. 存储估算

### 6.1 单行存储

| 表 | 单行大小 (未压缩) | 单行大小 (压缩后) |
|:---|:---|:---|
| crypto_order_book_tick | ~200 bytes | ~50 bytes |
| crypto_order_book | ~50 KB | ~5-10 KB |

### 6.2 日存储量 (4币种)

| 表 | 采样间隔 | 每日快照数 | 每日存储 (压缩后) |
|:---|:---|:---|:---|
| tick | 1s | 345,600 | ~17 MB |
| full | 5s | 69,120 | ~500 MB |

### 6.3 月存储量

```
4币种 × 30天 ≈ 15 GB (压缩后)
```

---

## 7. 验证清单

### 7.1 DDL 验证

```sql
-- 检查表结构
\d raw.crypto_order_book_tick
\d raw.crypto_order_book

-- 检查索引
SELECT indexname FROM pg_indexes 
WHERE tablename IN ('crypto_order_book_tick', 'crypto_order_book');

-- 检查压缩策略
SELECT * FROM timescaledb_information.jobs 
WHERE proc_name = 'policy_compression';
```

### 7.2 数据验证

```sql
-- 检查 lastUpdateId 是否写入
SELECT symbol, timestamp, last_update_id 
FROM raw.crypto_order_book 
ORDER BY timestamp DESC LIMIT 5;

-- 检查档位数
SELECT symbol, depth, 
       jsonb_array_length(bids) as bid_levels,
       jsonb_array_length(asks) as ask_levels
FROM raw.crypto_order_book 
ORDER BY timestamp DESC LIMIT 5;

-- 验证原始格式
SELECT bids->0->0 as price, bids->0->1 as qty
FROM raw.crypto_order_book LIMIT 1;
-- 预期: "91114.00", "16.841" (字符串)
```

### 7.3 代码验证

```bash
# 语法检查
cd services-preview/markets-service
.venv/bin/python -m py_compile src/crypto/collectors/order_book.py

# 运行测试
ORDER_BOOK_SYMBOLS=BTC .venv/bin/python -m src.crypto.collectors.order_book
```

---

## 8. 配置参考

```bash
# config/.env
ORDER_BOOK_TICK_INTERVAL=1     # tick 采样间隔 (秒)
ORDER_BOOK_FULL_INTERVAL=5     # full 采样间隔 (秒)
ORDER_BOOK_DEPTH=1000          # 每侧档位数
ORDER_BOOK_RETENTION_DAYS=30   # 保留天数 (仅供参考，默认不删除)
ORDER_BOOK_SYMBOLS=            # 可选，逗号分隔
```

---

## 9. 变更历史

| 日期 | 变更 | 审计员 |
|:---|:---|:---|
| 2026-01-09 | 初始设计: 双层采样架构 | - |
| 2026-01-09 | 修复: 字段顺序、血缘字段、索引 | - |
| 2026-01-09 | 修复: 原始格式存储 `[["price","qty"],...]` | - |
| 2026-01-09 | 修复: lastUpdateId 采集、乱序检测 | - |
| 2026-01-09 | 增强: 错误日志、统计指标 | - |

---

## 10. 附录

### A. 原始 Binance API 响应

```json
{
  "lastUpdateId": 9632865900189,
  "E": 1767941019719,
  "T": 1767941019709,
  "bids": [
    ["91114.00", "16.841"],
    ["91113.90", "0.004"],
    ...
  ],
  "asks": [
    ["91114.10", "3.319"],
    ["91114.20", "0.008"],
    ...
  ]
}
```

### B. cryptofeed 字段映射

| cryptofeed 属性 | Binance 字段 | 数据库字段 |
|:---|:---|:---|
| `book.timestamp` | `E` | `timestamp` |
| `book.sequence_number` | `lastUpdateId` | `last_update_id` |
| `book.book.bids` | `bids` | `bids` |
| `book.book.asks` | `asks` | `asks` |
| - | `T` | `transaction_time` (未采集) |
