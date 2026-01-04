-- ============================================================
-- TradeCat 全市场数据库 DDL - Part 7: Quality Schema (血缘/监控/回填)
-- ============================================================

-- ============================================================
-- quality.ingest_batches - 采集批次 (血缘根)
-- ============================================================
CREATE TABLE IF NOT EXISTS quality.ingest_batches (
    batch_id        BIGINT PRIMARY KEY DEFAULT nextval('quality.batch_id_seq'),
    source          TEXT NOT NULL,
    data_type       TEXT NOT NULL,          -- kline/trades/orderbook/metrics/...
    market          enum_market,
    symbol          TEXT,                   -- NULL = 全量
    time_range_start TIMESTAMPTZ,
    time_range_end  TIMESTAMPTZ,
    status          enum_batch_status NOT NULL DEFAULT 'pending',
    expected_rows   BIGINT,
    actual_rows     BIGINT,
    gap_ratio       NUMERIC(8,4),           -- 缺口比例
    params_json     JSONB,
    error_message   TEXT,
    parent_batch_id BIGINT REFERENCES quality.ingest_batches(batch_id), -- 重算时指向原批次
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_batches_source ON quality.ingest_batches (source, data_type);
CREATE INDEX idx_batches_status ON quality.ingest_batches (status);
CREATE INDEX idx_batches_time ON quality.ingest_batches (created_at DESC);

COMMENT ON TABLE quality.ingest_batches IS '采集批次 (血缘追踪根表)';
COMMENT ON COLUMN quality.ingest_batches.batch_id IS '全局唯一批次 ID，贯穿采集→清洗→聚合→指标';
COMMENT ON COLUMN quality.ingest_batches.parent_batch_id IS '重算时指向原批次，支持血缘追溯';

-- ============================================================
-- quality.data_gaps - 数据缺口
-- ============================================================
CREATE TABLE IF NOT EXISTS quality.data_gaps (
    gap_id          BIGSERIAL PRIMARY KEY,
    table_name      TEXT NOT NULL,
    exchange        TEXT,
    symbol          TEXT NOT NULL,
    gap_start       TIMESTAMPTZ NOT NULL,
    gap_end         TIMESTAMPTZ NOT NULL,
    gap_duration    INTERVAL GENERATED ALWAYS AS (gap_end - gap_start) STORED,
    detected_at     TIMESTAMPTZ DEFAULT now(),
    detected_batch_id BIGINT REFERENCES quality.ingest_batches(batch_id),
    status          enum_gap_status NOT NULL DEFAULT 'detected',
    backfill_task_id BIGINT,
    resolved_at     TIMESTAMPTZ,
    notes           TEXT
);

CREATE INDEX idx_gaps_table ON quality.data_gaps (table_name, symbol);
CREATE INDEX idx_gaps_status ON quality.data_gaps (status);
CREATE INDEX idx_gaps_time ON quality.data_gaps (gap_start);

COMMENT ON TABLE quality.data_gaps IS '数据缺口记录';

-- ============================================================
-- quality.anomaly_log - 异常检测日志
-- ============================================================
CREATE TABLE IF NOT EXISTS quality.anomaly_log (
    anomaly_id      BIGSERIAL PRIMARY KEY,
    table_name      TEXT NOT NULL,
    exchange        TEXT,
    symbol          TEXT NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL,
    anomaly_type    enum_anomaly_type NOT NULL,
    severity        enum_severity NOT NULL DEFAULT 'warning',
    details_json    JSONB,
    batch_id        BIGINT REFERENCES quality.ingest_batches(batch_id),
    detected_at     TIMESTAMPTZ DEFAULT now(),
    resolved_at     TIMESTAMPTZ,
    resolution_notes TEXT
);

CREATE INDEX idx_anomaly_table ON quality.anomaly_log (table_name, symbol);
CREATE INDEX idx_anomaly_type ON quality.anomaly_log (anomaly_type);
CREATE INDEX idx_anomaly_time ON quality.anomaly_log (detected_at DESC);

COMMENT ON TABLE quality.anomaly_log IS '数据异常检测日志';

-- ============================================================
-- quality.alert_rules - 告警规则
-- ============================================================
CREATE TABLE IF NOT EXISTS quality.alert_rules (
    rule_id         SERIAL PRIMARY KEY,
    rule_name       TEXT NOT NULL UNIQUE,
    table_name      TEXT NOT NULL,
    metric          TEXT NOT NULL,          -- gap_ratio/seq_break/latency/row_count
    operator        TEXT NOT NULL,          -- >/</=/!=
    threshold       NUMERIC NOT NULL,
    severity        enum_severity NOT NULL DEFAULT 'warning',
    auto_backfill   BOOLEAN DEFAULT FALSE,
    notification_channel TEXT,              -- slack/telegram/email
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- 预置告警规则
INSERT INTO quality.alert_rules (rule_name, table_name, metric, operator, threshold, severity, auto_backfill) VALUES
('kline_gap_warning', 'raw.crypto_kline_1m', 'gap_ratio', '>', 0.01, 'warning', TRUE),
('kline_gap_critical', 'raw.crypto_kline_1m', 'gap_ratio', '>', 0.05, 'critical', TRUE),
('trades_gap_warning', 'raw.trades', 'gap_ratio', '>', 0.01, 'warning', TRUE),
('orderbook_seq_break', 'raw.orderbook_delta', 'seq_break', '=', 1, 'critical', FALSE),
('ingest_latency_warning', '*', 'latency_seconds', '>', 300, 'warning', FALSE)
ON CONFLICT (rule_name) DO NOTHING;

COMMENT ON TABLE quality.alert_rules IS '告警规则配置';

-- ============================================================
-- quality.backfill_tasks - 回填任务
-- ============================================================
CREATE TABLE IF NOT EXISTS quality.backfill_tasks (
    task_id         BIGSERIAL PRIMARY KEY,
    table_name      TEXT NOT NULL,
    exchange        TEXT,
    symbol          TEXT,
    gap_start       TIMESTAMPTZ NOT NULL,
    gap_end         TIMESTAMPTZ NOT NULL,
    trigger_type    TEXT NOT NULL,          -- auto/manual
    trigger_gap_id  BIGINT REFERENCES quality.data_gaps(gap_id),
    trigger_batch_id BIGINT REFERENCES quality.ingest_batches(batch_id),
    status          enum_batch_status NOT NULL DEFAULT 'pending',
    priority        INT DEFAULT 5,          -- 1=highest, 10=lowest
    retry_count     INT DEFAULT 0,
    max_retries     INT DEFAULT 3,
    error_message   TEXT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    result_batch_id BIGINT REFERENCES quality.ingest_batches(batch_id)
);

CREATE INDEX idx_backfill_status ON quality.backfill_tasks (status, priority);
CREATE INDEX idx_backfill_table ON quality.backfill_tasks (table_name, symbol);

COMMENT ON TABLE quality.backfill_tasks IS '回填任务队列';

-- ============================================================
-- quality.lineage_graph - 血缘关系 (可选，用于复杂追溯)
-- ============================================================
CREATE TABLE IF NOT EXISTS quality.lineage_graph (
    id              BIGSERIAL PRIMARY KEY,
    upstream_batch_id BIGINT NOT NULL REFERENCES quality.ingest_batches(batch_id),
    downstream_table TEXT NOT NULL,
    downstream_batch_id BIGINT REFERENCES quality.ingest_batches(batch_id),
    transform_type  TEXT NOT NULL,          -- aggregate/calculate/derive/copy
    row_count       BIGINT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_lineage_upstream ON quality.lineage_graph (upstream_batch_id);
CREATE INDEX idx_lineage_downstream ON quality.lineage_graph (downstream_batch_id);

COMMENT ON TABLE quality.lineage_graph IS '数据血缘关系图';

-- ============================================================
-- 辅助函数: 获取新批次 ID
-- ============================================================
CREATE OR REPLACE FUNCTION quality.new_batch_id() RETURNS BIGINT AS $$
    SELECT nextval('quality.batch_id_seq');
$$ LANGUAGE SQL;

COMMENT ON FUNCTION quality.new_batch_id() IS '获取新的全局批次 ID';

-- ============================================================
-- 辅助函数: 记录批次开始
-- ============================================================
CREATE OR REPLACE FUNCTION quality.start_batch(
    p_source TEXT,
    p_data_type TEXT,
    p_market enum_market DEFAULT NULL,
    p_symbol TEXT DEFAULT NULL,
    p_time_start TIMESTAMPTZ DEFAULT NULL,
    p_time_end TIMESTAMPTZ DEFAULT NULL,
    p_params JSONB DEFAULT NULL
) RETURNS BIGINT AS $$
DECLARE
    v_batch_id BIGINT;
BEGIN
    INSERT INTO quality.ingest_batches (
        source, data_type, market, symbol, 
        time_range_start, time_range_end, 
        status, params_json, started_at
    ) VALUES (
        p_source, p_data_type, p_market, p_symbol,
        p_time_start, p_time_end,
        'running', p_params, now()
    ) RETURNING batch_id INTO v_batch_id;
    
    RETURN v_batch_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 辅助函数: 记录批次完成
-- ============================================================
CREATE OR REPLACE FUNCTION quality.finish_batch(
    p_batch_id BIGINT,
    p_actual_rows BIGINT,
    p_success BOOLEAN DEFAULT TRUE,
    p_error_message TEXT DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    UPDATE quality.ingest_batches SET
        status = CASE WHEN p_success THEN 'success'::enum_batch_status ELSE 'failed'::enum_batch_status END,
        actual_rows = p_actual_rows,
        error_message = p_error_message,
        finished_at = now()
    WHERE batch_id = p_batch_id;
END;
$$ LANGUAGE plpgsql;
