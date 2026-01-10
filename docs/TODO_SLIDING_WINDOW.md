# 滑动窗口低占用方案 TODO

> 目标：7 周期各保留最新 500 根 K 线，存储从 99GB 降至 ~80MB

## 方案概述

| 周期 | 保留行数 | 时间窗口 | 存储/币种 |
|:---|:---|:---|:---|
| 1m | 500 | 8.3 小时 | ~100KB |
| 5m | 500 | 1.7 天 | ~100KB |
| 15m | 500 | 5.2 天 | ~100KB |
| 1h | 500 | 20.8 天 | ~100KB |
| 4h | 500 | 83 天 | ~100KB |
| 1d | 500 | 1.4 年 | ~100KB |
| 1w | 500 | 9.6 年 | ~100KB |

**总计**: 600 币种 × 3500 行 = 210 万行 ≈ 80MB（压缩后）

---

## Phase 1: Retention Policy 方案（零代码改动）

### TODO

- [ ] **1.1** 备份当前 retention policy 配置
  ```bash
  psql -h localhost -p 5433 -U postgres -d market_data -c \
    "SELECT * FROM timescaledb_information.jobs WHERE proc_name = 'policy_retention';" > backup_retention.sql
  ```

- [ ] **1.2** 创建新 retention policy SQL
  - 文件: `scripts/ddl/sliding_window_retention.sql`
  - 内容: 各周期 500 根对应的时间间隔

- [ ] **1.3** 添加配置项到 `config/.env.example`
  ```bash
  # 滑动窗口配置
  CANDLE_WINDOW_SIZE=500
  ENABLE_SLIDING_WINDOW=false  # 开关
  ```

- [ ] **1.4** 执行 retention policy 变更（测试环境）
  ```bash
  psql -h localhost -p 5433 -U postgres -d market_data -f scripts/ddl/sliding_window_retention.sql
  ```

- [ ] **1.5** 验证 retention policy 生效
  ```sql
  SELECT hypertable_name, schedule_interval, config 
  FROM timescaledb_information.jobs 
  WHERE proc_name = 'policy_retention';
  ```

- [ ] **1.6** 监控存储变化（等待自动清理）
  ```sql
  SELECT hypertable_name, total_bytes, compressed_total_bytes 
  FROM timescaledb_information.hypertable_compression_stats;
  ```

---

## Phase 2: 环形缓冲表方案（精确行数控制，可选）

### TODO

- [ ] **2.1** 设计 `candles_window` 表结构
  - 文件: `scripts/ddl/candles_window.sql`
  - 主键: `(exchange, symbol, interval, seq)`
  - seq: 0-499 环形索引

- [ ] **2.2** 创建表和索引

- [ ] **2.3** 修改 `data-service/src/adapters/timescale.py`
  - 新增 `upsert_candle_window()` 方法
  - 环形缓冲写入逻辑

- [ ] **2.4** 添加配置开关
  ```bash
  CANDLE_STORAGE_MODE=hypertable  # hypertable | window
  ```

- [ ] **2.5** 双写过渡期
  - 同时写入 `candles_1m` 和 `candles_window`
  - 验证数据一致性

- [ ] **2.6** 切换读取源
  - 修改 `trading-service` 读取逻辑
  - 修改 `telegram-service` 读取逻辑

---

## Phase 3: 内存滑动窗口（热数据加速，可选）

### TODO

- [ ] **3.1** 创建 `libs/common/sliding_window.py`
  - `CandleWindow` 类
  - `deque(maxlen=500)` 实现

- [ ] **3.2** 集成到 `trading-service`
  - 指标计算优先读内存
  - 冷启动从 DB 预热

- [ ] **3.3** 添加 Redis 持久化（可选）
  - 重启后快速恢复

---

## 验收标准

- [ ] 各周期保持最新 500 根 K 线
- [ ] 总存储 < 100MB
- [ ] 指标计算正常
- [ ] Telegram Bot 查询正常
- [ ] 无数据丢失告警

---

## 风险 & 回滚

### 风险
1. **1m 窗口仅 8 小时**: 部分长周期指标（EMA99）可能受影响
2. **历史回测受限**: 无法支持长周期回测

### 回滚步骤
```bash
# 恢复原 retention policy
psql -h localhost -p 5433 -U postgres -d market_data -f backup_retention.sql

# 或移除 retention policy
SELECT remove_retention_policy('market_data.candles_1m');
```

---

## 参考

- TimescaleDB Retention Policy: https://docs.timescale.com/use-timescale/latest/data-retention/
- 贪心计算结果: 7 周期全物理存储为最优解（请求数 vs 存储量平衡）
