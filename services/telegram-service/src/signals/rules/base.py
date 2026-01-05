"""
信号规则基础定义
"""
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class ConditionType(Enum):
    """条件类型枚举"""
    STATE_CHANGE = "state_change"      # 状态变化 (prev_value → curr_value)
    THRESHOLD_CROSS_UP = "cross_up"    # 从下方穿越阈值
    THRESHOLD_CROSS_DOWN = "cross_down"  # 从上方穿越阈值
    CROSS_UP = "line_cross_up"         # 两值交叉上穿 (a < b → a > b)
    CROSS_DOWN = "line_cross_down"     # 两值交叉下穿 (a > b → a < b)
    CONTAINS = "contains"              # 字符串包含
    RANGE_ENTER = "range_enter"        # 进入区间
    RANGE_EXIT = "range_exit"          # 离开区间
    CUSTOM = "custom"                  # 自定义lambda


@dataclass
class SignalRule:
    """信号规则数据类"""
    name: str                          # 规则名称
    table: str                         # 数据表名
    category: str                      # 分类: momentum/trend/volatility/volume/futures/pattern/misc
    subcategory: str                   # 子分类: rsi/kdj/macd 等
    direction: str                     # 方向: BUY/SELL/ALERT
    strength: int                      # 强度: 0-100
    priority: str = "medium"           # 优先级: high/medium/low
    timeframes: List[str] = field(default_factory=lambda: ["1h", "4h", "1d"])
    cooldown: int = 3600               # 冷却时间(秒)
    min_volume: float = 100000         # 最小成交额
    condition_type: ConditionType = ConditionType.CUSTOM
    condition_config: Dict[str, Any] = field(default_factory=dict)
    message_template: str = ""
    fields: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True

    def check_condition(self, prev: Optional[Dict], curr: Dict) -> bool:
        """检查条件是否满足"""
        if not self.enabled:
            return False

        try:
            ct = self.condition_type
            cfg = self.condition_config

            if ct == ConditionType.STATE_CHANGE:
                if not prev:
                    return False
                fld = cfg.get("field", "")
                from_vals = cfg.get("from_values", [])
                to_vals = cfg.get("to_values", [])
                prev_val = str(prev.get(fld, ""))
                curr_val = str(curr.get(fld, ""))
                return prev_val in from_vals and curr_val in to_vals

            elif ct == ConditionType.THRESHOLD_CROSS_UP:
                if not prev:
                    return False
                fld = cfg.get("field", "")
                threshold = cfg.get("threshold", 0)
                prev_val = prev.get(fld, 0) or 0
                curr_val = curr.get(fld, 0) or 0
                return prev_val <= threshold < curr_val

            elif ct == ConditionType.THRESHOLD_CROSS_DOWN:
                if not prev:
                    return False
                fld = cfg.get("field", "")
                threshold = cfg.get("threshold", 0)
                prev_val = prev.get(fld, 0) or 0
                curr_val = curr.get(fld, 0) or 0
                return prev_val >= threshold > curr_val

            elif ct == ConditionType.CROSS_UP:
                if not prev:
                    return False
                fa = cfg.get("field_a", "")
                fb = cfg.get("field_b", "")
                prev_a = prev.get(fa, 0) or 0
                prev_b = prev.get(fb, 0) or 0
                curr_a = curr.get(fa, 0) or 0
                curr_b = curr.get(fb, 0) or 0
                return prev_a <= prev_b and curr_a > curr_b

            elif ct == ConditionType.CROSS_DOWN:
                if not prev:
                    return False
                fa = cfg.get("field_a", "")
                fb = cfg.get("field_b", "")
                prev_a = prev.get(fa, 0) or 0
                prev_b = prev.get(fb, 0) or 0
                curr_a = curr.get(fa, 0) or 0
                curr_b = curr.get(fb, 0) or 0
                return prev_a >= prev_b and curr_a < curr_b

            elif ct == ConditionType.CONTAINS:
                fld = cfg.get("field", "")
                patterns = cfg.get("patterns", [])
                match_any = cfg.get("match_any", True)
                val = str(curr.get(fld, ""))
                if match_any:
                    return any(p in val for p in patterns)
                return all(p in val for p in patterns)

            elif ct == ConditionType.RANGE_ENTER:
                if not prev:
                    return False
                fld = cfg.get("field", "")
                min_v = cfg.get("min_value", float("-inf"))
                max_v = cfg.get("max_value", float("inf"))
                prev_val = prev.get(fld, 0) or 0
                curr_val = curr.get(fld, 0) or 0
                prev_in = min_v <= prev_val <= max_v
                curr_in = min_v <= curr_val <= max_v
                return not prev_in and curr_in

            elif ct == ConditionType.RANGE_EXIT:
                if not prev:
                    return False
                fld = cfg.get("field", "")
                min_v = cfg.get("min_value", float("-inf"))
                max_v = cfg.get("max_value", float("inf"))
                prev_val = prev.get(fld, 0) or 0
                curr_val = curr.get(fld, 0) or 0
                prev_in = min_v <= prev_val <= max_v
                curr_in = min_v <= curr_val <= max_v
                return prev_in and not curr_in

            elif ct == ConditionType.CUSTOM:
                func = cfg.get("func")
                if callable(func):
                    return func(prev, curr)
                return False

            return False
        except Exception as e:
            logger.warning(f"规则检查异常 {self.name}: {e}")
            return False

    def format_message(self, prev: Optional[Dict], curr: Dict) -> str:
        """格式化消息"""
        try:
            fmt_args = {}
            for arg_name, field_name in self.fields.items():
                if arg_name.startswith("prev_"):
                    fmt_args[arg_name] = prev.get(field_name, 0) if prev else 0
                else:
                    fmt_args[arg_name] = curr.get(field_name, 0) or 0
            return self.message_template.format(**fmt_args)
        except Exception as e:
            logger.warning(f"消息格式化异常 {self.name}: {e}")
            return self.message_template
