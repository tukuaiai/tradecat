-- ============================================================
-- TradeCat 全市场数据库 DDL - Part 3: Raw Schema (时序数据)
-- ============================================================

-- ============================================================
-- raw.crypto_kline_1m - 加密货币 K线 (最小粒度)
-- 保留策略: 6个月热数据，之后冷存
-- ============================================================
CREATE TABLE IF NOT EXISTS raw.crypto_kline_1m (
    exchange                TEXT NOT NULL,
    symbol                  TEXT NOT NULL,
    open_time               TIMESTAMPTZ NOT NULL,
    close_time              TIMESTAMPTZ,
    open                    NUMERIC(38,18) NOT NULL,
    high                    NUMERIC(38,18) NOT NULL,
    low                     NUMERIC(38,18) NOT NULL,
    close                   NUMERIC(38,18) NOT NULL,
    volume                  NUMERIC(38,18) NOT NULL,
    quote_volume            NUMERIC(38,18),
    trades                  BIGINT,
    taker_buy_volume        NUMERIC(38,18),
    taker_buy_quote_volume  NUMERIC(38,18),
    is_closed               BOOLEAN NOT NULL DEFAULT FALSE,
    -- 血缘字段
    source                  TEXT NOT NULL DEFAULT 'binance_ws',
    ingest_batch_id         BIGINT NOT NULL,
    source_event_time       TIMESTAMPTZ,
    ingested_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    PRIMARY KEY (exchange, symbol, open_time)
);

SELECT create_hypertable('raw.crypto_kline_1m', 'open_time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX idx_crypto_kline_symbol_time ON raw.crypto_kline_1m (symbol, open_time DESC);
CREATE INDEX idx_crypto_kline_time ON raw.crypto_kline_1m (open_time DESC);
CREATE INDEX idx_crypto_kline_batch ON raw.crypto_kline_1m (ingest_batch_id);

-- 压缩策略: 7天后压缩
SELECT add_compression_policy('raw.crypto_kline_1m', INTERVAL '7 days', if_not_exists => TRUE);
ALTER TABLE raw.crypto_kline_1m SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'exchange, symbol',
    timescaledb.compress_orderby = 'open_time DESC'
);

-- 保留策略: 6个月 (冷存迁移预留，暂不自动删除)
-- SELECT add_retention_policy('raw.crypto_kline_1m', INTERVAL '6 months', if_not_exists => TRUE);

COMMENT ON TABLE raw.crypto_kline_1m IS '加密货币1分钟K线 (chunk=1d, compress=7d, retain=6m)';

-- ============================================================
-- raw.trades - 逐笔成交
-- 保留策略: 3个月热数据
-- ============================================================
CREATE TABLE IF NOT EXISTS raw.trades (
    exchange        TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    trade_id        BIGINT NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL,  -- 毫秒精度
    price           NUMERIC(38,18) NOT NULL,
    quantity        NUMERIC(38,18) NOT NULL,
    side            enum_side NOT NULL,
    is_maker        BOOLEAN,
    -- 血缘字段
    source          TEXT NOT NULL,
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    UNIQUE (exchange, symbol, trade_id)
);

SELECT create_hypertable('raw.trades', 'timestamp',
    chunk_time_interval => INTERVAL '6 hours',
    if_not_exists => TRUE
);

CREATE INDEX idx_trades_symbol_time ON raw.trades (symbol, timestamp DESC);
CREATE INDEX idx_trades_time ON raw.trades (timestamp DESC);

-- 压缩策略: 1天后压缩
SELECT add_compression_policy('raw.trades', INTERVAL '1 day', if_not_exists => TRUE);
ALTER TABLE raw.trades SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'exchange, symbol',
    timescaledb.compress_orderby = 'timestamp DESC'
);

COMMENT ON TABLE raw.trades IS '逐笔成交 (chunk=6h, compress=1d, retain=3m)';

-- ============================================================
-- raw.orderbook_snapshot - 订单簿快照
-- ============================================================
CREATE TABLE IF NOT EXISTS raw.orderbook_snapshot (
    exchange        TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL,
    seq_id          BIGINT NOT NULL,
    depth           INT NOT NULL,           -- 档位数
    price_precision INT NOT NULL,
    bids            JSONB NOT NULL,         -- [{p: price, s: size}, ...]
    asks            JSONB NOT NULL,
    -- 血缘字段
    source          TEXT NOT NULL,
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    UNIQUE (exchange, symbol, seq_id)
);

SELECT create_hypertable('raw.orderbook_snapshot', 'timestamp',
    chunk_time_interval => INTERVAL '6 hours',
    if_not_exists => TRUE
);

CREATE INDEX idx_ob_snap_symbol_time ON raw.orderbook_snapshot (symbol, timestamp DESC);
CREATE INDEX idx_ob_snap_seq ON raw.orderbook_snapshot (symbol, seq_id DESC);

SELECT add_compression_policy('raw.orderbook_snapshot', INTERVAL '1 day', if_not_exists => TRUE);
ALTER TABLE raw.orderbook_snapshot SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'exchange, symbol',
    timescaledb.compress_orderby = 'timestamp DESC'
);

COMMENT ON TABLE raw.orderbook_snapshot IS '订单簿快照 (chunk=6h, compress=1d)';

-- ============================================================
-- raw.orderbook_delta - 订单簿增量
-- ============================================================
CREATE TABLE IF NOT EXISTS raw.orderbook_delta (
    exchange        TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    seq_id          BIGINT NOT NULL,
    prev_seq_id     BIGINT,                 -- 前序 (校验连续性)
    timestamp       TIMESTAMPTZ NOT NULL,
    action          enum_ob_action NOT NULL,
    side            enum_book_side NOT NULL,
    price           NUMERIC(38,18) NOT NULL,
    size            NUMERIC(38,18) NOT NULL, -- delete 时为 0
    -- 血缘字段
    source          TEXT NOT NULL,
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    UNIQUE (exchange, symbol, seq_id)
);

SELECT create_hypertable('raw.orderbook_delta', 'timestamp',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

CREATE INDEX idx_ob_delta_symbol_seq ON raw.orderbook_delta (symbol, seq_id);

SELECT add_compression_policy('raw.orderbook_delta', INTERVAL '6 hours', if_not_exists => TRUE);
ALTER TABLE raw.orderbook_delta SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'exchange, symbol',
    timescaledb.compress_orderby = 'seq_id DESC'
);

COMMENT ON TABLE raw.orderbook_delta IS '订单簿增量 (chunk=1h, compress=6h)';

-- ============================================================
-- raw.crypto_metrics_5m - 加密期货指标
-- ============================================================
CREATE TABLE IF NOT EXISTS raw.crypto_metrics_5m (
    exchange                TEXT NOT NULL,
    symbol                  TEXT NOT NULL,
    timestamp               TIMESTAMPTZ NOT NULL,
    open_interest           NUMERIC(38,8),
    open_interest_value     NUMERIC(38,8),
    long_short_ratio        NUMERIC(18,8),
    top_long_short_ratio    NUMERIC(18,8),
    taker_buy_sell_ratio    NUMERIC(18,8),
    -- 血缘字段
    source                  TEXT NOT NULL DEFAULT 'binance_api',
    ingest_batch_id         BIGINT NOT NULL,
    ingested_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    PRIMARY KEY (exchange, symbol, timestamp)
);

SELECT create_hypertable('raw.crypto_metrics_5m', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX idx_crypto_metrics_symbol_time ON raw.crypto_metrics_5m (symbol, timestamp DESC);

SELECT add_compression_policy('raw.crypto_metrics_5m', INTERVAL '7 days', if_not_exists => TRUE);

COMMENT ON TABLE raw.crypto_metrics_5m IS '加密期货指标 (OI/多空比)';

-- ============================================================
-- raw.funding_rate - 资金费率
-- ============================================================
CREATE TABLE IF NOT EXISTS raw.funding_rate (
    exchange            TEXT NOT NULL,
    symbol              TEXT NOT NULL,
    funding_time        TIMESTAMPTZ NOT NULL,
    rate                NUMERIC(18,8) NOT NULL,
    next_funding_time   TIMESTAMPTZ,
    -- 血缘字段
    source              TEXT NOT NULL,
    ingest_batch_id     BIGINT NOT NULL,
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    PRIMARY KEY (exchange, symbol, funding_time)
);

SELECT create_hypertable('raw.funding_rate', 'funding_time',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

COMMENT ON TABLE raw.funding_rate IS '资金费率历史';
