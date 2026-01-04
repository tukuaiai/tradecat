-- ============================================================
-- TradeCat 全市场数据库 DDL - Part 7: Indicators Schema
-- ============================================================

-- ============================================================
-- INDICATORS SCHEMA - 技术指标/因子/信号
-- ============================================================

-- indicators.indicator_data - 技术指标
CREATE TABLE IF NOT EXISTS indicators.indicator_data (
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

CREATE INDEX IF NOT EXISTS idx_tech_ind_symbol ON indicators.indicator_data (symbol, timeframe);
CREATE INDEX IF NOT EXISTS idx_tech_ind_ts ON indicators.indicator_data (ts DESC);
CREATE INDEX IF NOT EXISTS idx_tech_ind_gin ON indicators.indicator_data USING GIN (data_json jsonb_path_ops);

COMMENT ON TABLE indicators.indicator_data IS '技术指标 (RSI/MACD/布林带等)';

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

CREATE INDEX IF NOT EXISTS idx_factor_symbol ON indicators.factor_values (symbol, date DESC);

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

CREATE INDEX IF NOT EXISTS idx_signals_symbol ON indicators.signals (symbol, timestamp DESC);

COMMENT ON TABLE indicators.signals IS '交易信号';
