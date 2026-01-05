"""Market Maker V2 - 完整 Avellaneda-Stoikov 做市系统

运行:
    python main.py --config config/default.json
    
或使用环境变量:
    API_KEY=xxx API_SECRET=xxx python main.py
"""
import asyncio
import argparse
import logging
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.config import Config
from core.engine import Engine, Quote
from core.feed import WSFeed
from core.user_stream import BinanceUserStream
from core.risk import RiskManager
from strategies.avellaneda_stoikov import AvellanedaStoikov, ASConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MarketMaker:
    """做市主程序"""

    def __init__(self, config: Config):
        self.config = config
        self.running = True

        # 初始化引擎
        self.engine = Engine(
            exchange=config.exchange.name,
            api_key=config.exchange.api_key,
            api_secret=config.exchange.api_secret,
            testnet=config.exchange.testnet,
            proxy=config.exchange.proxy,
            hedge_mode=config.exchange.hedge_mode,
            strict_no_rest_markets=config.exchange.strict_no_rest_markets,
            markets_path=config.exchange.markets_path,
            markets_sha256_path=config.exchange.markets_sha256_path,
            flat_retries=config.risk.flat_retries,
            flat_retry_backoff=config.risk.flat_retry_backoff,
        )
        if config.exchange.strict_no_rest_markets:
            self.engine.validate_markets(config.strategy.symbols)
            logger.info("strict_no_rest_markets=ON 已加载预置 markets.json")
        # 用户数据流（持仓/订单私有 WS）
        rest_base = "https://testnet.binancefuture.com" if config.exchange.testnet else "https://fapi.binance.com"
        ws_base = "wss://stream.binancefuture.com" if config.exchange.testnet else "wss://fstream.binance.com"
        self.user_stream = BinanceUserStream(
            api_key=config.exchange.api_key,
            api_secret=config.exchange.api_secret,
            rest_base=rest_base,
            ws_base=ws_base,
            proxy=config.exchange.proxy,
            use_rest_snapshot=config.exchange.use_rest_snapshot,
            account_stale_seconds=config.exchange.account_stale_seconds,
        )
        self.engine.user_stream = self.user_stream
        # WS 行情/成交
        self.feed = WSFeed(
            exchange=config.exchange.name,
            symbols=config.strategy.symbols,
            proxy=config.exchange.proxy,
        )

        # 初始化策略
        self.strategies = {}
        for symbol in config.strategy.symbols:
            self.strategies[symbol] = AvellanedaStoikov(ASConfig(
                symbol=symbol,
                gamma=config.strategy.gamma,
                T=config.strategy.T,
                max_inventory=config.strategy.max_inventory,
                order_size=config.strategy.order_size,
                min_spread_bps=getattr(config.strategy, "min_spread_bps", None),
            ))

        # 注册成交回调：市场成交流喂给策略强度估计
        def _make_trade_cb(sym):
            def _cb(symbol_ccxt, side, position_side, amount, price):
                if symbol_ccxt == sym:
                    self.strategies[sym].on_fill(side, amount, price, position_side)
            return _cb
        def _make_position_cb(sym):
            def _cb(symbol_ccxt, long_qty, short_qty, net_qty):
                if symbol_ccxt == sym:
                    self.strategies[sym].set_exchange_position(long_qty, short_qty, net_qty)
            return _cb
        def _make_public_trade_cb(sym):
            def _cb(symbol_ccxt, price, amount, mid):
                if symbol_ccxt == sym:
                    self.strategies[sym].on_trade(price, amount, mid)
            return _cb

        for sym in config.strategy.symbols:
            self.feed.register_trade_listener(_make_public_trade_cb(sym))
            self.user_stream.register_trade_listener(_make_trade_cb(sym))
            self.user_stream.register_position_listener(_make_position_cb(sym))

        # 风控
        self.risk = RiskManager(
            per_symbol_limit=config.risk.per_symbol_limit,
            global_limit=config.risk.global_limit,
            flat_threshold=config.risk.flat_threshold,
            cooldown=config.risk.cooldown,
            risk_log_details=getattr(config.risk, "risk_log_details", False),
        )
        self._mid_none_count = {s: 0 for s in config.strategy.symbols}
        self._quote_blocked = {s: False for s in config.strategy.symbols}
        self._account_stale_logged = False

    async def run(self):
        """主循环"""
        logger.info("🚀 Market Maker V2 启动")
        logger.info(f"   交易对: {self.config.strategy.symbols}")
        logger.info(f"   测试网: {self.config.exchange.testnet}")

        # 启动清理
        await self._startup_clean()
        # 启动 WS feed
        self.feed.start()
        await self.user_stream.start()

        try:
            while self.running:
                await self._tick()
                await asyncio.sleep(self.config.strategy.order_interval)
        except KeyboardInterrupt:
            logger.info("收到退出信号")
        finally:
            await self._shutdown_clean()

    async def _tick(self):
        """单次循环"""
        total_notional = 0

        for symbol, strategy in self.strategies.items():
            try:
                # 获取中间价
                mid = self.feed.get_mid_price(symbol)
                if mid is None:
                    # 无 WS 行情则跳过，避免回退 REST
                    self._mid_none_count[symbol] += 1
                    if self._mid_none_count[symbol] >= self.config.strategy.mid_none_limit:
                        if not self._quote_blocked[symbol]:
                            logger.warning(f"{symbol} mid 连续缺失 {self._mid_none_count[symbol]} 次，暂停报价")
                        self._quote_blocked[symbol] = True
                    continue
                else:
                    self._mid_none_count[symbol] = 0
                    if self._quote_blocked[symbol]:
                        logger.info(f"{symbol} mid 恢复，解除暂停")
                        self._quote_blocked[symbol] = False
                if self._quote_blocked[symbol]:
                    continue

                # 用户流健康检查
                if self.user_stream.account_stale():
                    if not self._account_stale_logged:
                        logger.warning("账户流超时未更新，暂停下单，等待用户流恢复")
                        self._account_stale_logged = True
                    continue
                else:
                    self._account_stale_logged = False
                strategy.update_price(mid)
                strategy.tick()

                # 计算名义价值
                pending_notional = self.engine.pending_notional(symbol, mid)
                notional = abs(strategy.inventory * mid) + pending_notional
                total_notional += notional

                # 风控检查
                details = {
                    "inventory": round(strategy.inventory, 6),
                    "pending": round(pending_notional, 6),
                    "mid": round(mid, 6) if mid else None,
                    "orders": len(self.engine.orders_by_symbol.get(symbol, [])),
                }
                action = self.risk.check(symbol, notional, total_notional, details=details)

                if action == "flat":
                    self.engine.cancel_all(symbol)
                    flat_ok = self.engine.flat_position(symbol)
                    if flat_ok:
                        strategy.pos_long = 0
                        strategy.pos_short = 0
                    else:
                        stats = self.engine.flat_stats()
                        logger.warning(f"{symbol} 平仓失败，已重试 {self.config.risk.flat_retries} 次，flat_failure_count={stats['flat_failure_count']}，保留本地持仓等待用户流修正")
                    continue

                if action in ("pause", "global_pause"):
                    continue

                # 获取报价
                if not strategy.should_update():
                    continue

                bid, bid_qty, ask, ask_qty = strategy.get_quotes(mid)

                if bid_qty <= 0 and ask_qty <= 0:
                    continue

                # 按 TTL / 价差偏离刷新挂单；未配置则保持原有全撤重下
                ttl = self.config.strategy.order_ttl_seconds
                deviation_bps = self.config.strategy.order_price_deviation_bps
                min_cancel = self.config.strategy.cancel_cooldown_seconds
                if ttl == 0 and deviation_bps == 0:
                    self.engine.cancel_all(symbol)
                else:
                    self.engine.cancel_stale_orders(symbol, mid, ttl, deviation_bps, min_interval=min_cancel)

                quote = Quote(bid, bid_qty, ask, ask_qty)
                self.engine.place_quote(symbol, quote)

                spread_bps = (ask - bid) / mid * 10000
                logger.info(f"{symbol} | mid={mid:,.2f} | spread={spread_bps:.1f}bps | inv={strategy.inventory:.4f}")

            except Exception as e:
                logger.error(f"{symbol} 错误: {e}")

    async def _startup_clean(self):
        """启动清理"""
        logger.info("启动清理...")
        for symbol in self.strategies:
            self.engine.cancel_all(symbol)
            self.engine.flat_position(symbol)

    async def _shutdown_clean(self):
        """退出清理"""
        logger.info("退出清理...")
        for symbol in self.strategies:
            self.engine.cancel_all(symbol)
            self.engine.flat_position(symbol)
        stats = self.engine.flat_stats()
        if stats["flat_failure_count"] > 0 or stats["cancel_rate_limited"] > 0:
            logger.warning(f"退出统计: flat_failure_count={stats['flat_failure_count']} cancel_rate_limited={stats['cancel_rate_limited']}")
        await self.user_stream.stop()
        logger.info("✅ 清理完成")

    def stop(self):
        self.running = False


def main():
    parser = argparse.ArgumentParser(description="Market Maker V2")
    parser.add_argument("--config", "-c", help="配置文件路径")
    args = parser.parse_args()

    if args.config:
        config = Config.from_file(args.config)
    else:
        config = Config.from_env()

    mm = MarketMaker(config)

    # 信号处理
    def handle_signal(sig, frame):
        mm.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    asyncio.run(mm.run())


if __name__ == "__main__":
    main()
