-- ============================================================
-- TradeCat 数据库迁移脚本 (5434 新库)
-- 只新增/调整结构，保留现有数据
-- ============================================================

-- ============================================================
-- 1. 创建枚举类型 (如不存在)
-- ============================================================

DO $$ BEGIN CREATE TYPE enum_side AS ENUM ('buy', 'sell'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE enum_book_side AS ENUM ('bid', 'ask'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE enum_ob_action AS ENUM ('add', 'update', 'delete'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE enum_option_type AS ENUM ('call', 'put'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE enum_instrument_type AS ENUM ('spot', 'perpetual', 'quarterly', 'option', 'etf', 'index'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE enum_market AS ENUM ('crypto', 'us_stock', 'cn_stock', 'hk_stock', 'cn_futures', 'us_futures', 'forex', 'bond', 'macro'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE enum_period_type AS ENUM ('Q1', 'Q2', 'Q3', 'Q4', 'FY', 'TTM', 'M'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE enum_accounting_standard AS ENUM ('GAAP', 'IFRS', 'CN_GAAP'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE enum_corporate_action AS ENUM ('dividend', 'split', 'reverse_split', 'rights', 'spinoff', 'merger'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE enum_window_type AS ENUM ('T-5m', 'T+5m', 'T-30m', 'T+30m', 'T-1h', 'T+1h', 'T-4h', 'T+4h', 'T-1d', 'T+1d', 'T-1w', 'T+1w'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE enum_event_type AS ENUM ('economic', 'earnings', 'news', 'corporate_action', 'fed', 'other'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE enum_batch_status AS ENUM ('pending', 'running', 'success', 'failed', 'reprocessing'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE enum_gap_status AS ENUM ('detected', 'backfilling', 'resolved', 'ignored'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE enum_anomaly_type AS ENUM ('price_spike', 'volume_spike', 'gap', 'duplicate', 'seq_break', 'stale', 'other'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE enum_severity AS ENUM ('info', 'warning', 'critical'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE enum_version_status AS ENUM ('active', 'superseded', 'deleted'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ============================================================
-- 2. 创建新 Schema (如不存在)
-- ============================================================

CREATE SCHEMA IF NOT EXISTS fundamental;
CREATE SCHEMA IF NOT EXISTS alternative;
CREATE SCHEMA IF NOT EXISTS quality;

-- ============================================================
-- 3. 为现有表添加血缘字段 (如不存在)
-- ============================================================

-- raw.kline_1m 添加 ingest_batch_id
ALTER TABLE raw.kline_1m ADD COLUMN IF NOT EXISTS ingest_batch_id BIGINT DEFAULT 0;
ALTER TABLE raw.kline_1m ADD COLUMN IF NOT EXISTS source_event_time TIMESTAMPTZ;

-- raw.futures_metrics 添加 ingest_batch_id  
ALTER TABLE raw.futures_metrics ADD COLUMN IF NOT EXISTS ingest_batch_id BIGINT DEFAULT 0;

-- ============================================================
-- 4. 为 reference 表添加版本化字段
-- ============================================================

ALTER TABLE reference.exchanges ADD COLUMN IF NOT EXISTS valid_from TIMESTAMPTZ DEFAULT now();
ALTER TABLE reference.exchanges ADD COLUMN IF NOT EXISTS valid_to TIMESTAMPTZ DEFAULT 'infinity';
ALTER TABLE reference.exchanges ADD COLUMN IF NOT EXISTS version INT DEFAULT 1;
ALTER TABLE reference.exchanges ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';

ALTER TABLE reference.instruments ADD COLUMN IF NOT EXISTS valid_from TIMESTAMPTZ DEFAULT now();
ALTER TABLE reference.instruments ADD COLUMN IF NOT EXISTS valid_to TIMESTAMPTZ DEFAULT 'infinity';
ALTER TABLE reference.instruments ADD COLUMN IF NOT EXISTS version INT DEFAULT 1;
ALTER TABLE reference.instruments ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';

ALTER TABLE reference.trading_hours ADD COLUMN IF NOT EXISTS valid_from TIMESTAMPTZ DEFAULT now();
ALTER TABLE reference.trading_hours ADD COLUMN IF NOT EXISTS valid_to TIMESTAMPTZ DEFAULT 'infinity';
ALTER TABLE reference.trading_hours ADD COLUMN IF NOT EXISTS version INT DEFAULT 1;

-- ============================================================
-- 5. 创建 reference.symbol_mapping (新表)
-- ============================================================

CREATE TABLE IF NOT EXISTS reference.symbol_mapping (
    mapping_id      BIGSERIAL PRIMARY KEY,
    canonical_symbol TEXT NOT NULL,
    market          TEXT NOT NULL,
    provider        TEXT NOT NULL,
    provider_symbol TEXT NOT NULL,
    valid_from      TIMESTAMPTZ DEFAULT now(),
    valid_to        TIMESTAMPTZ DEFAULT 'infinity',
    version         INT DEFAULT 1,
    status          TEXT DEFAULT 'active'
);

CREATE INDEX IF NOT EXISTS idx_symbol_mapping_canonical ON reference.symbol_mapping (canonical_symbol);
CREATE INDEX IF NOT EXISTS idx_symbol_mapping_provider ON reference.symbol_mapping (provider, provider_symbol);

-- ============================================================
-- 6. 创建 reference.data_sources (新表)
-- ============================================================

CREATE TABLE IF NOT EXISTS reference.data_sources (
    source_id       SERIAL PRIMARY KEY,
    source_code     TEXT NOT NULL UNIQUE,
    source_name     TEXT,
    market          TEXT,
    data_types      TEXT[],
    min_granularity TEXT NOT NULL,
    update_frequency TEXT,
    rate_limit      JSONB,
    requires_auth   BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE,
    meta_json       JSONB,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 7. 创建 Quality Schema 表
-- ============================================================

CREATE SEQUENCE IF NOT EXISTS quality.batch_id_seq START 1;

CREATE TABLE IF NOT EXISTS quality.ingest_batches (
    batch_id        BIGINT PRIMARY KEY DEFAULT nextval('quality.batch_id_seq'),
    source          TEXT NOT NULL,
    data_type       TEXT NOT NULL,
    market          TEXT,
    symbol          TEXT,
    time_range_start TIMESTAMPTZ,
    time_range_end  TIMESTAMPTZ,
    status          TEXT NOT NULL DEFAULT 'pending',
    expected_rows   BIGINT,
    actual_rows     BIGINT,
    gap_ratio       NUMERIC(8,4),
    params_json     JSONB,
    error_message   TEXT,
    parent_batch_id BIGINT,
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_batches_source ON quality.ingest_batches (source, data_type);
CREATE INDEX IF NOT EXISTS idx_batches_status ON quality.ingest_batches (status);

CREATE TABLE IF NOT EXISTS quality.data_gaps (
    gap_id          BIGSERIAL PRIMARY KEY,
    table_name      TEXT NOT NULL,
    exchange        TEXT,
    symbol          TEXT NOT NULL,
    gap_start       TIMESTAMPTZ NOT NULL,
    gap_end         TIMESTAMPTZ NOT NULL,
    detected_at     TIMESTAMPTZ DEFAULT now(),
    detected_batch_id BIGINT,
    status          TEXT DEFAULT 'detected',
    backfill_task_id BIGINT,
    resolved_at     TIMESTAMPTZ,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS quality.anomaly_log (
    anomaly_id      BIGSERIAL PRIMARY KEY,
    table_name      TEXT NOT NULL,
    exchange        TEXT,
    symbol          TEXT NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL,
    anomaly_type    TEXT NOT NULL,
    severity        TEXT DEFAULT 'warning',
    details_json    JSONB,
    batch_id        BIGINT,
    detected_at     TIMESTAMPTZ DEFAULT now(),
    resolved_at     TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS quality.alert_rules (
    rule_id         SERIAL PRIMARY KEY,
    rule_name       TEXT NOT NULL UNIQUE,
    table_name      TEXT NOT NULL,
    metric          TEXT NOT NULL,
    operator        TEXT NOT NULL,
    threshold       NUMERIC NOT NULL,
    severity        TEXT DEFAULT 'warning',
    auto_backfill   BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS quality.backfill_tasks (
    task_id         BIGSERIAL PRIMARY KEY,
    table_name      TEXT NOT NULL,
    exchange        TEXT,
    symbol          TEXT,
    gap_start       TIMESTAMPTZ NOT NULL,
    gap_end         TIMESTAMPTZ NOT NULL,
    trigger_type    TEXT NOT NULL,
    trigger_gap_id  BIGINT,
    status          TEXT DEFAULT 'pending',
    priority        INT DEFAULT 5,
    retry_count     INT DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT now(),
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    result_batch_id BIGINT
);

-- ============================================================
-- 8. 创建 Fundamental Schema 表
-- ============================================================

CREATE TABLE IF NOT EXISTS fundamental.financial_statements (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    period_end      DATE NOT NULL,
    period_type     TEXT NOT NULL,
    statement_type  TEXT NOT NULL,
    standard        TEXT DEFAULT 'GAAP',
    currency        TEXT DEFAULT 'USD',
    unit            INT DEFAULT 1,
    is_restated     BOOLEAN DEFAULT FALSE,
    filed_at        DATE,
    data_json       JSONB NOT NULL,
    source          TEXT NOT NULL,
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ DEFAULT now(),
    UNIQUE (symbol, period_end, period_type, statement_type, standard, is_restated)
);

CREATE TABLE IF NOT EXISTS fundamental.earnings_calendar (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    report_date     DATE NOT NULL,
    period_end      DATE,
    eps_estimate    NUMERIC(18,4),
    eps_actual      NUMERIC(18,4),
    revenue_estimate NUMERIC(38,8),
    revenue_actual  NUMERIC(38,8),
    surprise_pct    NUMERIC(18,4),
    source          TEXT NOT NULL,
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ DEFAULT now(),
    UNIQUE (symbol, report_date)
);

CREATE TABLE IF NOT EXISTS fundamental.corporate_actions (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    ex_date         DATE NOT NULL,
    action_type     TEXT NOT NULL,
    record_date     DATE,
    pay_date        DATE,
    details_json    JSONB,
    source          TEXT NOT NULL,
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ DEFAULT now(),
    UNIQUE (symbol, ex_date, action_type)
);

-- ============================================================
-- 9. 创建 Alternative Schema 表
-- ============================================================

CREATE TABLE IF NOT EXISTS alternative.news_articles (
    article_id      BIGSERIAL PRIMARY KEY,
    dedup_hash      TEXT NOT NULL UNIQUE,
    source          TEXT NOT NULL,
    url             TEXT,
    published_at    TIMESTAMPTZ NOT NULL,
    title           TEXT NOT NULL,
    summary         TEXT,
    symbols         TEXT[],
    categories      TEXT[],
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ DEFAULT now()
);

SELECT create_hypertable('alternative.news_articles', 'published_at',
    chunk_time_interval => INTERVAL '1 month', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_news_symbols ON alternative.news_articles USING GIN (symbols);

CREATE TABLE IF NOT EXISTS alternative.news_sentiment (
    article_id      BIGINT NOT NULL,
    symbol          TEXT NOT NULL,
    model           TEXT NOT NULL,
    horizon         TEXT DEFAULT 'short',
    score           NUMERIC(8,4) NOT NULL,
    label           TEXT,
    confidence      NUMERIC(8,4),
    analyzed_at     TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (article_id, symbol, model, horizon)
);

CREATE TABLE IF NOT EXISTS alternative.economic_calendar (
    event_id        BIGSERIAL PRIMARY KEY,
    event_time      TIMESTAMPTZ NOT NULL,
    event_type      TEXT NOT NULL,
    event_name      TEXT NOT NULL,
    country         TEXT,
    importance      INT,
    forecast        NUMERIC(38,8),
    actual          NUMERIC(38,8),
    previous        NUMERIC(38,8),
    source          TEXT NOT NULL,
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ DEFAULT now()
);

SELECT create_hypertable('alternative.economic_calendar', 'event_time',
    chunk_time_interval => INTERVAL '1 month', if_not_exists => TRUE);

-- ============================================================
-- 10. 创建 Indicators Schema 表 (如不存在)
-- ============================================================

-- 保留现有 indicator_data，新增 factor_values 和 signals
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

CREATE TABLE IF NOT EXISTS indicators.signals (
    signal_id       BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL,
    signal_type     TEXT NOT NULL,
    direction       TEXT NOT NULL,
    strength        NUMERIC(8,4),
    confidence      NUMERIC(8,4),
    source_indicator TEXT,
    source_batch_id BIGINT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

SELECT create_hypertable('indicators.signals', 'timestamp',
    chunk_time_interval => INTERVAL '1 day', if_not_exists => TRUE);

-- ============================================================
-- 11. 初始化数据源配置
-- ============================================================

INSERT INTO reference.data_sources (source_code, source_name, market, data_types, min_granularity, update_frequency, requires_auth) VALUES
('ccxt', 'CCXT', 'crypto', ARRAY['kline', 'trades', 'orderbook'], 'tick', 'realtime', FALSE),
('cryptofeed', 'Cryptofeed WebSocket', 'crypto', ARRAY['trades', 'orderbook'], 'tick', 'realtime', FALSE),
('yfinance', 'Yahoo Finance', 'us_stock', ARRAY['kline'], '1d', '1d', FALSE),
('akshare', 'AKShare', 'cn_stock', ARRAY['kline'], '1d', '1d', FALSE),
('baostock', 'BaoStock', 'cn_stock', ARRAY['kline'], '1d', '1d', FALSE),
('fredapi', 'FRED API', 'macro', ARRAY['macro'], '1d', '1d', TRUE),
('openbb', 'OpenBB Platform', NULL, ARRAY['kline', 'fundamentals'], '1d', '1d', FALSE)
ON CONFLICT (source_code) DO NOTHING;

-- ============================================================
-- 12. 初始化告警规则
-- ============================================================

INSERT INTO quality.alert_rules (rule_name, table_name, metric, operator, threshold, severity, auto_backfill) VALUES
('kline_gap_warning', 'raw.kline_1m', 'gap_ratio', '>', 0.01, 'warning', TRUE),
('kline_gap_critical', 'raw.kline_1m', 'gap_ratio', '>', 0.05, 'critical', TRUE),
('metrics_gap_warning', 'raw.futures_metrics', 'gap_ratio', '>', 0.01, 'warning', TRUE)
ON CONFLICT (rule_name) DO NOTHING;

-- ============================================================
-- 完成
-- ============================================================

SELECT '迁移完成' AS status, now() AS completed_at;
