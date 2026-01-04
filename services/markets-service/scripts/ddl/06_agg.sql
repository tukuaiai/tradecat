-- ============================================================
-- TradeCat 全市场数据库 DDL - Part 6: Agg Schema (连续聚合物化视图)
-- 命名规范: {market}_{datatype}_{timeframe}_mv
-- ============================================================

-- ============================================================
-- AGG SCHEMA - 连续聚合物化视图
-- ============================================================

-- ============================================================
-- K线聚合 (从 raw.crypto_kline_1m)
-- ============================================================

-- crypto_kline_5m_mv
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.crypto_kline_5m_mv
WITH (timescaledb.continuous) AS
SELECT exchange, symbol, time_bucket('5 minutes', open_time) AS bucket,
    first(open, open_time) AS open, max(high) AS high, min(low) AS low, last(close, open_time) AS close,
    sum(volume) AS volume, sum(quote_volume) AS quote_volume, sum(trades) AS trades, sum(taker_buy_volume) AS taker_buy_volume
FROM raw.crypto_kline_1m GROUP BY exchange, symbol, bucket WITH NO DATA;

-- crypto_kline_15m_mv
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.crypto_kline_15m_mv
WITH (timescaledb.continuous) AS
SELECT exchange, symbol, time_bucket('15 minutes', open_time) AS bucket,
    first(open, open_time) AS open, max(high) AS high, min(low) AS low, last(close, open_time) AS close,
    sum(volume) AS volume, sum(quote_volume) AS quote_volume, sum(trades) AS trades, sum(taker_buy_volume) AS taker_buy_volume
FROM raw.crypto_kline_1m GROUP BY exchange, symbol, bucket WITH NO DATA;

-- crypto_kline_1h_mv
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.crypto_kline_1h_mv
WITH (timescaledb.continuous) AS
SELECT exchange, symbol, time_bucket('1 hour', open_time) AS bucket,
    first(open, open_time) AS open, max(high) AS high, min(low) AS low, last(close, open_time) AS close,
    sum(volume) AS volume, sum(quote_volume) AS quote_volume, sum(trades) AS trades, sum(taker_buy_volume) AS taker_buy_volume
FROM raw.crypto_kline_1m GROUP BY exchange, symbol, bucket WITH NO DATA;

-- crypto_kline_4h_mv
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.crypto_kline_4h_mv
WITH (timescaledb.continuous) AS
SELECT exchange, symbol, time_bucket('4 hours', open_time) AS bucket,
    first(open, open_time) AS open, max(high) AS high, min(low) AS low, last(close, open_time) AS close,
    sum(volume) AS volume, sum(quote_volume) AS quote_volume, sum(trades) AS trades, sum(taker_buy_volume) AS taker_buy_volume
FROM raw.crypto_kline_1m GROUP BY exchange, symbol, bucket WITH NO DATA;

-- crypto_kline_1d_mv
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.crypto_kline_1d_mv
WITH (timescaledb.continuous) AS
SELECT exchange, symbol, time_bucket('1 day', open_time) AS bucket,
    first(open, open_time) AS open, max(high) AS high, min(low) AS low, last(close, open_time) AS close,
    sum(volume) AS volume, sum(quote_volume) AS quote_volume, sum(trades) AS trades, sum(taker_buy_volume) AS taker_buy_volume
FROM raw.crypto_kline_1m GROUP BY exchange, symbol, bucket WITH NO DATA;

-- crypto_kline_1w_mv
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.crypto_kline_1w_mv
WITH (timescaledb.continuous) AS
SELECT exchange, symbol, time_bucket('1 week', open_time) AS bucket,
    first(open, open_time) AS open, max(high) AS high, min(low) AS low, last(close, open_time) AS close,
    sum(volume) AS volume, sum(quote_volume) AS quote_volume, sum(trades) AS trades, sum(taker_buy_volume) AS taker_buy_volume
FROM raw.crypto_kline_1m GROUP BY exchange, symbol, bucket WITH NO DATA;

-- ============================================================
-- 期货指标聚合 (从 raw.crypto_metrics_5m)
-- ============================================================

-- crypto_metrics_15m_mv
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.crypto_metrics_15m_mv
WITH (timescaledb.continuous) AS
SELECT exchange, symbol, time_bucket('15 minutes', timestamp) AS bucket,
    last("sumOpenInterest", timestamp) AS open_interest,
    last("sumOpenInterestValue", timestamp) AS open_interest_value,
    avg("topAccountLongShortRatio") AS avg_long_short_ratio,
    avg("takerBuySellRatio") AS avg_taker_buy_sell_ratio
FROM raw.crypto_metrics_5m GROUP BY exchange, symbol, bucket WITH NO DATA;

-- crypto_metrics_1h_mv
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.crypto_metrics_1h_mv
WITH (timescaledb.continuous) AS
SELECT exchange, symbol, time_bucket('1 hour', timestamp) AS bucket,
    last("sumOpenInterest", timestamp) AS open_interest,
    last("sumOpenInterestValue", timestamp) AS open_interest_value,
    avg("topAccountLongShortRatio") AS avg_long_short_ratio,
    avg("takerBuySellRatio") AS avg_taker_buy_sell_ratio
FROM raw.crypto_metrics_5m GROUP BY exchange, symbol, bucket WITH NO DATA;

-- crypto_metrics_4h_mv
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.crypto_metrics_4h_mv
WITH (timescaledb.continuous) AS
SELECT exchange, symbol, time_bucket('4 hours', timestamp) AS bucket,
    last("sumOpenInterest", timestamp) AS open_interest,
    last("sumOpenInterestValue", timestamp) AS open_interest_value,
    avg("topAccountLongShortRatio") AS avg_long_short_ratio,
    avg("takerBuySellRatio") AS avg_taker_buy_sell_ratio
FROM raw.crypto_metrics_5m GROUP BY exchange, symbol, bucket WITH NO DATA;

-- crypto_metrics_1d_mv
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.crypto_metrics_1d_mv
WITH (timescaledb.continuous) AS
SELECT exchange, symbol, time_bucket('1 day', timestamp) AS bucket,
    last("sumOpenInterest", timestamp) AS open_interest,
    last("sumOpenInterestValue", timestamp) AS open_interest_value,
    avg("topAccountLongShortRatio") AS avg_long_short_ratio,
    avg("takerBuySellRatio") AS avg_taker_buy_sell_ratio
FROM raw.crypto_metrics_5m GROUP BY exchange, symbol, bucket WITH NO DATA;

-- crypto_metrics_1w_mv
CREATE MATERIALIZED VIEW IF NOT EXISTS agg.crypto_metrics_1w_mv
WITH (timescaledb.continuous) AS
SELECT exchange, symbol, time_bucket('1 week', timestamp) AS bucket,
    last("sumOpenInterest", timestamp) AS open_interest,
    last("sumOpenInterestValue", timestamp) AS open_interest_value,
    avg("topAccountLongShortRatio") AS avg_long_short_ratio,
    avg("takerBuySellRatio") AS avg_taker_buy_sell_ratio
FROM raw.crypto_metrics_5m GROUP BY exchange, symbol, bucket WITH NO DATA;

-- ============================================================
-- 刷新策略
-- ============================================================

-- K线刷新策略
SELECT add_continuous_aggregate_policy('agg.crypto_kline_5m_mv', start_offset => INTERVAL '1 day', end_offset => INTERVAL '5 minutes', schedule_interval => INTERVAL '5 minutes', if_not_exists => TRUE);
SELECT add_continuous_aggregate_policy('agg.crypto_kline_15m_mv', start_offset => INTERVAL '2 days', end_offset => INTERVAL '15 minutes', schedule_interval => INTERVAL '15 minutes', if_not_exists => TRUE);
SELECT add_continuous_aggregate_policy('agg.crypto_kline_1h_mv', start_offset => INTERVAL '7 days', end_offset => INTERVAL '1 hour', schedule_interval => INTERVAL '1 hour', if_not_exists => TRUE);
SELECT add_continuous_aggregate_policy('agg.crypto_kline_4h_mv', start_offset => INTERVAL '14 days', end_offset => INTERVAL '4 hours', schedule_interval => INTERVAL '4 hours', if_not_exists => TRUE);
SELECT add_continuous_aggregate_policy('agg.crypto_kline_1d_mv', start_offset => INTERVAL '30 days', end_offset => INTERVAL '1 day', schedule_interval => INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_continuous_aggregate_policy('agg.crypto_kline_1w_mv', start_offset => INTERVAL '90 days', end_offset => INTERVAL '1 week', schedule_interval => INTERVAL '1 week', if_not_exists => TRUE);

-- 期货指标刷新策略
SELECT add_continuous_aggregate_policy('agg.crypto_metrics_15m_mv', start_offset => INTERVAL '2 days', end_offset => INTERVAL '15 minutes', schedule_interval => INTERVAL '15 minutes', if_not_exists => TRUE);
SELECT add_continuous_aggregate_policy('agg.crypto_metrics_1h_mv', start_offset => INTERVAL '7 days', end_offset => INTERVAL '1 hour', schedule_interval => INTERVAL '1 hour', if_not_exists => TRUE);
SELECT add_continuous_aggregate_policy('agg.crypto_metrics_4h_mv', start_offset => INTERVAL '14 days', end_offset => INTERVAL '4 hours', schedule_interval => INTERVAL '4 hours', if_not_exists => TRUE);
SELECT add_continuous_aggregate_policy('agg.crypto_metrics_1d_mv', start_offset => INTERVAL '30 days', end_offset => INTERVAL '1 day', schedule_interval => INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_continuous_aggregate_policy('agg.crypto_metrics_1w_mv', start_offset => INTERVAL '90 days', end_offset => INTERVAL '1 week', schedule_interval => INTERVAL '1 week', if_not_exists => TRUE);
