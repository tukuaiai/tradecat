"""
数据精度裁剪工具

规则：
- |x| >= 1: 保留 2 位小数
- |x| < 1: 保留 3 位有效数字
- 去除尾部多余 0
"""
import math
import os

TRIM_ENABLED = os.getenv("INDICATOR_TRIM_PRECISION", "true").lower() != "false"


def format_number(x) -> str:
    """格式化单个数值"""
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return None
    try:
        val = float(x)
    except (TypeError, ValueError):
        return str(x) if x else None

    if val == 0:
        return "0"

    abs_val = abs(val)
    if abs_val >= 1:
        result = f"{val:.2f}"
    else:
        exp = math.floor(math.log10(abs_val))
        precision = -exp + 2
        result = f"{round(val, precision):.{precision}f}"

    if '.' in result:
        result = result.rstrip('0').rstrip('.')
    return result


def trim_dataframe(df, exclude: set = None):
    """裁剪 DataFrame 中所有数值列"""
    if not TRIM_ENABLED or df.empty:
        return df
    exclude = exclude or {"交易对", "周期", "数据时间"}
    result = df.copy()
    for col in result.columns:
        if col not in exclude:
            try:
                result[col] = result[col].apply(format_number)
            except Exception:
                pass
    return result
