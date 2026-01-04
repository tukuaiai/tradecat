-- ============================================================
-- TradeCat 全市场数据库标准化脚本
-- 目标库: postgresql://postgres:postgres@localhost:5434/market_data
-- ============================================================

-- 1. 初始化 reference.exchanges (交易所元数据)
INSERT INTO reference.exchanges (exchange_code, exchange_name, market, country, timezone) VALUES
-- 加密货币
('binanceusdm', 'Binance USDT-M Futures', 'crypto', 'global', 'UTC'),
('binancecoinm', 'Binance COIN-M Futures', 'crypto', 'global', 'UTC'),
('binancespot', 'Binance Spot', 'crypto', 'global', 'UTC'),
('okx', 'OKX', 'crypto', 'global', 'UTC'),
('bybit', 'Bybit', 'crypto', 'global', 'UTC'),
-- 美股
('nasdaq', 'NASDAQ', 'us_stock', 'US', 'America/New_York'),
('nyse', 'NYSE', 'us_stock', 'US', 'America/New_York'),
-- A股
('sse', '上海证券交易所', 'cn_stock', 'CN', 'Asia/Shanghai'),
('szse', '深圳证券交易所', 'cn_stock', 'CN', 'Asia/Shanghai'),
-- 港股
('hkex', '香港交易所', 'hk_stock', 'HK', 'Asia/Hong_Kong'),
-- 期货
('cffex', '中国金融期货交易所', 'cn_futures', 'CN', 'Asia/Shanghai'),
('shfe', '上海期货交易所', 'cn_futures', 'CN', 'Asia/Shanghai'),
('dce', '大连商品交易所', 'cn_futures', 'CN', 'Asia/Shanghai'),
('czce', '郑州商品交易所', 'cn_futures', 'CN', 'Asia/Shanghai'),
('cme', 'CME Group', 'us_futures', 'US', 'America/Chicago'),
-- 外汇
('forex', 'Forex Market', 'forex', 'global', 'UTC')
ON CONFLICT (exchange_code) DO NOTHING;

-- 2. 创建多周期 K线连续聚合视图
-- 5分钟
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.kline_5m
WITH (timescaledb.continuous) AS
SELECT
  exchange,
  symbol,
  time_bucket('5 minutes', open_time) AS bucket,
  first(open, open_time) AS open,
  max(high) AS high,
  min(low) AS low,
  last(close, open_time) AS close,
  sum(volume) AS volume,
  sum(quote_volume) AS quote_volume,
  sum(trades) AS trades,
  sum(taker_buy_volume) AS taker_buy_volume
FROM raw.kline_1m
GROUP BY exchange, symbol, bucket
WITH NO DATA;

-- 15分钟
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.kline_15m
WITH (timescaledb.continuous) AS
SELECT
  exchange,
  symbol,
  time_bucket('15 minutes', open_time) AS bucket,
  first(open, open_time) AS open,
  max(high) AS high,
  min(low) AS low,
  last(close, open_time) AS close,
  sum(volume) AS volume,
  sum(quote_volume) AS quote_volume,
  sum(trades) AS trades,
  sum(taker_buy_volume) AS taker_buy_volume
FROM raw.kline_1m
GROUP BY exchange, symbol, bucket
WITH NO DATA;

-- 1小时
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.kline_1h
WITH (timescaledb.continuous) AS
SELECT
  exchange,
  symbol,
  time_bucket('1 hour', open_time) AS bucket,
  first(open, open_time) AS open,
  max(high) AS high,
  min(low) AS low,
  last(close, open_time) AS close,
  sum(volume) AS volume,
  sum(quote_volume) AS quote_volume,
  sum(trades) AS trades,
  sum(taker_buy_volume) AS taker_buy_volume
FROM raw.kline_1m
GROUP BY exchange, symbol, bucket
WITH NO DATA;

-- 4小时
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.kline_4h
WITH (timescaledb.continuous) AS
SELECT
  exchange,
  symbol,
  time_bucket('4 hours', open_time) AS bucket,
  first(open, open_time) AS open,
  max(high) AS high,
  min(low) AS low,
  last(close, open_time) AS close,
  sum(volume) AS volume,
  sum(quote_volume) AS quote_volume,
  sum(trades) AS trades,
  sum(taker_buy_volume) AS taker_buy_volume
FROM raw.kline_1m
GROUP BY exchange, symbol, bucket
WITH NO DATA;

-- 1天
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.kline_1d
WITH (timescaledb.continuous) AS
SELECT
  exchange,
  symbol,
  time_bucket('1 day', open_time) AS bucket,
  first(open, open_time) AS open,
  max(high) AS high,
  min(low) AS low,
  last(close, open_time) AS close,
  sum(volume) AS volume,
  sum(quote_volume) AS quote_volume,
  sum(trades) AS trades,
  sum(taker_buy_volume) AS taker_buy_volume
FROM raw.kline_1m
GROUP BY exchange, symbol, bucket
WITH NO DATA;

-- 1周
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.kline_1w
WITH (timescaledb.continuous) AS
SELECT
  exchange,
  symbol,
  time_bucket('1 week', open_time) AS bucket,
  first(open, open_time) AS open,
  max(high) AS high,
  min(low) AS low,
  last(close, open_time) AS close,
  sum(volume) AS volume,
  sum(quote_volume) AS quote_volume,
  sum(trades) AS trades,
  sum(taker_buy_volume) AS taker_buy_volume
FROM raw.kline_1m
GROUP BY exchange, symbol, bucket
WITH NO DATA;

-- 3. 设置连续聚合刷新策略
SELECT add_continuous_aggregate_policy('agg.kline_5m',
  start_offset => INTERVAL '1 day',
  end_offset => INTERVAL '5 minutes',
  schedule_interval => INTERVAL '5 minutes',
  if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('agg.kline_15m',
  start_offset => INTERVAL '2 days',
  end_offset => INTERVAL '15 minutes',
  schedule_interval => INTERVAL '15 minutes',
  if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('agg.kline_1h',
  start_offset => INTERVAL '7 days',
  end_offset => INTERVAL '1 hour',
  schedule_interval => INTERVAL '1 hour',
  if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('agg.kline_4h',
  start_offset => INTERVAL '14 days',
  end_offset => INTERVAL '4 hours',
  schedule_interval => INTERVAL '4 hours',
  if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('agg.kline_1d',
  start_offset => INTERVAL '30 days',
  end_offset => INTERVAL '1 day',
  schedule_interval => INTERVAL '1 day',
  if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('agg.kline_1w',
  start_offset => INTERVAL '90 days',
  end_offset => INTERVAL '1 week',
  schedule_interval => INTERVAL '1 week',
  if_not_exists => TRUE);

-- 4. 创建宏观数据表 (新增)
CREATE TABLE IF NOT EXISTS raw.macro_data (
  source TEXT NOT NULL DEFAULT 'fred',
  series_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  value NUMERIC NOT NULL,
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (source, series_id, timestamp)
);

-- 转为 hypertable
SELECT create_hypertable('raw.macro_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 year',
  if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_macro_series ON raw.macro_data (series_id, timestamp DESC);

-- 5. 创建股票日线表 (新增)
CREATE TABLE IF NOT EXISTS raw.equity_daily (
  exchange TEXT NOT NULL,
  symbol TEXT NOT NULL,
  trade_date DATE NOT NULL,
  open NUMERIC(18,4) NOT NULL,
  high NUMERIC(18,4) NOT NULL,
  low NUMERIC(18,4) NOT NULL,
  close NUMERIC(18,4) NOT NULL,
  volume NUMERIC NOT NULL,
  amount NUMERIC,
  turnover_rate NUMERIC,
  pe_ratio NUMERIC,
  pb_ratio NUMERIC,
  source TEXT NOT NULL DEFAULT 'akshare',
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (exchange, symbol, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_equity_daily_symbol ON raw.equity_daily (symbol, trade_date DESC);

-- 6. 添加数据质量监控表
CREATE TABLE IF NOT EXISTS raw.data_quality_log (
  id BIGSERIAL PRIMARY KEY,
  provider TEXT NOT NULL,
  symbol TEXT NOT NULL,
  check_time TIMESTAMPTZ NOT NULL DEFAULT now(),
  records_fetched INT,
  latency_ms NUMERIC,
  has_gaps BOOLEAN DEFAULT FALSE,
  gap_count INT DEFAULT 0,
  success BOOLEAN NOT NULL,
  error_message TEXT,
  meta_json JSONB
);

CREATE INDEX IF NOT EXISTS idx_quality_log_time ON raw.data_quality_log (check_time DESC);
CREATE INDEX IF NOT EXISTS idx_quality_log_provider ON raw.data_quality_log (provider, symbol);

-- 7. 授权
GRANT ALL ON SCHEMA raw TO tradecat_ai;
GRANT ALL ON SCHEMA agg TO tradecat_ai;
GRANT ALL ON SCHEMA reference TO tradecat_ai;
GRANT ALL ON SCHEMA indicators TO tradecat_ai;
GRANT ALL ON ALL TABLES IN SCHEMA raw TO tradecat_ai;
GRANT ALL ON ALL TABLES IN SCHEMA agg TO tradecat_ai;
GRANT ALL ON ALL TABLES IN SCHEMA reference TO tradecat_ai;
GRANT ALL ON ALL TABLES IN SCHEMA indicators TO tradecat_ai;
GRANT ALL ON ALL SEQUENCES IN SCHEMA raw TO tradecat_ai;
GRANT ALL ON ALL SEQUENCES IN SCHEMA reference TO tradecat_ai;
