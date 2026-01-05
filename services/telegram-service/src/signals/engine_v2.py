"""
信号检测引擎 v2
基于新规则系统，支持完整信号模板
"""
import os
import sqlite3
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from .rules import ALL_RULES, RULES_BY_TABLE, SignalRule
from .formatter import get_formatter

logger = logging.getLogger(__name__)

# 数据库路径
_SIGNALS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_SIGNALS_DIR))))
DB_PATH = os.environ.get(
    "INDICATOR_SQLITE_PATH",
    os.path.join(_PROJECT_ROOT, "libs/database/services/telegram-service/market_data.db")
)
COOLDOWN_DB_PATH = os.path.join(_PROJECT_ROOT, "libs/database/services/telegram-service/signal_cooldown.db")

# 默认周期
DEFAULT_TIMEFRAMES = ["1h", "4h", "1d"]

# 默认最小成交额
DEFAULT_MIN_VOLUME = 100000


def _init_cooldown_db():
    """初始化冷却数据库"""
    os.makedirs(os.path.dirname(COOLDOWN_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(COOLDOWN_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cooldowns (
            key TEXT PRIMARY KEY,
            timestamp REAL
        )
    """)
    conn.commit()
    conn.close()


_init_cooldown_db()


@dataclass
class Signal:
    """信号数据结构"""
    symbol: str
    direction: str
    strength: int
    rule_name: str
    timeframe: str
    price: float
    message: str
    full_message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    category: str = ""
    subcategory: str = ""
    priority: str = "medium"


class SignalEngine:
    """信号检测引擎"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.baseline: Dict[str, Dict] = {}  # {table_symbol_tf: row_data}
        self.cooldown: Dict[str, float] = {}  # {rule_symbol_tf: last_trigger_time}
        self.callbacks: List[callable] = []
        self.baseline_loaded = False
        self.formatter = get_formatter()
        self.enabled_rules: Set[str] = {r.name for r in ALL_RULES if r.enabled}

        # 统计
        self.stats = {
            "checks": 0,
            "signals": 0,
            "errors": 0,
        }

    def register_callback(self, callback: callable):
        """注册信号回调"""
        self.callbacks.append(callback)

    def enable_rule(self, name: str) -> bool:
        """启用规则"""
        self.enabled_rules.add(name)
        return True

    def disable_rule(self, name: str) -> bool:
        """禁用规则"""
        self.enabled_rules.discard(name)
        return True

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_table_data(self, table: str, timeframe: str) -> Dict[str, Dict]:
        """获取表中指定周期的所有数据"""
        # 白名单验证防止SQL注入
        if table not in RULES_BY_TABLE:
            logger.warning(f"非法表名: {table}")
            return {}
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(f'SELECT * FROM "{table}" WHERE "周期" = ? OR "周期" IS NULL', (timeframe,))
            rows = cursor.fetchall()
            conn.close()

            result = {}
            for row in rows:
                row_dict = dict(row)
                symbol = row_dict.get("交易对", "")
                if symbol:
                    result[symbol] = row_dict
            return result
        except Exception as e:
            logger.warning(f"读取表 {table} 失败: {e}")
            return {}

    def _get_symbol_all_tables(self, symbol: str, timeframe: str) -> Dict[str, Dict]:
        """获取单个币种所有表的数据"""
        result = {}
        for table in RULES_BY_TABLE.keys():
            data = self._get_table_data(table, timeframe)
            if symbol in data:
                result[table] = data[symbol]
        return result

    def _is_cooled_down(self, rule: SignalRule, symbol: str, timeframe: str) -> bool:
        """检查是否在冷却期"""
        key = f"{rule.name}_{symbol}_{timeframe}"
        # 先查内存缓存
        last = self.cooldown.get(key)
        if last is None:
            # 从数据库加载
            try:
                conn = sqlite3.connect(COOLDOWN_DB_PATH)
                row = conn.execute("SELECT timestamp FROM cooldowns WHERE key = ?", (key,)).fetchone()
                conn.close()
                last = row[0] if row else 0
                self.cooldown[key] = last
            except Exception:
                last = 0
        return time.time() - last > rule.cooldown

    def _set_cooldown(self, rule: SignalRule, symbol: str, timeframe: str):
        """设置冷却"""
        key = f"{rule.name}_{symbol}_{timeframe}"
        ts = time.time()
        self.cooldown[key] = ts
        # 持久化
        try:
            conn = sqlite3.connect(COOLDOWN_DB_PATH)
            conn.execute("INSERT OR REPLACE INTO cooldowns (key, timestamp) VALUES (?, ?)", (key, ts))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"保存冷却失败: {e}")

    def check_signals(self) -> List[Signal]:
        """检查所有规则"""
        signals = []
        self.stats["checks"] += 1

        # 遍历所有表
        for table, rules in RULES_BY_TABLE.items():
            # 过滤启用的规则
            active_rules = [r for r in rules if r.name in self.enabled_rules]
            if not active_rules:
                continue

            # 获取所有周期
            all_timeframes = set()
            for r in active_rules:
                all_timeframes.update(r.timeframes)

            for timeframe in all_timeframes:
                # 获取当前数据
                current_data = self._get_table_data(table, timeframe)

                for symbol, curr_row in current_data.items():
                    # 成交额过滤
                    volume = curr_row.get("成交额") or curr_row.get("成交额（USDT）") or 0

                    cache_key = f"{table}_{symbol}_{timeframe}"
                    prev_row = self.baseline.get(cache_key)

                    # 第一次只缓存基线
                    if not self.baseline_loaded:
                        self.baseline[cache_key] = curr_row
                        continue

                    # 检查每条规则
                    for rule in active_rules:
                        if timeframe not in rule.timeframes:
                            continue
                        if volume < rule.min_volume:
                            continue

                        try:
                            if rule.check_condition(prev_row, curr_row):
                                if self._is_cooled_down(rule, symbol, timeframe):
                                    # 获取完整数据用于格式化
                                    curr_all = self._get_symbol_all_tables(symbol, timeframe)
                                    prev_all = {}
                                    for t in RULES_BY_TABLE.keys():
                                        pk = f"{t}_{symbol}_{timeframe}"
                                        if pk in self.baseline:
                                            prev_all[t] = self.baseline[pk]

                                    # 格式化消息
                                    rule_msg = rule.format_message(prev_row, curr_row)
                                    price = curr_row.get("当前价格") or curr_row.get("价格") or curr_row.get("收盘价") or 0

                                    full_msg = self.formatter.format_signal(
                                        symbol=symbol,
                                        direction=rule.direction,
                                        rule_name=rule.name,
                                        timeframe=timeframe,
                                        strength=rule.strength,
                                        curr_data=curr_all,
                                        prev_data=prev_all,
                                        rule_message=rule_msg
                                    )

                                    signal = Signal(
                                        symbol=symbol,
                                        direction=rule.direction,
                                        strength=rule.strength,
                                        rule_name=rule.name,
                                        timeframe=timeframe,
                                        price=price,
                                        message=rule_msg,
                                        full_message=full_msg,
                                        category=rule.category,
                                        subcategory=rule.subcategory,
                                        priority=rule.priority
                                    )
                                    signals.append(signal)
                                    self._set_cooldown(rule, symbol, timeframe)
                                    self.stats["signals"] += 1

                                    logger.info(f"信号触发: {symbol} {rule.direction} - {rule.name} ({timeframe})")
                        except Exception as e:
                            self.stats["errors"] += 1
                            logger.warning(f"规则检查异常 {rule.name}: {e}")

                    # 更新缓存
                    self.baseline[cache_key] = curr_row

        # 标记基线加载完成
        if not self.baseline_loaded:
            self.baseline_loaded = True
            logger.info(f"基线缓存完成，共 {len(self.baseline)} 条记录")

        return signals

    def notify(self, signals: List[Signal]):
        """通知回调"""
        for signal in signals:
            for callback in self.callbacks:
                try:
                    callback(signal)
                except Exception as e:
                    logger.error(f"回调执行失败: {e}")

    def run_once(self) -> List[Signal]:
        """执行一次检查"""
        signals = self.check_signals()
        if signals:
            self.notify(signals)
        return signals

    def run_loop(self, interval: int = 60):
        """持续运行"""
        logger.info(f"信号引擎启动，检查间隔: {interval}秒，规则数: {len(self.enabled_rules)}")

        while True:
            try:
                signals = self.run_once()
                if signals:
                    logger.info(f"本轮检测到 {len(signals)} 个信号")
            except Exception as e:
                logger.error(f"检查循环异常: {e}")

            time.sleep(interval)

    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            **self.stats,
            "baseline_size": len(self.baseline),
            "cooldown_size": len(self.cooldown),
            "enabled_rules": len(self.enabled_rules),
            "total_rules": len(ALL_RULES),
        }


# 单例
_engine: Optional[SignalEngine] = None
_engine_lock = threading.Lock()

def get_engine() -> SignalEngine:
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = SignalEngine()
    return _engine
