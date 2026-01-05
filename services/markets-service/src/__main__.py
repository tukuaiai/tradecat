"""markets-service 入口"""
import argparse
import logging
import os
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Markets Data Service")
    parser.add_argument("command", choices=[
        "test", "collect", "pricing",
        # 加密货币采集命令 (移植自 data-service)
        "crypto-backfill", "crypto-metrics", "crypto-ws", "crypto-scan", "crypto-test"
    ], help="命令")
    parser.add_argument("--provider", default="yfinance", help="数据源")
    parser.add_argument("--symbol", default="AAPL", help="标的代码")
    parser.add_argument("--symbols", default="", help="多个标的 (逗号分隔)")
    parser.add_argument("--market", default="us_stock", help="市场类型")
    parser.add_argument("--days", type=int, default=30, help="回溯天数")
    parser.add_argument("--klines", action="store_true", help="补齐K线")
    parser.add_argument("--metrics", action="store_true", help="补齐期货指标")
    parser.add_argument("--all", action="store_true", help="补齐全部")
    args = parser.parse_args()
    
    if args.command == "test":
        from providers import ccxt, akshare, yfinance, baostock, fredapi, openbb
        from core.registry import ProviderRegistry
        
        logger.info("已注册的 Providers: %s", ProviderRegistry.list_providers())
        
        fetcher_cls = ProviderRegistry.get(args.provider, "candle")
        if fetcher_cls:
            fetcher = fetcher_cls()
            data = fetcher.fetch_sync(market=args.market, symbol=args.symbol, limit=5)
            logger.info("获取到 %d 条数据", len(data))
            for d in data[:3]:
                logger.info("  %s", d)
        else:
            logger.error("未找到 Provider: %s", args.provider)
    
    elif args.command == "pricing":
        from providers.quantlib import OptionPricer
        from datetime import date, timedelta
        
        pricer = OptionPricer(risk_free_rate=0.05)
        greeks = pricer.price_european(
            spot=100, strike=100,
            expiry=date.today() + timedelta(days=30),
            volatility=0.2, option_type="call"
        )
        logger.info("期权定价 (ATM Call, 30天到期, IV=20%%):")
        logger.info("  价格: %.4f", greeks.price)
        logger.info("  Delta: %.4f, Gamma: %.4f", greeks.delta, greeks.gamma)
        logger.info("  Theta: %.4f, Vega: %.4f", greeks.theta, greeks.vega)
    
    elif args.command == "collect":
        from cryptofeed.defines import CANDLES
        # Cryptofeed WS 采集入口（按 env 分组解析，写 raw.crypto_kline_1m）
        from datetime import datetime, timezone
        from providers.cryptofeed.stream import (
            CryptoFeedStream, load_symbols_from_env, _to_binance_perp, _from_binance_perp, CandleEvent
        )
        from storage.raw_writer import TimescaleRawWriter
        from storage import batch as batch_mgr
        
        symbols = load_symbols_from_env()
        if not symbols:
            # auto/all 模式或未配置时，退回默认 main6
            symbols = [_to_binance_perp(s) for s in [
                "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT"
            ]]
            logger.warning("未提供分组或为 auto/all，使用默认 main6: %s", symbols)
        else:
            logger.info("使用 env 分组解析的交易对: %s", symbols)
        
        writer = TimescaleRawWriter()
        batch_id = batch_mgr.start_batch(source="binance_ws", data_type="kline", market="crypto")
        logger.info("批次 ID: %s", batch_id)

        def handle_candle(event: CandleEvent):
            row = {
                "exchange": event.exchange or "binance",
                "symbol": _from_binance_perp(event.symbol),
                "bucket_ts": datetime.fromtimestamp(event.timestamp, tz=timezone.utc),
                "open": event.open,
                "high": event.high,
                "low": event.low,
                "close": event.close,
                "volume": event.volume,
                "is_closed": event.closed,
                "source": "binance_ws",
            }
            writer.upsert_kline_1m([row], ingest_batch_id=batch_id)
        
        stream = CryptoFeedStream(exchange="binance")
        stream.on_candle(handle_candle)
        stream.subscribe(symbols, channels=[CANDLES])
        logger.info("启动 Cryptofeed WS 采集并写入 raw.crypto_kline_1m ...")
        stream.run()
    
    # ==================== 加密货币采集命令 (移植自 data-service) ====================
    
    elif args.command == "crypto-test":
        # 测试配置
        from crypto.config import settings
        logger.info("=== Crypto 模块配置 ===")
        logger.info("  write_mode: %s", settings.write_mode)
        logger.info("  database_url: %s", settings.database_url[:50] + "...")
        logger.info("  db_schema: %s", settings.db_schema)
        logger.info("  raw_schema: %s", settings.raw_schema)
        logger.info("  is_raw_mode: %s", settings.is_raw_mode)
    
    elif args.command == "crypto-scan":
        # 仅扫描缺口
        from datetime import date, timedelta
        from crypto.collectors.backfill import GapScanner
        from crypto.adapters.timescale import TimescaleAdapter
        from crypto.adapters.ccxt import load_symbols
        from crypto.config import settings
        
        symbols = args.symbols.split(",") if args.symbols else load_symbols(settings.ccxt_exchange)
        ts = TimescaleAdapter()
        scanner = GapScanner(ts)
        
        end = date.today() - timedelta(days=1)
        start = end - timedelta(days=args.days)
        
        logger.info("扫描缺口: %d 个符号, %s ~ %s (模式: %s)", len(symbols), start, end, settings.write_mode)
        
        if args.klines or args.all or not args.metrics:
            gaps = scanner.scan_klines(symbols, start, end)
            total = sum(len(g) for g in gaps.values())
            logger.info("K线缺口: %d 个符号, %d 个缺口", len(gaps), total)
            for sym, sym_gaps in list(gaps.items())[:5]:
                logger.info("  %s: %s", sym, [str(g.date) for g in sym_gaps[:3]])
        
        if args.metrics or args.all:
            gaps = scanner.scan_metrics(symbols, start, end)
            total = sum(len(g) for g in gaps.values())
            logger.info("Metrics缺口: %d 个符号, %d 个缺口", len(gaps), total)
        
        ts.close()
    
    elif args.command == "crypto-backfill":
        # K线 + 期货指标补齐
        from crypto.collectors.backfill import DataBackfiller
        from crypto.config import settings
        
        symbols = args.symbols.split(",") if args.symbols else None
        lookback = args.days or int(os.getenv("BACKFILL_DAYS", "30"))
        
        logger.info("开始补齐 (模式: %s, 回溯: %d 天)", settings.write_mode, lookback)
        
        bf = DataBackfiller(lookback_days=lookback)
        try:
            if args.all:
                result = bf.run_all(symbols)
            elif args.klines:
                result = {"klines": bf.run_klines(symbols)}
            elif args.metrics:
                result = {"metrics": bf.run_metrics(symbols)}
            else:
                result = bf.run_all(symbols)
            logger.info("补齐结果: %s", result)
        finally:
            bf.close()
    
    elif args.command == "crypto-metrics":
        # 期货指标采集 (单次)
        from crypto.collectors.metrics import MetricsCollector
        from crypto.config import settings
        
        symbols = args.symbols.split(",") if args.symbols else None
        logger.info("采集期货指标 (模式: %s)", settings.write_mode)
        
        c = MetricsCollector()
        try:
            c.run_once(symbols)
        finally:
            c.close()
    
    elif args.command == "crypto-ws":
        # WebSocket 实时采集
        from crypto.collectors.ws import WSCollector
        from crypto.config import settings
        
        logger.info("启动 WebSocket 采集 (模式: %s)", settings.write_mode)
        WSCollector().run()


if __name__ == "__main__":
    main()
