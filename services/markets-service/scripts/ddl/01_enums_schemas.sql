-- ============================================================
-- TradeCat 全市场数据库 DDL - Part 1: 基础设置与枚举类型
-- 目标库: postgresql://postgres:postgres@localhost:5434/market_data
-- 版本: 1.0.0
-- 日期: 2026-01-04
-- ============================================================

-- 扩展
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================
-- 枚举类型 (统一定义，便于客户端复用)
-- ============================================================

-- 交易方向
CREATE TYPE enum_side AS ENUM ('buy', 'sell');
COMMENT ON TYPE enum_side IS '交易方向: buy=买入, sell=卖出';

-- 订单簿方向
CREATE TYPE enum_book_side AS ENUM ('bid', 'ask');
COMMENT ON TYPE enum_book_side IS '订单簿方向: bid=买盘, ask=卖盘';

-- 订单簿增量动作
CREATE TYPE enum_ob_action AS ENUM ('add', 'update', 'delete');
COMMENT ON TYPE enum_ob_action IS '订单簿增量动作';

-- 期权类型
CREATE TYPE enum_option_type AS ENUM ('call', 'put');
COMMENT ON TYPE enum_option_type IS '期权类型';

-- 标的类型
CREATE TYPE enum_instrument_type AS ENUM (
    'spot', 'perpetual', 'quarterly', 'option', 'etf', 'index'
);
COMMENT ON TYPE enum_instrument_type IS '标的类型';

-- 市场类型
CREATE TYPE enum_market AS ENUM (
    'crypto', 'us_stock', 'cn_stock', 'hk_stock', 
    'cn_futures', 'us_futures', 'forex', 'bond', 'macro'
);
COMMENT ON TYPE enum_market IS '市场类型';

-- 财报周期类型
CREATE TYPE enum_period_type AS ENUM ('Q1', 'Q2', 'Q3', 'Q4', 'FY', 'TTM', 'M');
COMMENT ON TYPE enum_period_type IS '财报周期: Q1-Q4=季度, FY=年度, TTM=滚动12月, M=月度';

-- 会计准则
CREATE TYPE enum_accounting_standard AS ENUM ('GAAP', 'IFRS', 'CN_GAAP');
COMMENT ON TYPE enum_accounting_standard IS '会计准则';

-- 公司行动类型
CREATE TYPE enum_corporate_action AS ENUM (
    'dividend', 'split', 'reverse_split', 'rights', 'spinoff', 'merger'
);
COMMENT ON TYPE enum_corporate_action IS '公司行动类型';

-- 事件窗口类型
CREATE TYPE enum_window_type AS ENUM (
    'T-5m', 'T+5m', 'T-30m', 'T+30m', 'T-1h', 'T+1h', 
    'T-4h', 'T+4h', 'T-1d', 'T+1d', 'T-1w', 'T+1w'
);
COMMENT ON TYPE enum_window_type IS '事件窗口类型';

-- 事件类型
CREATE TYPE enum_event_type AS ENUM (
    'economic', 'earnings', 'news', 'corporate_action', 'fed', 'other'
);
COMMENT ON TYPE enum_event_type IS '事件类型';

-- 批次状态
CREATE TYPE enum_batch_status AS ENUM (
    'pending', 'running', 'success', 'failed', 'reprocessing'
);
COMMENT ON TYPE enum_batch_status IS '采集批次状态';

-- 缺口状态
CREATE TYPE enum_gap_status AS ENUM ('detected', 'backfilling', 'resolved', 'ignored');
COMMENT ON TYPE enum_gap_status IS '数据缺口状态';

-- 异常类型
CREATE TYPE enum_anomaly_type AS ENUM (
    'price_spike', 'volume_spike', 'gap', 'duplicate', 'seq_break', 'stale', 'other'
);
COMMENT ON TYPE enum_anomaly_type IS '数据异常类型';

-- 告警级别
CREATE TYPE enum_severity AS ENUM ('info', 'warning', 'critical');
COMMENT ON TYPE enum_severity IS '告警级别';

-- 版本状态
CREATE TYPE enum_version_status AS ENUM ('active', 'superseded', 'deleted');
COMMENT ON TYPE enum_version_status IS '版本状态';

-- ============================================================
-- Schema 创建
-- ============================================================

CREATE SCHEMA IF NOT EXISTS reference;
COMMENT ON SCHEMA reference IS '元数据层 - 交易所/标的/映射 (版本化)';

CREATE SCHEMA IF NOT EXISTS raw;
COMMENT ON SCHEMA raw IS '原始时序数据层 - K线/成交/订单簿/指标';

CREATE SCHEMA IF NOT EXISTS fundamental;
COMMENT ON SCHEMA fundamental IS '基本面数据层 - 财报/公司事件';

CREATE SCHEMA IF NOT EXISTS alternative;
COMMENT ON SCHEMA alternative IS '另类数据层 - 新闻/舆情/链上';

CREATE SCHEMA IF NOT EXISTS agg;
COMMENT ON SCHEMA agg IS '聚合层 - 连续聚合视图';

CREATE SCHEMA IF NOT EXISTS indicators;
COMMENT ON SCHEMA indicators IS '指标层 - 技术指标/因子/信号';

CREATE SCHEMA IF NOT EXISTS quality;
COMMENT ON SCHEMA quality IS '数据质量层 - 血缘/监控/回填';

-- ============================================================
-- 全局序列 (血缘 ID 统一管理)
-- ============================================================

CREATE SEQUENCE IF NOT EXISTS quality.batch_id_seq START 1;
COMMENT ON SEQUENCE quality.batch_id_seq IS '采集批次 ID 全局序列';
