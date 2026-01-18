"""
SQLite 信号检测引擎
基于指标数据库检测信号
"""

import logging
import sqlite3
import threading
import time
from collections.abc import Callable

try:
    from ..config import DATA_MAX_AGE_SECONDS, get_sqlite_path
    from ..events import SignalEvent, SignalPublisher
    from ..rules import ALL_RULES, RULES_BY_TABLE, SignalRule
    from ..storage.cooldown import get_cooldown_storage
except ImportError:
    from config import DATA_MAX_AGE_SECONDS, get_sqlite_path
    from events import SignalEvent, SignalPublisher
    from rules import ALL_RULES, RULES_BY_TABLE, SignalRule
    from storage.cooldown import get_cooldown_storage

from .base import BaseEngine, Signal
from .pg_engine import _get_default_symbols  # 复用统一符号选择

logger = logging.getLogger(__name__)


class SQLiteSignalEngine(BaseEngine):
    """SQLite 信号检测引擎"""

    def __init__(
        self,
        db_path: str = None,
        formatter: Callable = None,
    ):
        super().__init__()
        self.db_path = db_path or str(get_sqlite_path())
        self.formatter = formatter  # 可选的格式化器

        # 状态
        self.baseline: dict[str, dict] = {}  # {table_symbol_tf: row_data}
        self.baseline_loaded = False
        self.enabled_rules: set[str] = {r.name for r in ALL_RULES if r.enabled}

        # 冷却状态（从持久化存储加载）
        self._cooldown_storage = get_cooldown_storage()
        self.cooldown: dict[str, float] = self._cooldown_storage.load_all()
        logger.info(f"加载 {len(self.cooldown)} 条冷却记录")

        # 符号白名单：与 PG 引擎一致，遵守 SIGNAL_SYMBOLS / SYMBOLS_GROUPS / EXTRA / EXCLUDE
        self.allowed_symbols = set(_get_default_symbols())
        self._last_symbol_refresh = time.time()
        logger.info("符号白名单: %s", sorted(self.allowed_symbols) if self.allowed_symbols else "未设置，默认全量")

        # 统计
        self.stats = {
            "checks": 0,
            "signals": 0,
            "errors": 0,
            "stale": 0,
            "symbol_filtered": 0,
        }

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

    def _maybe_refresh_symbols(self):
        """定期刷新符号白名单，支持热更新 .env 配置"""
        if time.time() - self._last_symbol_refresh < 300:
            return
        self.allowed_symbols = set(_get_default_symbols())
        self._last_symbol_refresh = time.time()
        logger.info("符号白名单已刷新: %s", sorted(self.allowed_symbols))

    @staticmethod
    def _parse_ts(row_dict: dict) -> float:
        """提取时间戳（秒）用于新鲜度判断"""
        for key in (
            "更新时间",
            "时间",
            "时间戳",
            "数据时间",
            "update_time",
            "时间(UTC)",
            "时间_utc",
            "timestamp",
            "ts",
            "created_at",
            "updated_at",
            "event_time",
        ):
            if key in row_dict and row_dict[key]:
                val = row_dict[key]
                try:
                    if isinstance(val, (int, float)):
                        v = float(val)
                        if v > 1e12:  # 可能是毫秒级 epoch
                            v = v / 1000.0
                        return v
                    from datetime import datetime

                    return datetime.fromisoformat(str(val)).timestamp()
                except Exception:
                    continue
        return 0.0

    @staticmethod
    def _tf_seconds(timeframe: str) -> float:
        """将 1h/4h/1d 等周期转为秒，无法解析则返回 0"""
        try:
            unit = timeframe[-1].lower()
            val = float(timeframe[:-1])
            if unit == "m":
                return val * 60
            if unit == "h":
                return val * 3600
            if unit == "d":
                return val * 86400
            if unit == "w":
                return val * 604800
        except Exception:
            return 0
        return 0

    def _is_fresh(self, ts_seconds: float, timeframe: str) -> bool:
        """数据是否新鲜：基于周期动态阈值"""
        if ts_seconds <= 0:
            return False
        tf_secs = self._tf_seconds(timeframe) or 0
        # 允许的数据年龄：max(全局阈值, 1.5个周期)
        allowed = max(DATA_MAX_AGE_SECONDS, tf_secs * 1.5 if tf_secs else 0)
        if allowed <= 0:
            allowed = DATA_MAX_AGE_SECONDS
        return (time.time() - ts_seconds) <= allowed

    def _get_table_data(self, table: str, timeframe: str) -> dict[str, dict]:
        """获取表中指定周期的所有数据"""
        if table not in RULES_BY_TABLE:
            logger.warning(f"非法表名: {table}")
            return {}
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                f'''
                SELECT * FROM "{table}"
                WHERE "周期" = ? OR "周期" IS NULL
                ORDER BY
                    COALESCE("更新时间","时间","时间戳") DESC,
                    rowid DESC
                ''',
                (timeframe,),
            )
            rows = cursor.fetchall()
            conn.close()

            result = {}
            for row in rows:
                row_dict = dict(row)
                symbol = row_dict.get("交易对", "")
                if symbol:
                    if symbol in result:
                        # 已有该符号最新行
                        continue
                    ts_seconds = self._parse_ts(row_dict)
                    if not self._is_fresh(ts_seconds, timeframe):
                        self.stats["stale"] += 1
                        logger.debug("跳过陈旧行 %s %s ts=%s", table, symbol, ts_seconds)
                        continue
                    self._maybe_refresh_symbols()
                    if self.allowed_symbols and symbol.upper() not in self.allowed_symbols:
                        self.stats["symbol_filtered"] += 1
                        continue
                    result[symbol] = row_dict
            return result
        except Exception as e:
            logger.warning(f"读取表 {table} 失败: {e}")
            return {}

    def _get_symbol_all_tables(self, symbol: str, timeframe: str) -> dict[str, dict]:
        """获取单个币种所有表的数据"""
        result = {}
        for table in RULES_BY_TABLE:
            data = self._get_table_data(table, timeframe)
            if symbol in data:
                result[table] = data[symbol]
        return result

    def _is_cooled_down(self, rule: SignalRule, symbol: str, timeframe: str) -> bool:
        """检查是否在冷却期"""
        key = f"{rule.name}_{symbol}_{timeframe}"
        last = self.cooldown.get(key, 0)
        return time.time() - last > rule.cooldown

    def _set_cooldown(self, rule: SignalRule, symbol: str, timeframe: str):
        """设置冷却（同时持久化）"""
        key = f"{rule.name}_{symbol}_{timeframe}"
        ts = time.time()
        self.cooldown[key] = ts
        self._cooldown_storage.set(key, ts)

    def check_signals(self) -> list[Signal]:
        """检查所有规则"""
        signals = []
        self.stats["checks"] += 1

        for table, rules in RULES_BY_TABLE.items():
            active_rules = [r for r in rules if r.name in self.enabled_rules]
            if not active_rules:
                continue

            all_timeframes = set()
            for r in active_rules:
                all_timeframes.update(r.timeframes)

            for timeframe in all_timeframes:
                current_data = self._get_table_data(table, timeframe)

                for symbol, curr_row in current_data.items():
                    volume = curr_row.get("成交额") or curr_row.get("成交额（USDT）") or 0
                    cache_key = f"{table}_{symbol}_{timeframe}"
                    prev_row = self.baseline.get(cache_key)

                    if not self.baseline_loaded:
                        self.baseline[cache_key] = curr_row
                        continue

                    for rule in active_rules:
                        if timeframe not in rule.timeframes:
                            continue
                        if volume < rule.min_volume:
                            continue

                        try:
                            if rule.check_condition(prev_row, curr_row) and self._is_cooled_down(
                                rule, symbol, timeframe
                            ):
                                price = curr_row.get("当前价格") or curr_row.get("价格") or curr_row.get("收盘价") or 0
                                rule_msg = rule.format_message(prev_row, curr_row)

                                # 构建信号
                                signal = Signal(
                                    symbol=symbol,
                                    direction=rule.direction,
                                    strength=rule.strength,
                                    rule_name=rule.name,
                                    timeframe=timeframe,
                                    price=price,
                                    message=rule_msg,
                                    category=rule.category,
                                    subcategory=rule.subcategory,
                                    table=table,
                                    priority=rule.priority,
                                )

                                # 格式化完整消息（如果有格式化器）
                                if self.formatter:
                                    curr_all = self._get_symbol_all_tables(symbol, timeframe)
                                    prev_all = {}
                                    for t in RULES_BY_TABLE:
                                        pk = f"{t}_{symbol}_{timeframe}"
                                        if pk in self.baseline:
                                            prev_all[t] = self.baseline[pk]

                                    signal.full_message = self.formatter(
                                        symbol=symbol,
                                        direction=rule.direction,
                                        rule_name=rule.name,
                                        timeframe=timeframe,
                                        strength=rule.strength,
                                        curr_data=curr_all,
                                        prev_data=prev_all,
                                        rule_message=rule_msg,
                                    )

                                signals.append(signal)
                                self._set_cooldown(rule, symbol, timeframe)
                                self.stats["signals"] += 1

                                logger.info(f"信号触发: {symbol} {rule.direction} - {rule.name} ({timeframe})")

                                # 发布事件
                                self._publish_event(signal, rule)

                        except Exception as e:
                            self.stats["errors"] += 1
                            logger.warning(f"规则检查异常 {rule.name}: {e}")

                    self.baseline[cache_key] = curr_row

        if not self.baseline_loaded:
            self.baseline_loaded = True
            logger.info(f"基线缓存完成，共 {len(self.baseline)} 条记录")

        return signals

    def _publish_event(self, signal: Signal, rule: SignalRule):
        """发布信号事件"""
        event = SignalEvent(
            symbol=signal.symbol,
            signal_type=rule.name,
            direction=signal.direction,
            strength=signal.strength,
            message_key=f"signal.{rule.category}.{rule.subcategory}",
            message_params={
                "symbol": signal.symbol,
                "price": signal.price,
                "timeframe": signal.timeframe,
            },
            timestamp=signal.timestamp,
            timeframe=signal.timeframe,
            price=signal.price,
            source="sqlite",
            rule_name=rule.name,
            category=rule.category,
            subcategory=rule.subcategory,
            table=signal.table,
            extra={"message": signal.message},
        )
        SignalPublisher.publish(event)

    def run_loop(self, interval: int = 60):
        """持续运行"""
        self._running = True
        logger.info(f"SQLite 信号引擎启动，间隔: {interval}秒，规则数: {len(self.enabled_rules)}")

        while self._running:
            try:
                signals = self.check_signals()
                if signals:
                    for signal in signals:
                        self._emit_signal(signal)
                    logger.info(f"本轮检测到 {len(signals)} 个信号")
            except Exception as e:
                logger.error(f"检查循环异常: {e}")

            time.sleep(interval)

    def get_stats(self) -> dict:
        """获取统计"""
        return {
            **self.stats,
            "baseline_size": len(self.baseline),
            "cooldown_size": len(self.cooldown),
            "enabled_rules": len(self.enabled_rules),
            "total_rules": len(ALL_RULES),
        }


# 单例
_engine: SQLiteSignalEngine | None = None
_engine_lock = threading.Lock()


def get_sqlite_engine() -> SQLiteSignalEngine:
    """获取 SQLite 引擎单例"""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = SQLiteSignalEngine()
    return _engine
