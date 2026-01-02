"""
信号检测引擎
监控 SQLite 表变化，根据规则触发信号
"""

import sqlite3
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from .rules import SIGNAL_RULES, TIMEFRAMES, SIGNAL_COOLDOWN, MIN_VOLUME

logger = logging.getLogger(__name__)

DB_PATH = "/home/lenovo/.projects/tradecat/libs/database/services/telegram-service/market_data.db"


@dataclass
class Signal:
    """信号数据结构"""
    symbol: str
    direction: str  # BUY / SELL / ALERT
    strength: int   # 0-100
    rule_name: str
    timeframe: str
    price: float
    message: str
    timestamp: datetime = field(default_factory=datetime.now)


class SignalEngine:
    """信号检测引擎"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.state_cache: Dict[str, Dict] = {}  # {table_symbol_tf: row_data}
        self.cooldown_cache: Dict[str, float] = {}  # {signal_key: last_trigger_time}
        self.callbacks: List[callable] = []
        self.baseline_loaded = False  # 基线是否已加载
    
    def register_callback(self, callback: callable):
        """注册信号回调函数"""
        self.callbacks.append(callback)
    
    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _get_table_data(self, table: str, timeframe: str) -> Dict[str, Dict]:
        """获取表中指定周期的所有数据"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # 查询指定周期的数据
            cursor.execute(f"""
                SELECT * FROM "{table}" 
                WHERE "周期" = ? OR "周期" IS NULL
            """, (timeframe,))
            
            rows = cursor.fetchall()
            conn.close()
            
            result = {}
            for row in rows:
                row_dict = dict(row)
                symbol = row_dict.get('交易对', '')
                if symbol:
                    result[symbol] = row_dict
            
            return result
        except Exception as e:
            logger.debug(f"读取表 {table} 失败: {e}")
            return {}
    
    def _is_cooled_down(self, signal_key: str) -> bool:
        """检查信号是否在冷却期"""
        last_time = self.cooldown_cache.get(signal_key, 0)
        return time.time() - last_time > SIGNAL_COOLDOWN
    
    def _set_cooldown(self, signal_key: str):
        """设置信号冷却"""
        self.cooldown_cache[signal_key] = time.time()
    
    def _format_message(self, rule: dict, prev: dict, curr: dict) -> str:
        """格式化信号消息"""
        try:
            fields = rule.get('fields', {})
            format_args = {}
            
            for arg_name, field_name in fields.items():
                if 'prev' in arg_name:
                    format_args[arg_name] = prev.get(field_name, 0) if prev else 0
                else:
                    format_args[arg_name] = curr.get(field_name, 0)
            
            return rule['message'].format(**format_args)
        except Exception:
            return rule['message']
    
    def check_signals(self) -> List[Signal]:
        """检查所有规则，返回触发的信号"""
        signals = []
        
        for rule in SIGNAL_RULES:
            table = rule['table']
            
            for timeframe in TIMEFRAMES:
                # 获取当前数据
                current_data = self._get_table_data(table, timeframe)
                
                for symbol, curr_row in current_data.items():
                    # 成交额过滤
                    volume = curr_row.get('成交额', 0) or 0
                    if volume < MIN_VOLUME:
                        continue
                    
                    # 获取缓存的上次状态
                    cache_key = f"{table}_{symbol}_{timeframe}"
                    prev_row = self.state_cache.get(cache_key)
                    
                    # 第一次只缓存基线，不触发信号
                    if not self.baseline_loaded:
                        self.state_cache[cache_key] = curr_row
                        continue
                    
                    # 检查规则条件
                    try:
                        if rule['condition'](prev_row, curr_row):
                            # 检查冷却
                            signal_key = f"{rule['name']}_{symbol}_{timeframe}"
                            if self._is_cooled_down(signal_key):
                                # 触发信号
                                signal = Signal(
                                    symbol=symbol,
                                    direction=rule['direction'],
                                    strength=rule['strength'],
                                    rule_name=rule['name'],
                                    timeframe=timeframe,
                                    price=curr_row.get('当前价格', 0) or curr_row.get('价格', 0) or 0,
                                    message=self._format_message(rule, prev_row, curr_row)
                                )
                                signals.append(signal)
                                self._set_cooldown(signal_key)
                                
                                logger.info(f"信号触发: {signal.symbol} {signal.direction} - {signal.rule_name}")
                    except Exception as e:
                        logger.debug(f"规则检查异常 {rule['name']}: {e}")
                    
                    # 更新缓存
                    self.state_cache[cache_key] = curr_row
        
        # 第一次加载完成后标记基线已加载
        if not self.baseline_loaded:
            self.baseline_loaded = True
            logger.info(f"基线缓存完成，共 {len(self.state_cache)} 条记录")
        
        return signals
    
    def notify(self, signals: List[Signal]):
        """通知所有回调"""
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
        """持续运行检查循环"""
        logger.info(f"信号引擎启动，检查间隔: {interval}秒")
        
        while True:
            try:
                signals = self.run_once()
                if signals:
                    logger.info(f"本轮检测到 {len(signals)} 个信号")
            except Exception as e:
                logger.error(f"检查循环异常: {e}")
            
            time.sleep(interval)


# 单例
_engine: Optional[SignalEngine] = None

def get_engine() -> SignalEngine:
    global _engine
    if _engine is None:
        _engine = SignalEngine()
    return _engine
