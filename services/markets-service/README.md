# Markets Service

全市场数据采集服务 + 统一金融数据库

## 目录

- [数据库连接](#数据库连接)
- [数据库结构](#数据库结构)
- [数据概览](#数据概览)
- [命名规范](#命名规范)
- [表结构详情](#表结构详情)
- [物化视图](#物化视图)
- [数据源](#数据源)
- [架构设计](#架构设计)
- [快速开始](#快速开始)
- [DDL文件](#ddl文件)
- [配置](#配置)

---

## 数据库连接

```
postgresql://postgres:postgres@localhost:5434/market_data
```

---

## 数据库结构

```
market_data (数据库)
│
├── reference (元数据层 - 版本化)
│   ├── exchanges              # 交易所信息
│   ├── instruments            # 标的主数据
│   ├── trading_hours          # 交易时间
│   ├── symbol_mapping         # 跨源符号映射
│   └── data_sources           # 数据源配置
│
├── raw (原始时序数据层 - Hypertable)
│   ├── crypto_kline_1m        # 加密货币K线 1分钟
│   ├── crypto_metrics_5m      # 加密期货指标 5分钟
│   ├── us_equity_1d           # 美股日线
│   ├── cn_equity_1d           # A股日线
│   └── macro_series           # 宏观经济数据
│
├── agg (连续聚合物化视图 - 自动刷新)
│   ├── crypto_kline_*_mv      # K线多周期聚合 (5m/15m/1h/4h/1d/1w)
│   └── crypto_metrics_*_mv    # 期货指标聚合 (15m/1h/4h/1d/1w)
│
├── fundamental (基本面数据层)
│   ├── financial_statements   # 财务报表
│   ├── earnings_calendar      # 财报日历
│   └── corporate_actions      # 公司行动 (分红/拆股)
│
├── alternative (另类数据层)
│   ├── news_articles          # 新闻文章
│   ├── news_sentiment         # 新闻情感分析
│   └── economic_calendar      # 经济日历
│
├── indicators (指标层)
│   ├── indicator_data         # 技术指标 (RSI/MACD等)
│   ├── factor_values          # 因子值
│   └── signals                # 交易信号
│
└── quality (数据质量层 - 血缘追踪)
    ├── ingest_batches         # 采集批次
    ├── data_gaps              # 数据缺口
    ├── anomaly_log            # 异常日志
    ├── alert_rules            # 告警规则
    └── backfill_tasks         # 回填任务
```

---

## 数据概览

### 当前数据量

| 表 | 数据量 | 存储大小 | 时间范围 | 币种数 |
|:---|---:|---:|:---|---:|
| `raw.crypto_kline_1m` | 3.74 亿条 | 52 GB | 2018-01-01 ~ 2026-01-03 | 615 |
| `raw.crypto_metrics_5m` | 9400 万条 | 28 GB | 2021-12-01 ~ 2026-01-04 | 538 |
| `raw.us_equity_1d` | 0 | - | - | - |
| `raw.cn_equity_1d` | 0 | - | - | - |
| `raw.macro_series` | 0 | - | - | - |

### 元数据

| 表 | 数据量 |
|:---|---:|
| `reference.exchanges` | 16 |
| `reference.data_sources` | 7 |
| `quality.alert_rules` | 3 |

---

## 命名规范

### 原始表

```
{market}_{datatype}_{timeframe}
```

| 示例 | 说明 |
|:---|:---|
| `crypto_kline_1m` | 加密货币 K线 1分钟 |
| `crypto_metrics_5m` | 加密货币 期货指标 5分钟 |
| `us_equity_1d` | 美股 日线 |
| `cn_equity_1d` | A股 日线 |

### 物化视图

```
{market}_{datatype}_{timeframe}_mv
```

| 示例 | 说明 |
|:---|:---|
| `crypto_kline_5m_mv` | 加密货币 K线 5分钟 物化视图 |
| `crypto_metrics_1h_mv` | 加密货币 期货指标 1小时 物化视图 |

### 市场代码

| 代码 | 说明 |
|:---|:---|
| `crypto` | 加密货币 |
| `us_equity` | 美股 |
| `cn_equity` | A股 |
| `hk_equity` | 港股 |
| `futures` | 期货 |
| `forex` | 外汇 |
| `macro` | 宏观数据 |

---

## 表结构详情

### raw.crypto_kline_1m

加密货币 1 分钟 K线数据

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| exchange | TEXT | 交易所 (binanceusdm) |
| symbol | TEXT | 交易对 (BTCUSDT) |
| open_time | TIMESTAMPTZ | K线开始时间 |
| open | NUMERIC(38,18) | 开盘价 |
| high | NUMERIC(38,18) | 最高价 |
| low | NUMERIC(38,18) | 最低价 |
| close | NUMERIC(38,18) | 收盘价 |
| volume | NUMERIC(38,18) | 成交量 |
| quote_volume | NUMERIC(38,18) | 成交额 |
| trades | BIGINT | 成交笔数 |
| taker_buy_volume | NUMERIC(38,18) | 主动买入量 |
| is_closed | BOOLEAN | 是否已收盘 |
| source | TEXT | 数据源 |
| ingest_batch_id | BIGINT | 采集批次ID (血缘) |
| ingested_at | TIMESTAMPTZ | 入库时间 |

**主键**: `(exchange, symbol, open_time)`

**Hypertable**: chunk_interval = 1 day

### raw.crypto_metrics_5m

加密货币期货指标 (持仓量/多空比)

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| exchange | TEXT | 交易所 |
| symbol | TEXT | 交易对 |
| timestamp | TIMESTAMPTZ | 时间 |
| sumOpenInterest | NUMERIC | 持仓量 |
| sumOpenInterestValue | NUMERIC | 持仓价值 (USDT) |
| topAccountLongShortRatio | NUMERIC | 大户账户多空比 |
| topPositionLongShortRatio | NUMERIC | 大户持仓多空比 |
| globalLongShortRatio | NUMERIC | 全局多空比 |
| takerBuySellRatio | NUMERIC | 主动买卖比 |
| source | TEXT | 数据源 |
| ingest_batch_id | BIGINT | 采集批次ID |

**主键**: `(exchange, symbol, timestamp)`

**Hypertable**: chunk_interval = 1 day

---

## 物化视图

### 连续聚合 (TimescaleDB Continuous Aggregate)

所有物化视图自动增量刷新，无需手动操作。

#### K线聚合 (从 crypto_kline_1m)

| 视图 | 刷新间隔 | 说明 |
|:---|:---|:---|
| `agg.crypto_kline_5m_mv` | 每 5 分钟 | 5分钟K线 |
| `agg.crypto_kline_15m_mv` | 每 15 分钟 | 15分钟K线 |
| `agg.crypto_kline_1h_mv` | 每 1 小时 | 1小时K线 |
| `agg.crypto_kline_4h_mv` | 每 4 小时 | 4小时K线 |
| `agg.crypto_kline_1d_mv` | 每 1 天 | 日K线 |
| `agg.crypto_kline_1w_mv` | 每 1 周 | 周K线 |

#### 期货指标聚合 (从 crypto_metrics_5m)

| 视图 | 刷新间隔 | 说明 |
|:---|:---|:---|
| `agg.crypto_metrics_15m_mv` | 每 15 分钟 | 15分钟指标 |
| `agg.crypto_metrics_1h_mv` | 每 1 小时 | 1小时指标 |
| `agg.crypto_metrics_4h_mv` | 每 4 小时 | 4小时指标 |
| `agg.crypto_metrics_1d_mv` | 每 1 天 | 日指标 |
| `agg.crypto_metrics_1w_mv` | 每 1 周 | 周指标 |

### 查看刷新任务

```sql
SELECT job_id, application_name, schedule_interval, next_start
FROM timescaledb_information.jobs
WHERE proc_name = 'policy_refresh_continuous_aggregate';
```

---

## 数据源

### 联通性测试 (2026-01-04)

| Provider | 市场 | 测试符号 | 状态 | 数据量 | 备注 |
|:---|:---|:---|:---:|---:|:---|
| **ccxt** | 加密货币 | BTCUSDT | ✅ | 5 | 100+ 交易所 |
| **cryptofeed** | 加密WS | - | ✅ | - | WebSocket 流 |
| **yfinance** | 美股 | AAPL | ✅ | 21 | 免费 |
| **akshare** | A股 | 000001 | ✅ | 1455 | 免费 |
| **baostock** | A股 | 000001 | ✅ | 2674 | 历史数据长 |
| **fredapi** | 宏观 | DGS10 | ✅ | 15984 | 需 API Key |
| **quantlib** | 定价 | 期权 | ✅ | - | 本地计算 |
| **openbb** | 聚合 | AAPL | ✅ | 249 | 100+ 数据源 |

### 历史数据集

| 市场 | 数据源 | 链接 |
|:---|:---|:---|
| 加密货币 | Binance Vision | https://data.binance.vision/ |
| 加密货币 | HuggingFace | https://huggingface.co/datasets/123olp/binance-futures-ohlcv-2018-2026 |
| 美股 | Kaggle S&P 500 | https://www.kaggle.com/datasets/andrewmvd/sp-500-stocks |
| A股 | BaoStock | 通过 baostock 库 |
| 宏观 | FRED | https://fred.stlouisfed.org/ |

---

## 架构设计

### Provider + Router 模式

```
src/
├── core/                  # 核心框架
│   ├── fetcher.py         # TET Pipeline 基类 (Transform-Extract-Transform)
│   ├── registry.py        # Provider 注册表
│   ├── quality.py         # 数据质量监控
│   └── key_manager.py     # 多 Key 负载均衡
│
├── models/                # 标准化数据模型
│   ├── candle.py          # K线 (Candle)
│   ├── ticker.py          # 行情 (Ticker)
│   ├── trade.py           # 成交 (Trade)
│   └── instrument.py      # 统一标的标识 (Instrument)
│
├── providers/             # 数据源适配器 (8个)
│   ├── ccxt/              # 加密货币 REST (100+ 交易所)
│   ├── cryptofeed/        # 加密货币 WebSocket
│   ├── akshare/           # A股/港股/期货
│   ├── baostock/          # A股历史数据
│   ├── yfinance/          # 美股/港股/外汇
│   ├── fredapi/           # 美联储宏观数据
│   ├── quantlib/          # 期权/债券定价
│   └── openbb/            # 综合聚合 (备份)
│
├── collectors/            # 采集任务调度
│   ├── base.py            # Collector 基类
│   ├── crypto.py          # 加密货币采集器
│   ├── ashare.py          # A股采集器
│   └── macro.py           # 宏观数据采集器
│
├── routers/               # 统一路由层
│   └── market.py          # 自动检测市场并路由
│
└── storage/               # 存储层
    └── timescale.py       # TimescaleDB 适配器
```

### TET Pipeline

每个 Provider 实现 Transform-Extract-Transform 流程:

1. **Transform**: 验证并转换查询参数
2. **Extract**: 从数据源获取原始数据
3. **Transform**: 将原始数据转换为标准模型

### 统一标的标识 (Instrument)

解决跨数据源符号映射问题:

```python
# UID 格式: market.exchange.symbol
inst = Instrument(
    uid="crypto.binance.BTCUSDT",
    canonical_symbol="BTC/USDT",
    market="crypto",
    exchange="binance",
)

# 转换为不同 Provider 格式
inst.to_provider_symbol("ccxt")      # "BTC/USDT:USDT"
inst.to_provider_symbol("yfinance")  # "BTC-USD"
```

### 数据质量监控

```python
from src.core import quality_monitor, QualityMetrics

# 记录采集质量
metrics = QualityMetrics(
    provider="ccxt",
    symbol="BTCUSDT",
    records_fetched=100,
    latency_ms=150,
)
quality_monitor.record(metrics)
```

### 多 Key 负载均衡

```bash
# config/.env - 多个 Key 逗号分隔
FRED_API_KEY=key1,key2,key3
```

```python
from src.core import get_key_manager

km = get_key_manager("FRED_API_KEY")
key = km.get_key()  # 自动轮询
km.report_success(key)  # 或 report_error(key)
```

---

## 快速开始

### 初始化环境

```bash
cd services/markets-service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 测试数据源

```bash
# 美股
python -m src test --provider yfinance --symbol AAPL

# A股
python -m src test --provider akshare --symbol 000001
python -m src test --provider baostock --symbol 000001

# 加密货币
python -m src test --provider ccxt --symbol BTCUSDT

# 期权定价
python -m src pricing
```

### 数据库初始化

```bash
cd scripts
./init_market_db.sh localhost 5434 market_data
```

或手动执行:

```bash
PGPASSWORD=postgres psql -h localhost -p 5434 -U postgres -d market_data -f ddl/01_enums_schemas.sql
PGPASSWORD=postgres psql -h localhost -p 5434 -U postgres -d market_data -f ddl/02_reference.sql
# ... 依次执行 03-09
```

---

## DDL文件

| 文件 | 说明 |
|:---|:---|
| `01_enums_schemas.sql` | 枚举类型 + Schema 定义 |
| `02_reference.sql` | 元数据表 (版本化: valid_from/valid_to) |
| `03_raw_crypto.sql` | 加密货币时序表 (Hypertable) |
| `04_raw_equity_macro.sql` | 股票/宏观表 |
| `05_fundamental_alternative.sql` | 基本面/另类数据表 |
| `06_agg.sql` | 连续聚合物化视图 + 刷新策略 |
| `07_indicators.sql` | 技术指标/因子/信号表 |
| `08_quality.sql` | 数据质量监控表 (血缘追踪) |
| `09_init_data.sql` | 初始数据 (交易所/数据源/告警规则) |

---

## 配置

在 `config/.env` 中添加:

```bash
# FRED 宏观数据 API Key (免费申请)
# https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY=your_api_key

# 多 Key 负载均衡 (逗号分隔)
FRED_API_KEY=key1,key2,key3

# 代理 (如需)
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

---

## 常用 SQL

### 查询最新 K线

```sql
SELECT * FROM raw.crypto_kline_1m
WHERE symbol = 'BTCUSDT'
ORDER BY open_time DESC
LIMIT 10;
```

### 查询日线 (物化视图)

```sql
SELECT * FROM agg.crypto_kline_1d_mv
WHERE symbol = 'BTCUSDT'
ORDER BY bucket DESC
LIMIT 30;
```

### 查询期货指标

```sql
SELECT * FROM raw.crypto_metrics_5m
WHERE symbol = 'BTCUSDT'
ORDER BY timestamp DESC
LIMIT 10;
```

### 查看物化视图刷新状态

```sql
SELECT job_id, application_name, schedule_interval, next_start, last_run_status
FROM timescaledb_information.jobs
WHERE proc_name = 'policy_refresh_continuous_aggregate';
```

### 手动刷新物化视图

```sql
CALL refresh_continuous_aggregate('agg.crypto_kline_1d_mv', '2026-01-01', '2026-01-04');
```
