-- ============================================================
-- TradeCat 全市场数据库 DDL - Part 8: 初始数据 & 权限
-- ============================================================

-- ============================================================
-- 初始化交易所数据
-- ============================================================
INSERT INTO reference.exchanges (exchange_code, exchange_name, market, country, timezone) VALUES
-- 加密货币
('binanceusdm', 'Binance USDT-M Futures', 'crypto', 'global', 'UTC'),
('binancecoinm', 'Binance COIN-M Futures', 'crypto', 'global', 'UTC'),
('binancespot', 'Binance Spot', 'crypto', 'global', 'UTC'),
('okx', 'OKX', 'crypto', 'global', 'UTC'),
('bybit', 'Bybit', 'crypto', 'global', 'UTC'),
('deribit', 'Deribit', 'crypto', 'global', 'UTC'),
-- 美股
('nasdaq', 'NASDAQ', 'us_stock', 'US', 'America/New_York'),
('nyse', 'NYSE', 'us_stock', 'US', 'America/New_York'),
('amex', 'NYSE American', 'us_stock', 'US', 'America/New_York'),
-- A股
('sse', '上海证券交易所', 'cn_stock', 'CN', 'Asia/Shanghai'),
('szse', '深圳证券交易所', 'cn_stock', 'CN', 'Asia/Shanghai'),
('bse', '北京证券交易所', 'cn_stock', 'CN', 'Asia/Shanghai'),
-- 港股
('hkex', '香港交易所', 'hk_stock', 'HK', 'Asia/Hong_Kong'),
-- 中国期货
('cffex', '中国金融期货交易所', 'cn_futures', 'CN', 'Asia/Shanghai'),
('shfe', '上海期货交易所', 'cn_futures', 'CN', 'Asia/Shanghai'),
('dce', '大连商品交易所', 'cn_futures', 'CN', 'Asia/Shanghai'),
('czce', '郑州商品交易所', 'cn_futures', 'CN', 'Asia/Shanghai'),
('ine', '上海国际能源交易中心', 'cn_futures', 'CN', 'Asia/Shanghai'),
-- 美国期货
('cme', 'CME Group', 'us_futures', 'US', 'America/Chicago'),
('cbot', 'CBOT', 'us_futures', 'US', 'America/Chicago'),
('nymex', 'NYMEX', 'us_futures', 'US', 'America/New_York'),
-- 外汇
('forex', 'Forex Market', 'forex', 'global', 'UTC')
ON CONFLICT DO NOTHING;

-- ============================================================
-- 初始化数据源配置
-- ============================================================
INSERT INTO reference.data_sources (source_code, source_name, market, data_types, min_granularity, update_frequency, requires_auth) VALUES
('ccxt', 'CCXT (100+ exchanges)', 'crypto', ARRAY['kline', 'trades', 'orderbook', 'ticker'], 'tick', 'realtime', FALSE),
('cryptofeed', 'Cryptofeed WebSocket', 'crypto', ARRAY['trades', 'orderbook', 'kline'], 'tick', 'realtime', FALSE),
('yfinance', 'Yahoo Finance', 'us_stock', ARRAY['kline', 'fundamentals'], '1d', '1d', FALSE),
('akshare', 'AKShare', 'cn_stock', ARRAY['kline', 'fundamentals', 'news'], '1d', '1d', FALSE),
('baostock', 'BaoStock', 'cn_stock', ARRAY['kline'], '1d', '1d', FALSE),
('fredapi', 'FRED API', 'macro', ARRAY['macro'], '1d', '1d', TRUE),
('openbb', 'OpenBB Platform', NULL, ARRAY['kline', 'fundamentals', 'news'], '1d', '1d', FALSE),
('polygon', 'Polygon.io', 'us_stock', ARRAY['kline', 'trades', 'orderbook'], '1m', 'realtime', TRUE),
('glassnode', 'Glassnode', 'crypto', ARRAY['onchain'], '1d', '1d', TRUE),
('santiment', 'Santiment', 'crypto', ARRAY['onchain', 'social'], '1d', '1d', TRUE)
ON CONFLICT (source_code) DO NOTHING;

-- ============================================================
-- 初始化常用宏观指标映射
-- ============================================================
INSERT INTO reference.symbol_mapping (canonical_symbol, market, provider, provider_symbol) VALUES
-- FRED 宏观指标
('US_GDP', 'macro', 'fredapi', 'GDP'),
('US_UNEMPLOYMENT', 'macro', 'fredapi', 'UNRATE'),
('US_CPI', 'macro', 'fredapi', 'CPIAUCSL'),
('US_FED_RATE', 'macro', 'fredapi', 'DFF'),
('US_10Y_YIELD', 'macro', 'fredapi', 'DGS10'),
('US_2Y_YIELD', 'macro', 'fredapi', 'DGS2'),
('US_M2', 'macro', 'fredapi', 'M2SL'),
('VIX', 'macro', 'fredapi', 'VIXCLS'),
-- 加密货币跨源映射
('BTC/USDT', 'crypto', 'ccxt', 'BTC/USDT:USDT'),
('BTC/USDT', 'crypto', 'binance_ws', 'BTCUSDT'),
('ETH/USDT', 'crypto', 'ccxt', 'ETH/USDT:USDT'),
('ETH/USDT', 'crypto', 'binance_ws', 'ETHUSDT')
ON CONFLICT DO NOTHING;

-- ============================================================
-- 权限设置
-- ============================================================

-- 创建应用用户 (如果不存在)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'tradecat_app') THEN
        CREATE ROLE tradecat_app WITH LOGIN PASSWORD 'tradecat_app_pwd';
    END IF;
END
$$;

-- 授权
GRANT USAGE ON SCHEMA reference, raw, fundamental, alternative, agg, indicators, quality TO tradecat_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA reference TO tradecat_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA raw TO tradecat_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA fundamental TO tradecat_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA alternative TO tradecat_app;
GRANT SELECT ON ALL TABLES IN SCHEMA agg TO tradecat_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA indicators TO tradecat_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA quality TO tradecat_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA reference, raw, fundamental, alternative, indicators, quality TO tradecat_app;

-- 默认权限 (新建表自动授权)
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO tradecat_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA quality GRANT SELECT, INSERT, UPDATE ON TABLES TO tradecat_app;

-- ============================================================
-- 完成
-- ============================================================
SELECT 'DDL 执行完成' AS status, now() AS completed_at;
