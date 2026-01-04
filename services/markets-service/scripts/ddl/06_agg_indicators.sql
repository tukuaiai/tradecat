-- ============================================================
-- TradeCat 全市场数据库 DDL - Part 6: Agg, Indicators, Quality Schema
-- ============================================================

-- ============================================================
-- AGG SCHEMA - 连续聚合视图
-- ============================================================

-- K线聚合: 5m
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.crypto_kline_5m
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
FROM raw.crypto_kline_1m
GROUP BY exchange, symbol, bucket
WITH NO DATA;

-- K线聚合: 15m
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.crypto_kline_15m
WITH (timescaledb.continuous) AS
SELECT
    exchange, symbol,
    time_bucket('15 minutes', open_time) AS bucket,
    first(open, open_time) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, open_time) AS close,
    sum(volume) AS volume,
    sum(quote_volume) AS quote_volume,
    sum(trades) AS trades,
    sum(taker_buy_volume) AS taker_buy_volume
FROM raw.crypto_kline_1m
GROUP BY exchange, symbol, bucket
WITH NO DATA;

-- K线聚合: 1h
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.crypto_kline_1h
WITH (timescaledb.continuous) AS
SELECT
    exchange, symbol,
    time_bucket('1 hour', open_time) AS bucket,
    first(open, open_time) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, open_time) AS close,
    sum(volume) AS volume,
    sum(quote_volume) AS quote_volume,
    sum(trades) AS trades,
    sum(taker_buy_volume) AS taker_buy_volume
FROM raw.crypto_kline_1m
GROUP BY exchange, symbol, bucket
WITH NO DATA;

-- K线聚合: 4h
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.crypto_kline_4h
WITH (timescaledb.continuous) AS
SELECT
    exchange, symbol,
    time_bucket('4 hours', open_time) AS bucket,
    first(open, open_time) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, open_time) AS close,
    sum(volume) AS volume,
    sum(quote_volume) AS quote_volume,
    sum(trades) AS trades,
    sum(taker_buy_volume) AS taker_buy_volume
FROM raw.crypto_kline_1m
GROUP BY exchange, symbol, bucket
WITH NO DATA;

-- K线聚合: 1d
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.crypto_kline_1d
WITH (timescaledb.continuous) AS
SELECT
    exchange, symbol,
    time_bucket('1 day', open_time) AS bucket,
    first(open, open_time) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, open_time) AS close,
    sum(volume) AS volume,
    sum(quote_volume) AS quote_volume,
    sum(trades) AS trades,
    sum(taker_buy_volume) AS taker_buy_volume
FROM raw.crypto_kline_1m
GROUP BY exchange, symbol, bucket
WITH NO DATA;

-- K线聚合: 1w
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.crypto_kline_1w
WITH (timescaledb.continuous) AS
SELECT
    exchange, symbol,
    time_bucket('1 week', open_time) AS bucket,
    first(open, open_time) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, open_time) AS close,
    sum(volume) AS volume,
    sum(quote_volume) AS quote_volume,
    sum(trades) AS trades,
    sum(taker_buy_volume) AS taker_buy_volume
FROM raw.crypto_kline_1m
GROUP BY exchange, symbol, bucket
WITH NO DATA;

-- 成交聚合: 1m
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.trades_1m
WITH (timescaledb.continuous) AS
SELECT
    exchange, symbol,
    time_bucket('1 minute', timestamp) AS bucket,
    sum(price * quantity) / NULLIF(sum(quantity), 0) AS vwap,
    sum(quantity) AS volume,
    sum(CASE WHEN side = 'buy' THEN quantity ELSE 0 END) AS buy_volume,
    sum(CASE WHEN side = 'sell' THEN quantity ELSE 0 END) AS sell_volume,
    count(*) AS trade_count,
    max(price) AS high,
    min(price) AS low,
    first(price, timestamp) AS open,
    last(price, timestamp) AS close
FROM raw.trades
GROUP BY exchange, symbol, bucket
WITH NO DATA;

-- 期货指标聚合: 1h
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.crypto_metrics_1h
WITH (timescaledb.continuous) AS
SELECT
    exchange, symbol,
    time_bucket('1 hour', timestamp) AS bucket,
    last(open_interest, timestamp) AS open_interest,
    last(open_interest_value, timestamp) AS open_interest_value,
    avg(long_short_ratio) AS avg_long_short_ratio,
    avg(taker_buy_sell_ratio) AS avg_taker_buy_sell_ratio
FROM raw.crypto_metrics_5m
GROUP BY exchange, symbol, bucket
WITH NO DATA;

-- 期货指标聚合: 1d
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.crypto_metrics_1d
WITH (timescaledb.continuous) AS
SELECT
    exchange, symbol,
    time_bucket('1 day', timestamp) AS bucket,
    last(open_interest, timestamp) AS open_interest,
    last(open_interest_value, timestamp) AS open_interest_value,
    avg(long_short_ratio) AS avg_long_short_ratio,
    avg(taker_buy_sell_ratio) AS avg_taker_buy_sell_ratio
FROM raw.crypto_metrics_5m
GROUP BY exchange, symbol, bucket
WITH NO DATA;

-- 舆情聚合: daily
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.sentiment_daily
WITH (timescaledb.continuous) AS
SELECT
    symbol,
    time_bucket('1 day', analyzed_at) AS bucket,
    avg(score) AS avg_score,
    count(*) AS mention_count,
    sum(CASE WHEN label = 'positive' THEN 1 ELSE 0 END) AS positive_count,
    sum(CASE WHEN label = 'negative' THEN 1 ELSE 0 END) AS negative_count
FROM alternative.news_sentiment
GROUP BY symbol, bucket
WITH NO DATA;

-- ============================================================
-- 连续聚合刷新策略
-- ============================================================

SELECT add_continuous_aggregate_policy('agg.crypto_kline_5m',
    start_offset => INTERVAL '1 day', end_offset => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '5 minutes', if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('agg.crypto_kline_15m',
    start_offset => INTERVAL '2 days', end_offset => INTERVAL '15 minutes',
    schedule_interval => INTERVAL '15 minutes', if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('agg.crypto_kline_1h',
    start_offset => INTERVAL '7 days', end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour', if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('agg.crypto_kline_4h',
    start_offset => INTERVAL '14 days', end_offset => INTERVAL '4 hours',
    schedule_interval => INTERVAL '4 hours', if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('agg.crypto_kline_1d',
    start_offset => INTERVAL '30 days', end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day', if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('agg.crypto_kline_1w',
    start_offset => INTERVAL '90 days', end_offset => INTERVAL '1 week',
    schedule_interval => INTERVAL '1 week', if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('agg.trades_1m',
    start_offset => INTERVAL '1 day', end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute', if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('agg.crypto_metrics_1h',
    start_offset => INTERVAL '7 days', end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour', if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('agg.crypto_metrics_1d',
    start_offset => INTERVAL '30 days', end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day', if_not_exists => TRUE);

-- ============================================================
-- 事件窗口表 (非连续聚合，按需计算)
-- ============================================================
CREATE TABLE IF NOT EXISTS agg.event_windows (
    id              BIGSERIAL PRIMARY KEY,
    event_id        BIGINT NOT NULL,
    event_type      enum_event_type NOT NULL,
    symbol          TEXT NOT NULL,
    window_type     enum_window_type NOT NULL,
    window_start    TIMESTAMPTZ NOT NULL,
    window_end      TIMESTAMPTZ NOT NULL,
    vwap            NUMERIC(38,18),
    volume          NUMERIC(38,8),
    high            NUMERIC(38,18),
    low             NUMERIC(38,18),
    return_pct      NUMERIC(18,8),
    trade_count     BIGINT,
    source_batch_id BIGINT,
    calculated_at   TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE (event_id, symbol, window_type)
);

CREATE INDEX idx_event_windows_symbol ON agg.event_windows (symbol, window_start);

COMMENT ON TABLE agg.event_windows IS '事件窗口聚合 (T±N)';

-- ============================================================
-- INDICATORS SCHEMA
-- ============================================================

-- indicators.technical_indicators - 技术指标
CREATE TABLE IF NOT EXISTS indicators.technical_indicators (
    exchange        TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    timeframe       TEXT NOT NULL,
    indicator       TEXT NOT NULL,
    ts              BIGINT NOT NULL,        -- Unix timestamp
    data_json       JSONB NOT NULL,
    source_batch_id BIGINT,
    calculated_at   TIMESTAMPTZ DEFAULT now(),
    
    PRIMARY KEY (exchange, symbol, timeframe, indicator, ts)
);

CREATE INDEX idx_tech_ind_symbol ON indicators.technical_indicators (symbol, timeframe);
CREATE INDEX idx_tech_ind_ts ON indicators.technical_indicators (ts DESC);
CREATE INDEX idx_tech_ind_gin ON indicators.technical_indicators USING GIN (data_json jsonb_path_ops);

COMMENT ON TABLE indicators.technical_indicators IS '技术指标 (RSI/MACD/布林带等)';

-- indicators.factor_values - 因子值
CREATE TABLE IF NOT EXISTS indicators.factor_values (
    symbol          TEXT NOT NULL,
    factor_name     TEXT NOT NULL,
    date            DATE NOT NULL,
    value           NUMERIC(18,8),
    zscore          NUMERIC(18,8),
    percentile      NUMERIC(8,4),
    source_batch_id BIGINT,
    calculated_at   TIMESTAMPTZ DEFAULT now(),
    
    PRIMARY KEY (symbol, factor_name, date)
);

CREATE INDEX idx_factor_symbol ON indicators.factor_values (symbol, date DESC);

COMMENT ON TABLE indicators.factor_values IS '因子值 (动量/价值/质量等)';

-- indicators.signals - 交易信号
CREATE TABLE IF NOT EXISTS indicators.signals (
    signal_id       BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL,
    signal_type     TEXT NOT NULL,
    direction       TEXT NOT NULL,          -- long/short/close
    strength        NUMERIC(8,4),
    confidence      NUMERIC(8,4),
    source_indicator TEXT,
    source_batch_id BIGINT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

SELECT create_hypertable('indicators.signals', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX idx_signals_symbol ON indicators.signals (symbol, timestamp DESC);

COMMENT ON TABLE indicators.signals IS '交易信号';
