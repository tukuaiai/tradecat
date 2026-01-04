-- ============================================================
-- TradeCat 全市场数据库 DDL - Part 5: Fundamental & Alternative Schema
-- ============================================================

-- ============================================================
-- FUNDAMENTAL SCHEMA
-- ============================================================

-- fundamental.financial_statements - 财务报表
CREATE TABLE IF NOT EXISTS fundamental.financial_statements (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    period_end      DATE NOT NULL,
    period_type     enum_period_type NOT NULL,
    statement_type  TEXT NOT NULL,          -- balance_sheet/income/cashflow
    standard        enum_accounting_standard NOT NULL DEFAULT 'GAAP',
    currency        TEXT NOT NULL DEFAULT 'USD',
    unit            INT NOT NULL DEFAULT 1, -- 1/1000/1000000
    is_restated     BOOLEAN DEFAULT FALSE,
    filed_at        DATE,                   -- 披露日期
    data_json       JSONB NOT NULL,
    -- 血缘字段
    source          TEXT NOT NULL,
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    UNIQUE (symbol, period_end, period_type, statement_type, standard, is_restated)
);

CREATE INDEX idx_fin_stmt_symbol ON fundamental.financial_statements (symbol, period_end DESC);
CREATE INDEX idx_fin_stmt_filed ON fundamental.financial_statements (filed_at DESC);

COMMENT ON TABLE fundamental.financial_statements IS '财务报表 (结构化口径)';

-- fundamental.financial_ratios - 财务比率
CREATE TABLE IF NOT EXISTS fundamental.financial_ratios (
    symbol                  TEXT NOT NULL,
    period_end              DATE NOT NULL,
    ratio_name              TEXT NOT NULL,
    value                   NUMERIC(18,8),
    source_statement_id     BIGINT REFERENCES fundamental.financial_statements(id),
    calculated_at           TIMESTAMPTZ DEFAULT now(),
    
    PRIMARY KEY (symbol, period_end, ratio_name)
);

COMMENT ON TABLE fundamental.financial_ratios IS '财务比率 (PE/PB/ROE等)';

-- fundamental.earnings_calendar - 财报日历
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
    -- 血缘字段
    source          TEXT NOT NULL,
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    UNIQUE (symbol, report_date)
);

CREATE INDEX idx_earnings_date ON fundamental.earnings_calendar (report_date);

COMMENT ON TABLE fundamental.earnings_calendar IS '财报日历';

-- fundamental.corporate_actions - 公司行动
CREATE TABLE IF NOT EXISTS fundamental.corporate_actions (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    ex_date         DATE NOT NULL,
    action_type     enum_corporate_action NOT NULL,
    record_date     DATE,
    pay_date        DATE,
    details_json    JSONB,
    -- 血缘字段
    source          TEXT NOT NULL,
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    UNIQUE (symbol, ex_date, action_type)
);

CREATE INDEX idx_corp_action_date ON fundamental.corporate_actions (ex_date);

COMMENT ON TABLE fundamental.corporate_actions IS '公司行动 (分红/拆股等)';

-- fundamental.institutional_holdings - 机构持仓
CREATE TABLE IF NOT EXISTS fundamental.institutional_holdings (
    symbol          TEXT NOT NULL,
    holder          TEXT NOT NULL,
    report_date     DATE NOT NULL,
    shares          BIGINT,
    value           NUMERIC(38,8),
    pct_outstanding NUMERIC(18,8),
    change_shares   BIGINT,
    -- 血缘字段
    source          TEXT NOT NULL,
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    PRIMARY KEY (symbol, holder, report_date)
);

COMMENT ON TABLE fundamental.institutional_holdings IS '机构持仓';

-- ============================================================
-- ALTERNATIVE SCHEMA
-- ============================================================

-- alternative.news_articles - 新闻文章
CREATE TABLE IF NOT EXISTS alternative.news_articles (
    article_id      BIGSERIAL PRIMARY KEY,
    dedup_hash      TEXT NOT NULL UNIQUE,   -- 去重哈希
    source          TEXT NOT NULL,
    url             TEXT,
    published_at    TIMESTAMPTZ NOT NULL,
    title           TEXT NOT NULL,
    summary         TEXT,
    content         TEXT,
    symbols         TEXT[],                 -- 关联标的
    categories      TEXT[],
    language        TEXT DEFAULT 'en',
    -- 血缘字段
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

SELECT create_hypertable('alternative.news_articles', 'published_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

CREATE INDEX idx_news_symbols ON alternative.news_articles USING GIN (symbols);
CREATE INDEX idx_news_published ON alternative.news_articles (published_at DESC);
CREATE INDEX idx_news_source ON alternative.news_articles (source, published_at DESC);

SELECT add_compression_policy('alternative.news_articles', INTERVAL '30 days', if_not_exists => TRUE);

COMMENT ON TABLE alternative.news_articles IS '新闻文章';

-- alternative.news_sentiment - 新闻情感 (1:多)
CREATE TABLE IF NOT EXISTS alternative.news_sentiment (
    article_id      BIGINT NOT NULL,
    symbol          TEXT NOT NULL,
    model           TEXT NOT NULL,          -- gpt4/finbert/vader
    horizon         TEXT DEFAULT 'short',   -- short/medium/long
    score           NUMERIC(8,4) NOT NULL,  -- -1 ~ 1
    label           TEXT,                   -- negative/neutral/positive
    confidence      NUMERIC(8,4),
    analyzed_at     TIMESTAMPTZ DEFAULT now(),
    
    PRIMARY KEY (article_id, symbol, model, horizon)
);

CREATE INDEX idx_sentiment_symbol ON alternative.news_sentiment (symbol, analyzed_at DESC);

COMMENT ON TABLE alternative.news_sentiment IS '新闻情感分析 (支持多模型多标的)';

-- alternative.social_mentions - 社交媒体
CREATE TABLE IF NOT EXISTS alternative.social_mentions (
    mention_id      BIGSERIAL PRIMARY KEY,
    dedup_hash      TEXT NOT NULL,          -- 去重哈希
    platform        TEXT NOT NULL,          -- twitter/reddit/telegram
    timestamp       TIMESTAMPTZ NOT NULL,
    symbols         TEXT[],
    content_hash    TEXT,                   -- 内容指纹
    author          TEXT,
    engagement      JSONB,                  -- {likes, retweets, comments}
    sentiment_score NUMERIC(8,4),
    -- 血缘字段
    source          TEXT NOT NULL,
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    UNIQUE (platform, dedup_hash)
);

SELECT create_hypertable('alternative.social_mentions', 'timestamp',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

CREATE INDEX idx_social_symbols ON alternative.social_mentions USING GIN (symbols);

SELECT add_compression_policy('alternative.social_mentions', INTERVAL '7 days', if_not_exists => TRUE);

COMMENT ON TABLE alternative.social_mentions IS '社交媒体提及';

-- alternative.onchain_metrics - 链上指标
CREATE TABLE IF NOT EXISTS alternative.onchain_metrics (
    chain           TEXT NOT NULL,
    metric_name     TEXT NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL,
    value           NUMERIC(38,8) NOT NULL,
    -- 血缘字段
    source          TEXT NOT NULL,
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    PRIMARY KEY (chain, metric_name, timestamp)
);

SELECT create_hypertable('alternative.onchain_metrics', 'timestamp',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

COMMENT ON TABLE alternative.onchain_metrics IS '链上指标';

-- alternative.whale_transactions - 大户转账
CREATE TABLE IF NOT EXISTS alternative.whale_transactions (
    chain           TEXT NOT NULL,
    tx_hash         TEXT NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL,
    from_address    TEXT,
    to_address      TEXT,
    token           TEXT,
    amount          NUMERIC(38,18),
    usd_value       NUMERIC(38,8),
    from_label      TEXT,                   -- exchange/whale/unknown
    to_label        TEXT,
    -- 血缘字段
    source          TEXT NOT NULL,
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    UNIQUE (chain, tx_hash)
);

SELECT create_hypertable('alternative.whale_transactions', 'timestamp',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

COMMENT ON TABLE alternative.whale_transactions IS '大户转账';

-- alternative.exchange_flows - 交易所流入流出
CREATE TABLE IF NOT EXISTS alternative.exchange_flows (
    exchange        TEXT NOT NULL,
    token           TEXT NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL,
    inflow          NUMERIC(38,18),
    outflow         NUMERIC(38,18),
    netflow         NUMERIC(38,18),
    -- 血缘字段
    source          TEXT NOT NULL,
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    PRIMARY KEY (exchange, token, timestamp)
);

SELECT create_hypertable('alternative.exchange_flows', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

COMMENT ON TABLE alternative.exchange_flows IS '交易所资金流入流出';

-- alternative.economic_calendar - 经济日历
CREATE TABLE IF NOT EXISTS alternative.economic_calendar (
    event_id        BIGSERIAL PRIMARY KEY,
    event_time      TIMESTAMPTZ NOT NULL,
    event_type      enum_event_type NOT NULL,
    event_name      TEXT NOT NULL,
    country         TEXT,
    importance      INT,                    -- 1/2/3
    forecast        NUMERIC(38,8),
    actual          NUMERIC(38,8),
    previous        NUMERIC(38,8),
    unit            TEXT,
    -- 血缘字段
    source          TEXT NOT NULL,
    ingest_batch_id BIGINT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

SELECT create_hypertable('alternative.economic_calendar', 'event_time',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

CREATE INDEX idx_econ_cal_type ON alternative.economic_calendar (event_type, event_time);

COMMENT ON TABLE alternative.economic_calendar IS '经济日历';
