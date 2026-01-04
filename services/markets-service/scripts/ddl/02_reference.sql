-- ============================================================
-- TradeCat 全市场数据库 DDL - Part 2: Reference Schema (版本化元数据)
-- ============================================================

-- ============================================================
-- reference.exchanges - 交易所信息 (版本化)
-- ============================================================
CREATE TABLE IF NOT EXISTS reference.exchanges (
    exchange_id     BIGSERIAL PRIMARY KEY,
    exchange_code   TEXT NOT NULL,
    exchange_name   TEXT,
    market          enum_market NOT NULL,
    country         TEXT,
    timezone        TEXT DEFAULT 'UTC',
    is_active       BOOLEAN DEFAULT TRUE,
    meta_json       JSONB,
    -- 版本化字段
    valid_from      TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_to        TIMESTAMPTZ DEFAULT 'infinity',
    version         INT NOT NULL DEFAULT 1,
    status          enum_version_status NOT NULL DEFAULT 'active',
    -- 审计
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX idx_exchanges_code_valid 
    ON reference.exchanges (exchange_code, valid_from);
CREATE INDEX idx_exchanges_active 
    ON reference.exchanges (exchange_code) WHERE status = 'active';

COMMENT ON TABLE reference.exchanges IS '交易所信息 (版本化)';
COMMENT ON COLUMN reference.exchanges.valid_from IS '生效开始时间';
COMMENT ON COLUMN reference.exchanges.valid_to IS '生效结束时间 (infinity=当前有效)';

-- 当前有效版本视图
CREATE OR REPLACE VIEW reference.v_exchanges_current AS
SELECT * FROM reference.exchanges 
WHERE status = 'active' AND now() BETWEEN valid_from AND valid_to;

-- ============================================================
-- reference.instruments - 标的主数据 (版本化)
-- ============================================================
CREATE TABLE IF NOT EXISTS reference.instruments (
    instrument_id   BIGSERIAL PRIMARY KEY,
    market          enum_market NOT NULL,
    exchange        TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    base_currency   TEXT,
    quote_currency  TEXT,
    instrument_type enum_instrument_type NOT NULL DEFAULT 'spot',
    -- 合约参数
    contract_size   NUMERIC(38,18),
    tick_size       NUMERIC(38,18),
    min_qty         NUMERIC(38,18),
    max_qty         NUMERIC(38,18),
    price_precision INT,
    qty_precision   INT,
    -- 衍生品字段
    underlying      TEXT,
    expiry          DATE,
    strike          NUMERIC(38,18),
    option_type     enum_option_type,
    -- 状态
    is_active       BOOLEAN DEFAULT TRUE,
    meta_json       JSONB,
    -- 版本化字段
    valid_from      TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_to        TIMESTAMPTZ DEFAULT 'infinity',
    version         INT NOT NULL DEFAULT 1,
    status          enum_version_status NOT NULL DEFAULT 'active',
    -- 审计
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX idx_instruments_uk 
    ON reference.instruments (market, exchange, symbol, valid_from);
CREATE INDEX idx_instruments_symbol 
    ON reference.instruments (symbol);
CREATE INDEX idx_instruments_active 
    ON reference.instruments (market, exchange, symbol) WHERE status = 'active';

COMMENT ON TABLE reference.instruments IS '标的主数据 (版本化，支持合约更换)';

-- 当前有效版本视图
CREATE OR REPLACE VIEW reference.v_instruments_current AS
SELECT * FROM reference.instruments 
WHERE status = 'active' AND now() BETWEEN valid_from AND valid_to;

-- ============================================================
-- reference.trading_hours - 交易时间 (版本化)
-- ============================================================
CREATE TABLE IF NOT EXISTS reference.trading_hours (
    id              BIGSERIAL PRIMARY KEY,
    exchange_code   TEXT NOT NULL,
    session_type    TEXT NOT NULL DEFAULT 'regular', -- regular/pre/post/overnight
    day_of_week     INT NOT NULL, -- 0=Sunday, 1=Monday, ...
    open_time       TIME NOT NULL,
    close_time      TIME NOT NULL,
    timezone        TEXT NOT NULL DEFAULT 'UTC',
    -- 版本化
    valid_from      TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_to        TIMESTAMPTZ DEFAULT 'infinity',
    version         INT NOT NULL DEFAULT 1,
    status          enum_version_status NOT NULL DEFAULT 'active'
);

CREATE INDEX idx_trading_hours_exchange 
    ON reference.trading_hours (exchange_code, day_of_week);

COMMENT ON TABLE reference.trading_hours IS '交易时间 (版本化，支持交易时间调整)';

-- ============================================================
-- reference.symbol_mapping - 跨源符号映射
-- ============================================================
CREATE TABLE IF NOT EXISTS reference.symbol_mapping (
    mapping_id      BIGSERIAL PRIMARY KEY,
    canonical_symbol TEXT NOT NULL,  -- 内部标准符号
    market          enum_market NOT NULL,
    provider        TEXT NOT NULL,   -- ccxt/yfinance/akshare/...
    provider_symbol TEXT NOT NULL,   -- 外部符号
    -- 版本化
    valid_from      TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_to        TIMESTAMPTZ DEFAULT 'infinity',
    version         INT NOT NULL DEFAULT 1,
    status          enum_version_status NOT NULL DEFAULT 'active'
);

CREATE UNIQUE INDEX idx_symbol_mapping_uk 
    ON reference.symbol_mapping (provider, provider_symbol, valid_from);
CREATE INDEX idx_symbol_mapping_canonical 
    ON reference.symbol_mapping (canonical_symbol);

COMMENT ON TABLE reference.symbol_mapping IS '跨数据源符号映射';

-- ============================================================
-- reference.data_sources - 数据源配置
-- ============================================================
CREATE TABLE IF NOT EXISTS reference.data_sources (
    source_id       SERIAL PRIMARY KEY,
    source_code     TEXT NOT NULL UNIQUE,  -- ccxt/yfinance/akshare/fredapi
    source_name     TEXT,
    market          enum_market,
    data_types      TEXT[],                -- ['kline', 'trades', 'orderbook']
    min_granularity TEXT NOT NULL,         -- tick/1s/1m/5m/1d
    update_frequency TEXT,                 -- realtime/1m/5m/1d
    rate_limit      JSONB,                 -- {requests_per_second: 10, ...}
    requires_auth   BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE,
    meta_json       JSONB,
    created_at      TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE reference.data_sources IS '数据源配置 (最小粒度/频率/限流)';
