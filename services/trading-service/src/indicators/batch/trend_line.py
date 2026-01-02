"""趋势线扫描器 - Pine Trend Lines v2 完整复刻"""
import numpy as np
import pandas as pd
from typing import List, Optional, Tuple
from ..base import Indicator, IndicatorMeta, register


def _pivot_high(highs: np.ndarray, idx: int, prd: int) -> Optional[float]:
    """pivothigh(prd, prd)"""
    if idx < 2 * prd:
        return None
    window = highs[idx - 2 * prd : idx + 1]
    pivot_val = highs[idx - prd]
    return pivot_val if pivot_val == window.max() else None


def _pivot_low(lows: np.ndarray, idx: int, prd: int) -> Optional[float]:
    """pivotlow(prd, prd)"""
    if idx < 2 * prd:
        return None
    window = lows[idx - 2 * prd : idx + 1]
    pivot_val = lows[idx - prd]
    return pivot_val if pivot_val == window.min() else None


def _add_to_array(vals: List, poss: List, val: float, bar_index: int, keep: int):
    vals.insert(0, val)
    poss.insert(0, bar_index)
    if len(vals) > keep:
        vals.pop()
    if len(poss) > keep:
        poss.pop()


def _build_lines(bvals: List, bpos: List, tvals: List, tpos: List, 
                 prd: int, maxline: int, bar_index: int, closes: np.ndarray
                 ) -> Tuple[List, List]:
    """完整复刻 Pine 的 line 检测循环"""
    blines = [None] * maxline
    tlines = [None] * maxline
    count_lo = 0
    count_hi = 0
    PPnum = len(bvals)

    for p1 in range(0, PPnum - 1):
        uv1 = uv2 = 0.0
        up1 = up2 = 0
        # 低点线（上升支撑）
        if count_lo <= maxline - 1:
            for p2 in range(PPnum - 1, p1, -1):
                val1, val2 = bvals[p1], bvals[p2]
                pos1, pos2 = bpos[p1], bpos[p2]
                if val1 is None or val2 is None or pos1 is None or pos2 is None:
                    continue
                if val1 > val2:
                    diff = (val1 - val2) / (pos1 - pos2)
                    hline = val2 + diff
                    lloc = bar_index
                    valid = True
                    for x in range(pos2 + 1 - prd, bar_index + 1):
                        idx = bar_index - x
                        if idx < 0:
                            continue
                        if closes[idx] < hline:
                            valid = False
                            break
                        lloc = x
                        hline = hline + diff
                    if valid:
                        uv1 = hline - diff
                        uv2 = val2
                        up1 = lloc
                        up2 = pos2
                        break

        dv1 = dv2 = 0.0
        dp1 = dp2 = 0
        # 高点线（下降压制）
        if count_hi <= maxline - 1:
            for p2 in range(PPnum - 1, p1, -1):
                val1, val2 = tvals[p1], tvals[p2]
                pos1, pos2 = tpos[p1], tpos[p2]
                if val1 is None or val2 is None or pos1 is None or pos2 is None:
                    continue
                if val1 < val2:
                    diff = (val2 - val1) / float(pos1 - pos2)
                    hline = val2 - diff
                    lloc = bar_index
                    valid = True
                    for x in range(pos2 + 1 - prd, bar_index + 1):
                        idx = bar_index - x
                        if idx < 0:
                            continue
                        if closes[idx] > hline:
                            valid = False
                            break
                        lloc = x
                        hline = hline - diff
                    if valid:
                        dv1 = hline + diff
                        dv2 = val2
                        dp1 = lloc
                        dp2 = pos2
                        break

        if up1 != 0 and up2 != 0 and count_lo < maxline:
            blines[count_lo] = (up2 - prd, uv2, up1, uv1)
            count_lo += 1
        if dp1 != 0 and dp2 != 0 and count_hi < maxline:
            tlines[count_hi] = (dp2 - prd, dv2, dp1, dv1)
            count_hi += 1

    blines = [ln for ln in blines if ln is not None]
    tlines = [ln for ln in tlines if ln is not None]
    return blines, tlines


def _pick_direction_and_distance(blines: List, tlines: List, bar_index: int, close_price: float) -> Tuple[str, float]:
    """方向：有压制线->空；有支撑线->多；都没有->震荡"""
    if tlines:
        x1, y1, x2, y2 = tlines[0]
        direction = "空"
    elif blines:
        x1, y1, x2, y2 = blines[0]
        direction = "多"
    else:
        return "震荡", 0.0

    if x2 == x1:
        return direction, 0.0
    k = (y2 - y1) / (x2 - x1)
    y_at_now = y1 + k * (bar_index - x1)
    if y_at_now == 0:
        return direction, 0.0
    dist_pct = (close_price - y_at_now) / y_at_now * 100.0
    return direction, dist_pct


@register
class TrendLine(Indicator):
    meta = IndicatorMeta(name="趋势线榜单.py", lookback=100, is_incremental=False, min_data=45)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        prd = 20
        PPnum = 3
        
        if not self._check_data(df):
            return self._make_insufficient_result(df, symbol, interval, {"信号": None})

        highs = df["high"].to_numpy(dtype=float)
        lows = df["low"].to_numpy(dtype=float)
        closes = df["close"].to_numpy(dtype=float)

        tval: List = [None] * PPnum
        tpos: List = [None] * PPnum
        bval: List = [None] * PPnum
        bpos: List = [None] * PPnum

        bar_index = len(df) - 1
        for i in range(len(df)):
            ph = _pivot_high(highs, i, prd)
            pl = _pivot_low(lows, i, prd)
            if ph is not None:
                _add_to_array(tval, tpos, ph, i, PPnum)
            if pl is not None:
                _add_to_array(bval, bpos, pl, i, PPnum)

        blines, tlines = _build_lines(bval, bpos, tval, tpos, prd, maxline=3, bar_index=bar_index, closes=closes)
        direction, dist_pct = _pick_direction_and_distance(blines, tlines, bar_index, closes[-1])

        return self._make_result(df, symbol, interval, {
            "趋势方向": direction,
            "距离趋势线%": round(dist_pct, 4),
            "当前价格": float(closes[-1]),
        })
