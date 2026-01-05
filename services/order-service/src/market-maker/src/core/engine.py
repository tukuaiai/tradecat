"""做市引擎 - 交易所连接与订单管理"""
import ccxt
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Quote:
    bid_price: float
    bid_qty: float
    ask_price: float
    ask_qty: float


@dataclass
class Order:
    id: str
    symbol: str
    side: str
    position_side: Optional[str]
    price: float
    quantity: float
    ts: float


class Engine:
    """做市引擎"""

    def __init__(self, exchange: str, api_key: str, api_secret: str,
                 testnet: bool = True, proxy: str = None, hedge_mode: bool = False,
                 strict_no_rest_markets: bool = False, markets_path: str = "config/markets.json",
                 markets_sha256_path: Optional[str] = None,
                 flat_retries: int = 2, flat_retry_backoff: float = 0.5):
        config = {
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "options": {"defaultType": "future"},
        }
        if proxy:
            config["proxies"] = {"http": proxy, "https": proxy}

        self.exchange = getattr(ccxt, exchange)(config)
        self.exchange.has["fetchCurrencies"] = False
        self.strict_no_rest_markets = strict_no_rest_markets
        self.markets_path = Path(markets_path)
        self.markets_sha256_path = Path(markets_sha256_path) if markets_sha256_path else None

        if testnet and exchange == "binanceusdm":
            self._setup_testnet()
        if self.strict_no_rest_markets:
            self._preload_markets()

        self.orders: Dict[str, Order] = {}
        self.orders_by_symbol: Dict[str, List[Order]] = {}
        self._last_cancel_ts: Dict[str, float] = {}
        self.cancel_rate_limited = 0

        # 持仓模式由配置决定，避免额外 REST 探测
        self.hedge_mode = hedge_mode
        self.user_stream = None
        self.flat_retries = max(0, flat_retries)
        self.flat_retry_backoff = max(0.0, flat_retry_backoff)
        self.flat_failure_count = 0

    def _preload_markets(self):
        """预置 markets 以避免 load_markets 触发 REST"""
        if not self.markets_path.exists():
            raise FileNotFoundError(f"strict_no_rest_markets 启用但未找到 {self.markets_path}")
        if self.markets_sha256_path:
            if not self.markets_sha256_path.exists():
                raise FileNotFoundError(f"strict_no_rest_markets 启用但未找到 {self.markets_sha256_path}")
            expected = self.markets_sha256_path.read_text().strip()
            actual = hashlib.sha256(self.markets_path.read_bytes()).hexdigest()
            if expected and actual != expected:
                raise ValueError(f"markets.json 校验失败：期望 {expected} 实际 {actual}")
        with open(self.markets_path) as f:
            markets = json.load(f)
        if not isinstance(markets, dict) or not markets:
            raise ValueError("markets.json 内容为空或格式错误")
        self.exchange.markets = markets
        self.exchange.markets_by_id = {m.get("id"): m for m in markets.values() if m.get("id")}
        self.exchange.symbols = list(markets.keys())
        self.exchange.ids = [m["id"] for m in markets.values() if m.get("id")]
        self.exchange.currencies = {}
        self.exchange.load_markets = lambda *a, **k: markets
        self.exchange.has["loadMarkets"] = False
        self.exchange.has["fetchMarkets"] = False

    def _setup_testnet(self):
        self.exchange.set_sandbox_mode(True)
        base = "https://testnet.binancefuture.com"
        for key in ["fapiPublic", "fapiPrivate", "fapiPublicV2", "fapiPrivateV2", "fapi"]:
            if key in self.exchange.urls.get("api", {}):
                self.exchange.urls["api"][key] = f"{base}/fapi/v1"

    def get_mid_price(self, symbol: str) -> float:
        """保留兼容接口（不再调用 REST）"""
        return 0.0

    def place_quote(self, symbol: str, quote: Quote) -> tuple:
        params = self._order_params
        bid_order = ask_order = None

        # 记录下单时间以便 TTL/偏离检查
        now = time.time()
        try:
            res = self.exchange.create_limit_order(
                symbol, "buy", quote.bid_qty, quote.bid_price, params=params("buy"))
            bid_order = Order(res["id"], symbol, "buy", params("buy").get("positionSide"), quote.bid_price, quote.bid_qty, now)
            self.orders[res["id"]] = bid_order
            self.orders_by_symbol.setdefault(symbol, []).append(bid_order)
        except Exception as e:
            print(f"买单失败: {e}")

        try:
            res = self.exchange.create_limit_order(
                symbol, "sell", quote.ask_qty, quote.ask_price, params=params("sell"))
            ask_order = Order(res["id"], symbol, "sell", params("sell").get("positionSide"), quote.ask_price, quote.ask_qty, now)
            self.orders[res["id"]] = ask_order
            self.orders_by_symbol.setdefault(symbol, []).append(ask_order)
        except Exception as e:
            print(f"卖单失败: {e}")

        return bid_order, ask_order

    def cancel_all(self, symbol: str):
        try:
            self.exchange.cancel_all_orders(symbol)
            for order in self.orders_by_symbol.get(symbol, []):
                self.orders.pop(order.id, None)
            self.orders_by_symbol.pop(symbol, None)
        except Exception as e:
            if "rate limit" in str(e).lower() or "too many" in str(e).lower():
                self.cancel_rate_limited += 1
            if "No open orders" not in str(e):
                print(f"撤单失败: {e}")

    def pending_notional(self, symbol: str, mid: Optional[float]) -> float:
        """计算该交易对未成交挂单名义价值"""
        if mid is None:
            return 0.0
        return sum(abs(o.price * o.quantity) for o in self.orders_by_symbol.get(symbol, []))

    def cancel_stale_orders(self, symbol: str, mid: Optional[float], ttl: float, deviation_bps: float,
                            min_interval: float = 0.0) -> bool:
        """根据 TTL 或价格偏离撤单；返回是否撤单"""
        if symbol not in self.orders_by_symbol:
            return False
        now = time.time()
        last = self._last_cancel_ts.get(symbol, 0)
        if min_interval > 0 and now - last < min_interval:
            return False
        need_cancel = False
        for o in self.orders_by_symbol.get(symbol, []):
            if ttl > 0 and now - o.ts >= ttl:
                need_cancel = True
                break
            if deviation_bps > 0 and mid:
                dev = abs(o.price - mid) / mid * 10000
                if dev >= deviation_bps:
                    need_cancel = True
                    break
        if need_cancel:
            self.cancel_all(symbol)
            self._last_cancel_ts[symbol] = now
            return True
        return False

    def get_position(self, symbol: str) -> float:
        # 优先使用用户数据流缓存
        if self.user_stream:
            pos = self.user_stream.get_position(symbol.replace("/", "").replace(":", ""))
            if pos is not None:
                return pos
        return 0

    def flat_position(self, symbol: str):
        """平仓，支持重试，返回是否全部提交成功"""
        if not self.user_stream:
            return False
        snapshot = self.user_stream.positions_snapshot()
        # symbol key in snapshot is without slash/colon, e.g., BTCUSDT
        key = symbol.replace("/", "").replace(":", "")
        pos_map = snapshot.get(key, {})
        # 无持仓直接视为成功
        if all(abs(v) < 1e-12 for v in pos_map.values()):
            return True
        attempt = 0
        while attempt <= self.flat_retries:
            success = True
            for side_key, amt in pos_map.items():
                if amt == 0:
                    continue
                side = "sell" if (side_key == "LONG" or (side_key == "BOTH" and amt > 0)) else "buy"
                params = {"reduceOnly": True}
                if self.hedge_mode and side_key in ("LONG", "SHORT"):
                    params["positionSide"] = side_key
                try:
                    self.exchange.create_market_order(symbol, side, abs(amt), params=params)
                except Exception as exc:
                    success = False
                    self.flat_failure_count += 1
                    print(f"[Engine] 平仓失败 attempt={attempt} {symbol} {side_key} amt={amt}: {exc}")
            if success:
                return True
            attempt += 1
            if attempt <= self.flat_retries and self.flat_retry_backoff > 0:
                time.sleep(self.flat_retry_backoff * attempt)
        return False

    def flat_stats(self) -> Dict[str, int]:
        return {
            "flat_failure_count": self.flat_failure_count,
            "cancel_rate_limited": self.cancel_rate_limited,
        }

    def _order_params(self, side: str) -> Dict:
        if self.hedge_mode:
            return {"positionSide": "LONG" if side == "buy" else "SHORT"}
        return {}

    def validate_markets(self, symbols: List[str]):
        """校验预置 markets 覆盖所有交易对且包含关键字段"""
        missing = [s for s in symbols if s not in self.exchange.markets]
        if missing:
            raise ValueError(f"markets.json 缺少交易对: {missing}")
        required_keys = ["id", "symbol", "precision", "limits"]
        for sym in symbols:
            m = self.exchange.markets[sym]
            for k in required_keys:
                if k not in m:
                    raise ValueError(f"{sym} 缺少字段 {k}")
            if "contractSize" not in m:
                raise ValueError(f"{sym} 缺少 contractSize")
            # 关键字段值检查，避免空值导致下单精度错误
            precision = m.get("precision", {})
            if precision.get("amount") is None or precision.get("price") is None:
                raise ValueError(f"{sym} precision.amount/price 缺失")
            limits = m.get("limits", {}).get("amount", {})
            if limits.get("min") is None:
                raise ValueError(f"{sym} limits.amount.min 缺失")
            price_limits = m.get("limits", {}).get("price", {})
            if price_limits and price_limits.get("min") is None and price_limits.get("max") is None:
                raise ValueError(f"{sym} limits.price.* 缺失或为空")
