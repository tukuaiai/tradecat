"""markets-service 入口"""
import argparse
import logging
import sys
from pathlib import Path

from cryptofeed.defines import CANDLES

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Markets Data Service")
    parser.add_argument("command", choices=["test", "collect", "pricing"], help="命令")
    parser.add_argument("--provider", default="yfinance", help="数据源")
    parser.add_argument("--symbol", default="AAPL", help="标的代码")
    parser.add_argument("--market", default="us_stock", help="市场类型")
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


if __name__ == "__main__":
    main()
