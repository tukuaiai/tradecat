"""
基于 TimescaleDB 的信号检测引擎
直接从 PostgreSQL 读取 candles_1m 和 binance_futures_metrics_5m 数据
"""
import os
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# 数据库连接配置
_SIGNALS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_SIGNALS_DIR))))

def _get_db_url() -> str:
    """获取数据库连接URL"""
    # 优先从环境变量读取
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    # 尝试从 config/.env 读取
    env_file = os.path.join(_PROJECT_ROOT, "config", ".env")
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    return line.strip().split("=", 1)[1].strip('"\'')
    # 默认值
    return "postgresql://postgres:postgres@localhost:5433/market_data"


@dataclass
class PGSignal:
    """基于PG数据的信号"""
    symbol: str
    signal_type: str
    direction: str  # BUY/SELL/ALERT
    strength: int   # 0-100
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    timeframe: str = "5m"
    price: float = 0.0
    extra: Dict = field(default_factory=dict)


# =============================================================================
# 信号规则定义 - 基于 PG 原始数据
# =============================================================================

class PGSignalRules:
    """基于PG数据的信号规则集"""
    
    @staticmethod
    def check_price_surge(curr: Dict, prev: Dict, threshold_pct: float = 3.0) -> Optional[PGSignal]:
        """价格急涨信号 - 5分钟涨幅超过阈值"""
        if not prev or not curr:
            return None
        try:
            curr_close = float(curr.get("close", 0))
            prev_close = float(prev.get("close", 0))
            if prev_close == 0:
                return None
            change_pct = (curr_close - prev_close) / prev_close * 100
            if change_pct >= threshold_pct:
                return PGSignal(
                    symbol=curr.get("symbol", ""),
                    signal_type="price_surge",
                    direction="BUY",
                    strength=min(90, int(50 + change_pct * 10)),
                    message=f"🚀 价格急涨! 5分钟涨幅 {change_pct:.2f}%",
                    price=curr_close,
                    extra={"change_pct": change_pct}
                )
        except Exception as e:
            logger.warning(f"check_price_surge error: {e}")
        return None
    
    @staticmethod
    def check_price_dump(curr: Dict, prev: Dict, threshold_pct: float = 3.0) -> Optional[PGSignal]:
        """价格急跌信号 - 5分钟跌幅超过阈值"""
        if not prev or not curr:
            return None
        try:
            curr_close = float(curr.get("close", 0))
            prev_close = float(prev.get("close", 0))
            if prev_close == 0:
                return None
            change_pct = (curr_close - prev_close) / prev_close * 100
            if change_pct <= -threshold_pct:
                return PGSignal(
                    symbol=curr.get("symbol", ""),
                    signal_type="price_dump",
                    direction="SELL",
                    strength=min(90, int(50 + abs(change_pct) * 10)),
                    message=f"💥 价格急跌! 5分钟跌幅 {change_pct:.2f}%",
                    price=curr_close,
                    extra={"change_pct": change_pct}
                )
        except Exception as e:
            logger.warning(f"check_price_dump error: {e}")
        return None
    
    @staticmethod
    def check_volume_spike(curr: Dict, prev: Dict, multiplier: float = 5.0) -> Optional[PGSignal]:
        """成交量异常放大信号"""
        if not prev or not curr:
            return None
        try:
            curr_vol = float(curr.get("quote_volume", 0))
            prev_vol = float(prev.get("quote_volume", 0))
            if prev_vol == 0:
                return None
            vol_ratio = curr_vol / prev_vol
            if vol_ratio >= multiplier:
                return PGSignal(
                    symbol=curr.get("symbol", ""),
                    signal_type="volume_spike",
                    direction="ALERT",
                    strength=min(85, int(50 + vol_ratio * 5)),
                    message=f"📊 成交量暴增! {vol_ratio:.1f}倍 ({curr_vol/1e6:.2f}M)",
                    price=float(curr.get("close", 0)),
                    extra={"vol_ratio": vol_ratio, "quote_volume": curr_vol}
                )
        except Exception as e:
            logger.warning(f"check_volume_spike error: {e}")
        return None
    
    @staticmethod
    def check_taker_buy_dominance(curr: Dict, threshold: float = 0.7) -> Optional[PGSignal]:
        """主动买入占比异常高"""
        if not curr:
            return None
        try:
            taker_buy = float(curr.get("taker_buy_quote_volume", 0))
            total_vol = float(curr.get("quote_volume", 0))
            if total_vol == 0:
                return None
            buy_ratio = taker_buy / total_vol
            if buy_ratio >= threshold:
                return PGSignal(
                    symbol=curr.get("symbol", ""),
                    signal_type="taker_buy_dominance",
                    direction="BUY",
                    strength=int(60 + buy_ratio * 30),
                    message=f"🟢 主动买入占比 {buy_ratio*100:.1f}% (>{threshold*100:.0f}%)",
                    price=float(curr.get("close", 0)),
                    extra={"buy_ratio": buy_ratio}
                )
        except Exception as e:
            logger.warning(f"check_taker_buy_dominance error: {e}")
        return None
    
    @staticmethod
    def check_taker_sell_dominance(curr: Dict, threshold: float = 0.7) -> Optional[PGSignal]:
        """主动卖出占比异常高"""
        if not curr:
            return None
        try:
            taker_buy = float(curr.get("taker_buy_quote_volume", 0))
            total_vol = float(curr.get("quote_volume", 0))
            if total_vol == 0:
                return None
            sell_ratio = 1 - taker_buy / total_vol
            if sell_ratio >= threshold:
                return PGSignal(
                    symbol=curr.get("symbol", ""),
                    signal_type="taker_sell_dominance",
                    direction="SELL",
                    strength=int(60 + sell_ratio * 30),
                    message=f"🔴 主动卖出占比 {sell_ratio*100:.1f}% (>{threshold*100:.0f}%)",
                    price=float(curr.get("close", 0)),
                    extra={"sell_ratio": sell_ratio}
                )
        except Exception as e:
            logger.warning(f"check_taker_sell_dominance error: {e}")
        return None
    
    @staticmethod
    def check_oi_surge(curr: Dict, prev: Dict, threshold_pct: float = 5.0) -> Optional[PGSignal]:
        """持仓量急增信号"""
        if not prev or not curr:
            return None
        try:
            curr_oi = float(curr.get("sum_open_interest_value", 0))
            prev_oi = float(prev.get("sum_open_interest_value", 0))
            if prev_oi == 0:
                return None
            change_pct = (curr_oi - prev_oi) / prev_oi * 100
            if change_pct >= threshold_pct:
                return PGSignal(
                    symbol=curr.get("symbol", ""),
                    signal_type="oi_surge",
                    direction="ALERT",
                    strength=min(80, int(55 + change_pct * 3)),
                    message=f"📈 持仓量急增! 5分钟增加 {change_pct:.2f}% (${curr_oi/1e9:.2f}B)",
                    extra={"oi_change_pct": change_pct, "oi_value": curr_oi}
                )
        except Exception as e:
            logger.warning(f"check_oi_surge error: {e}")
        return None
    
    @staticmethod
    def check_oi_dump(curr: Dict, prev: Dict, threshold_pct: float = 5.0) -> Optional[PGSignal]:
        """持仓量急减信号"""
        if not prev or not curr:
            return None
        try:
            curr_oi = float(curr.get("sum_open_interest_value", 0))
            prev_oi = float(prev.get("sum_open_interest_value", 0))
            if prev_oi == 0:
                return None
            change_pct = (curr_oi - prev_oi) / prev_oi * 100
            if change_pct <= -threshold_pct:
                return PGSignal(
                    symbol=curr.get("symbol", ""),
                    signal_type="oi_dump",
                    direction="ALERT",
                    strength=min(80, int(55 + abs(change_pct) * 3)),
                    message=f"📉 持仓量急减! 5分钟减少 {abs(change_pct):.2f}% (${curr_oi/1e9:.2f}B)",
                    extra={"oi_change_pct": change_pct, "oi_value": curr_oi}
                )
        except Exception as e:
            logger.warning(f"check_oi_dump error: {e}")
        return None
    
    @staticmethod
    def check_top_trader_extreme_long(curr: Dict, threshold: float = 3.0) -> Optional[PGSignal]:
        """大户极度看多"""
        if not curr:
            return None
        try:
            ratio = float(curr.get("count_toptrader_long_short_ratio", 1))
            if ratio >= threshold:
                return PGSignal(
                    symbol=curr.get("symbol", ""),
                    signal_type="top_trader_extreme_long",
                    direction="ALERT",
                    strength=min(85, int(60 + ratio * 8)),
                    message=f"⚠️ 大户极度看多! 多空比 {ratio:.2f} (>{threshold})",
                    extra={"top_trader_ratio": ratio}
                )
        except Exception as e:
            logger.warning(f"check_top_trader_extreme_long error: {e}")
        return None
    
    @staticmethod
    def check_top_trader_extreme_short(curr: Dict, threshold: float = 0.5) -> Optional[PGSignal]:
        """大户极度看空"""
        if not curr:
            return None
        try:
            ratio = float(curr.get("count_toptrader_long_short_ratio", 1))
            if ratio <= threshold:
                return PGSignal(
                    symbol=curr.get("symbol", ""),
                    signal_type="top_trader_extreme_short",
                    direction="ALERT",
                    strength=min(85, int(60 + (1/ratio) * 5)),
                    message=f"⚠️ 大户极度看空! 多空比 {ratio:.2f} (<{threshold})",
                    extra={"top_trader_ratio": ratio}
                )
        except Exception as e:
            logger.warning(f"check_top_trader_extreme_short error: {e}")
        return None
    
    @staticmethod
    def check_taker_ratio_flip_long(curr: Dict, prev: Dict) -> Optional[PGSignal]:
        """主动成交多空比翻多"""
        if not prev or not curr:
            return None
        try:
            curr_ratio = float(curr.get("sum_taker_long_short_vol_ratio", 1))
            prev_ratio = float(prev.get("sum_taker_long_short_vol_ratio", 1))
            # 从小于1翻到大于1.2
            if prev_ratio < 1.0 and curr_ratio >= 1.2:
                return PGSignal(
                    symbol=curr.get("symbol", ""),
                    signal_type="taker_ratio_flip_long",
                    direction="BUY",
                    strength=70,
                    message=f"🔄 主动成交翻多! {prev_ratio:.2f} → {curr_ratio:.2f}",
                    extra={"prev_ratio": prev_ratio, "curr_ratio": curr_ratio}
                )
        except Exception as e:
            logger.warning(f"check_taker_ratio_flip_long error: {e}")
        return None
    
    @staticmethod
    def check_taker_ratio_flip_short(curr: Dict, prev: Dict) -> Optional[PGSignal]:
        """主动成交多空比翻空"""
        if not prev or not curr:
            return None
        try:
            curr_ratio = float(curr.get("sum_taker_long_short_vol_ratio", 1))
            prev_ratio = float(prev.get("sum_taker_long_short_vol_ratio", 1))
            # 从大于1翻到小于0.8
            if prev_ratio > 1.0 and curr_ratio <= 0.8:
                return PGSignal(
                    symbol=curr.get("symbol", ""),
                    signal_type="taker_ratio_flip_short",
                    direction="SELL",
                    strength=70,
                    message=f"🔄 主动成交翻空! {prev_ratio:.2f} → {curr_ratio:.2f}",
                    extra={"prev_ratio": prev_ratio, "curr_ratio": curr_ratio}
                )
        except Exception as e:
            logger.warning(f"check_taker_ratio_flip_short error: {e}")
        return None


class PGSignalEngine:
    """基于 TimescaleDB 的信号检测引擎"""
    
    def __init__(self, db_url: str = None, symbols: List[str] = None):
        self.db_url = db_url or _get_db_url()
        self.symbols = symbols or ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
        self.callbacks: List[Callable] = []
        self.baseline_candles: Dict[str, Dict] = {}  # {symbol: last_candle}
        self.baseline_metrics: Dict[str, Dict] = {}  # {symbol: last_metrics}
        self.cooldowns: Dict[str, float] = {}  # {signal_key: last_trigger_time}
        self.cooldown_seconds = 300  # 5分钟冷却
        self._conn = None
        self.stats = {"checks": 0, "signals": 0, "errors": 0}
    
    def _get_conn(self):
        """获取数据库连接"""
        if self._conn is None or self._conn.closed:
            try:
                import psycopg2
                self._conn = psycopg2.connect(self.db_url)
            except ImportError:
                logger.error("psycopg2 not installed, run: pip install psycopg2-binary")
                return None
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                return None
        return self._conn
    
    def register_callback(self, callback: Callable):
        """注册信号回调"""
        self.callbacks.append(callback)
    
    def _is_cooled_down(self, signal_key: str) -> bool:
        """检查是否在冷却期"""
        last = self.cooldowns.get(signal_key, 0)
        return time.time() - last > self.cooldown_seconds
    
    def _set_cooldown(self, signal_key: str):
        """设置冷却"""
        self.cooldowns[signal_key] = time.time()
    
    def _fetch_latest_candles(self) -> Dict[str, Dict]:
        """获取最新K线数据"""
        conn = self._get_conn()
        if not conn:
            return {}
        
        result = {}
        try:
            symbols_str = ",".join(f"'{s}'" for s in self.symbols)
            # 获取每个币种最新的2条K线（用于对比）
            query = f"""
                WITH ranked AS (
                    SELECT symbol, bucket_ts, open, high, low, close, volume, 
                           quote_volume, trade_count, taker_buy_volume, taker_buy_quote_volume,
                           ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY bucket_ts DESC) as rn
                    FROM market_data.candles_1m
                    WHERE symbol IN ({symbols_str})
                )
                SELECT symbol, bucket_ts, open, high, low, close, volume, 
                       quote_volume, trade_count, taker_buy_volume, taker_buy_quote_volume
                FROM ranked WHERE rn = 1
            """
            with conn.cursor() as cur:
                cur.execute(query)
                for row in cur.fetchall():
                    result[row[0]] = {
                        "symbol": row[0],
                        "bucket_ts": row[1],
                        "open": row[2],
                        "high": row[3],
                        "low": row[4],
                        "close": row[5],
                        "volume": row[6],
                        "quote_volume": row[7],
                        "trade_count": row[8],
                        "taker_buy_volume": row[9],
                        "taker_buy_quote_volume": row[10],
                    }
        except Exception as e:
            logger.error(f"Fetch candles error: {e}")
            self.stats["errors"] += 1
        return result
    
    def _fetch_latest_metrics(self) -> Dict[str, Dict]:
        """获取最新期货指标数据"""
        conn = self._get_conn()
        if not conn:
            return {}
        
        result = {}
        try:
            symbols_str = ",".join(f"'{s}'" for s in self.symbols)
            # 获取每个币种最新的期货指标
            query = f"""
                WITH ranked AS (
                    SELECT symbol, create_time, sum_open_interest, sum_open_interest_value,
                           count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio,
                           count_long_short_ratio, sum_taker_long_short_vol_ratio,
                           ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY create_time DESC) as rn
                    FROM market_data.binance_futures_metrics_5m
                    WHERE symbol IN ({symbols_str})
                )
                SELECT symbol, create_time, sum_open_interest, sum_open_interest_value,
                       count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio,
                       count_long_short_ratio, sum_taker_long_short_vol_ratio
                FROM ranked WHERE rn = 1
            """
            with conn.cursor() as cur:
                cur.execute(query)
                for row in cur.fetchall():
                    result[row[0]] = {
                        "symbol": row[0],
                        "create_time": row[1],
                        "sum_open_interest": row[2],
                        "sum_open_interest_value": row[3],
                        "count_toptrader_long_short_ratio": row[4],
                        "sum_toptrader_long_short_ratio": row[5],
                        "count_long_short_ratio": row[6],
                        "sum_taker_long_short_vol_ratio": row[7],
                    }
        except Exception as e:
            logger.error(f"Fetch metrics error: {e}")
            self.stats["errors"] += 1
        return result
    
    def check_signals(self) -> List[PGSignal]:
        """检查所有信号"""
        signals = []
        self.stats["checks"] += 1
        
        # 获取最新数据
        candles = self._fetch_latest_candles()
        metrics = self._fetch_latest_metrics()
        
        rules = PGSignalRules()
        
        for symbol in self.symbols:
            curr_candle = candles.get(symbol)
            prev_candle = self.baseline_candles.get(symbol)
            curr_metric = metrics.get(symbol)
            prev_metric = self.baseline_metrics.get(symbol)
            
            if not curr_candle:
                continue
            
            # K线相关信号
            checkers = [
                (rules.check_price_surge, [curr_candle, prev_candle, 2.0]),
                (rules.check_price_dump, [curr_candle, prev_candle, 2.0]),
                (rules.check_volume_spike, [curr_candle, prev_candle, 5.0]),
                (rules.check_taker_buy_dominance, [curr_candle, 0.7]),
                (rules.check_taker_sell_dominance, [curr_candle, 0.7]),
            ]
            
            # 期货指标信号
            if curr_metric:
                checkers.extend([
                    (rules.check_oi_surge, [curr_metric, prev_metric, 3.0]),
                    (rules.check_oi_dump, [curr_metric, prev_metric, 3.0]),
                    (rules.check_top_trader_extreme_long, [curr_metric, 3.0]),
                    (rules.check_top_trader_extreme_short, [curr_metric, 0.5]),
                    (rules.check_taker_ratio_flip_long, [curr_metric, prev_metric]),
                    (rules.check_taker_ratio_flip_short, [curr_metric, prev_metric]),
                ])
            
            for checker, args in checkers:
                try:
                    signal = checker(*args)
                    if signal:
                        signal_key = f"{signal.symbol}_{signal.signal_type}"
                        if self._is_cooled_down(signal_key):
                            signals.append(signal)
                            self._set_cooldown(signal_key)
                            self.stats["signals"] += 1
                            logger.info(f"PG Signal: {signal.symbol} - {signal.signal_type}")
                except Exception as e:
                    logger.warning(f"Check error: {e}")
                    self.stats["errors"] += 1
            
            # 更新基线
            self.baseline_candles[symbol] = curr_candle
            if curr_metric:
                self.baseline_metrics[symbol] = curr_metric
        
        return signals
    
    def notify(self, signals: List[PGSignal]):
        """通知回调"""
        from .pg_formatter import get_pg_formatter
        formatter = get_pg_formatter()
        
        for signal in signals:
            # 使用模板格式化消息
            formatted_msg = formatter.format(signal)
            for callback in self.callbacks:
                try:
                    callback(signal, formatted_msg)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
    
    def run_once(self) -> List[PGSignal]:
        """执行一次检查"""
        signals = self.check_signals()
        if signals:
            self.notify(signals)
        return signals
    
    def run_loop(self, interval: int = 60):
        """持续运行"""
        logger.info(f"PG Signal Engine started, interval: {interval}s, symbols: {self.symbols}")
        while True:
            try:
                signals = self.run_once()
                if signals:
                    logger.info(f"Found {len(signals)} PG signals")
            except Exception as e:
                logger.error(f"Run loop error: {e}")
            time.sleep(interval)
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            **self.stats,
            "symbols": len(self.symbols),
            "cooldowns": len(self.cooldowns),
        }


# 单例
_pg_engine: Optional[PGSignalEngine] = None
_pg_engine_lock = threading.Lock()

def get_pg_engine(symbols: List[str] = None) -> PGSignalEngine:
    """获取PG信号引擎单例"""
    global _pg_engine
    if _pg_engine is None:
        with _pg_engine_lock:
            if _pg_engine is None:
                _pg_engine = PGSignalEngine(symbols=symbols)
    return _pg_engine


def start_pg_signal_loop(interval: int = 60, symbols: List[str] = None):
    """在后台线程启动PG信号检测循环"""
    def run():
        engine = get_pg_engine(symbols)
        engine.run_loop(interval=interval)
    
    thread = threading.Thread(target=run, daemon=True, name="PGSignalEngine")
    thread.start()
    return thread
