-- ============================================================
-- TradeCat 全市场数据库 DDL - Part 4: Raw Schema (股票/期货/宏观)
-- ============================================================

-- ============================================================
-- raw.us_equity_1d - 美股日线
-- ============================================================
CREATE TABLE IF NOT EXISTS raw.us_equity_1d (
    exchange        TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    trade_date      DATE NOT NULL,
    open            NUMERIC(18,4) NOT NULL,
    high            NUMERIC(18,4) NOT NULL,
    low             NUMERIC(18,4) NOT NULL,
    close           NUMERIC(18,4) NOT NULL,
    volume          NUMERIC(38,8) NOT NULL,
    amount          NUMERIC(38,8),
    adj_close       NUMERIC(18,4),          -- 复权价
    -- 血缘字段
    source          TEXT NOT NULL DEFAULT 'yfinance',
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    PRIMARY KEY (exchange, symbol, trade_date)
);

SELECT create_hypertable('raw.us_equity_1d', 'trade_date',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

CREATE INDEX idx_us_equity_symbol_date ON raw.us_equity_1d (symbol, trade_date DESC);

COMMENT ON TABLE raw.us_equity_1d IS '美股日线 (yfinance)';

-- ============================================================
-- raw.cn_equity_1d - A股日线
-- ============================================================
CREATE TABLE IF NOT EXISTS raw.cn_equity_1d (
    exchange        TEXT NOT NULL,          -- sse/szse
    symbol          TEXT NOT NULL,
    trade_date      DATE NOT NULL,
    open            NUMERIC(18,4) NOT NULL,
    high            NUMERIC(18,4) NOT NULL,
    low             NUMERIC(18,4) NOT NULL,
    close           NUMERIC(18,4) NOT NULL,
    volume          NUMERIC(38,8) NOT NULL,
    amount          NUMERIC(38,8),
    turnover_rate   NUMERIC(18,8),          -- 换手率
    pe_ratio        NUMERIC(18,4),
    pb_ratio        NUMERIC(18,4),
    -- 血缘字段
    source          TEXT NOT NULL DEFAULT 'akshare',
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    PRIMARY KEY (exchange, symbol, trade_date)
);

SELECT create_hypertable('raw.cn_equity_1d', 'trade_date',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

CREATE INDEX idx_cn_equity_symbol_date ON raw.cn_equity_1d (symbol, trade_date DESC);

COMMENT ON TABLE raw.cn_equity_1d IS 'A股日线 (akshare/baostock)';

-- ============================================================
-- raw.hk_equity_1d - 港股日线
-- ============================================================
CREATE TABLE IF NOT EXISTS raw.hk_equity_1d (
    exchange        TEXT NOT NULL DEFAULT 'hkex',
    symbol          TEXT NOT NULL,
    trade_date      DATE NOT NULL,
    open            NUMERIC(18,4) NOT NULL,
    high            NUMERIC(18,4) NOT NULL,
    low             NUMERIC(18,4) NOT NULL,
    close           NUMERIC(18,4) NOT NULL,
    volume          NUMERIC(38,8) NOT NULL,
    amount          NUMERIC(38,8),
    -- 血缘字段
    source          TEXT NOT NULL DEFAULT 'akshare',
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    PRIMARY KEY (exchange, symbol, trade_date)
);

SELECT create_hypertable('raw.hk_equity_1d', 'trade_date',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

COMMENT ON TABLE raw.hk_equity_1d IS '港股日线';

-- ============================================================
-- raw.futures_1d - 期货日线
-- ============================================================
CREATE TABLE IF NOT EXISTS raw.futures_1d (
    exchange        TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    trade_date      DATE NOT NULL,
    open            NUMERIC(18,4) NOT NULL,
    high            NUMERIC(18,4) NOT NULL,
    low             NUMERIC(18,4) NOT NULL,
    close           NUMERIC(18,4) NOT NULL,
    settle          NUMERIC(18,4),          -- 结算价
    volume          NUMERIC(38,8) NOT NULL,
    amount          NUMERIC(38,8),
    open_interest   NUMERIC(38,8),          -- 持仓量
    -- 血缘字段
    source          TEXT NOT NULL,
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    PRIMARY KEY (exchange, symbol, trade_date)
);

SELECT create_hypertable('raw.futures_1d', 'trade_date',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

COMMENT ON TABLE raw.futures_1d IS '期货日线';

-- ============================================================
-- raw.forex_1d - 外汇日线
-- ============================================================
CREATE TABLE IF NOT EXISTS raw.forex_1d (
    symbol          TEXT NOT NULL,          -- EURUSD, USDJPY
    trade_date      DATE NOT NULL,
    open            NUMERIC(18,6) NOT NULL,
    high            NUMERIC(18,6) NOT NULL,
    low             NUMERIC(18,6) NOT NULL,
    close           NUMERIC(18,6) NOT NULL,
    volume          NUMERIC(38,8),
    -- 血缘字段
    source          TEXT NOT NULL DEFAULT 'yfinance',
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    PRIMARY KEY (symbol, trade_date)
);

SELECT create_hypertable('raw.forex_1d', 'trade_date',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

COMMENT ON TABLE raw.forex_1d IS '外汇日线';

-- ============================================================
-- raw.macro_series - 宏观数据
-- ============================================================
CREATE TABLE IF NOT EXISTS raw.macro_series (
    source          TEXT NOT NULL DEFAULT 'fred',
    series_id       TEXT NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL,
    value           NUMERIC(38,8) NOT NULL,
    release_date    DATE,                   -- 发布日期 (可能晚于数据日期)
    revision_num    INT DEFAULT 0,          -- 修正版本号
    -- 血缘字段
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    PRIMARY KEY (source, series_id, timestamp, revision_num)
);

SELECT create_hypertable('raw.macro_series', 'timestamp',
    chunk_time_interval => INTERVAL '1 year',
    if_not_exists => TRUE
);

CREATE INDEX idx_macro_series_id ON raw.macro_series (series_id, timestamp DESC);

COMMENT ON TABLE raw.macro_series IS '宏观经济数据 (FRED等)';

-- ============================================================
-- raw.options_chain - 期权链
-- ============================================================
CREATE TABLE IF NOT EXISTS raw.options_chain (
    exchange        TEXT NOT NULL,
    underlying      TEXT NOT NULL,
    expiry          DATE NOT NULL,
    strike          NUMERIC(18,4) NOT NULL,
    option_type     enum_option_type NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL,
    bid             NUMERIC(18,4),
    ask             NUMERIC(18,4),
    last            NUMERIC(18,4),
    volume          BIGINT,
    open_interest   BIGINT,
    iv              NUMERIC(18,8),          -- 隐含波动率
    delta           NUMERIC(18,8),
    gamma           NUMERIC(18,8),
    theta           NUMERIC(18,8),
    vega            NUMERIC(18,8),
    -- 血缘字段
    source          TEXT NOT NULL,
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    PRIMARY KEY (exchange, underlying, expiry, strike, option_type, timestamp)
);

SELECT create_hypertable('raw.options_chain', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

COMMENT ON TABLE raw.options_chain IS '期权链数据';
