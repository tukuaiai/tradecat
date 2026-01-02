"""K线形态指标 - 蜡烛形态 + 价格图形形态"""
import logging
import pandas as pd
import numpy as np
from ..base import Indicator, IndicatorMeta, register

logger = logging.getLogger(__name__)

# talib CDL 中文映射
CDL_NAMES = {
    "CDL2CROWS": "两只乌鸦", "CDL3BLACKCROWS": "三乌鸦", "CDL3INSIDE": "内侧三烛线",
    "CDL3LINESTRIKE": "三线打击", "CDL3OUTSIDE": "外侧三烛线", "CDL3STARSINSOUTH": "南方三星",
    "CDL3WHITESOLDIERS": "三白兵", "CDLABANDONEDBABY": "弃婴", "CDLADVANCEBLOCK": "推进受阻",
    "CDLBELTHOLD": "捉腰带线", "CDLBREAKAWAY": "脱离形态", "CDLCLOSINGMARUBOZU": "收盘光头光脚",
    "CDLCONCEALBABYSWALL": "藏婴吞没", "CDLCOUNTERATTACK": "反击线", "CDLDARKCLOUDCOVER": "乌云盖顶",
    "CDLDOJI": "十字星", "CDLDOJISTAR": "十字星", "CDLDRAGONFLYDOJI": "蜻蜓十字",
    "CDLENGULFING": "吞没形态", "CDLEVENINGDOJISTAR": "暮星十字", "CDLEVENINGSTAR": "暮星",
    "CDLGAPSIDESIDEWHITE": "并列阴阳线", "CDLGRAVESTONEDOJI": "墓碑十字", "CDLHAMMER": "锤子线",
    "CDLHANGINGMAN": "上吊线", "CDLHARAMI": "孕线", "CDLHARAMICROSS": "十字孕线",
    "CDLHIGHWAVE": "高浪线", "CDLHIKKAKE": "陷阱形态", "CDLHIKKAKEMOD": "改良陷阱形态",
    "CDLHOMINGPIGEON": "家鸽形态", "CDLIDENTICAL3CROWS": "三胞胎乌鸦", "CDLINNECK": "颈内线",
    "CDLINVERTEDHAMMER": "倒锤子", "CDLKICKING": "踢线", "CDLKICKINGBYLENGTH": "长腿踢线",
    "CDLLADDERBOTTOM": "梯底", "CDLLONGLEGGEDDOJI": "长腿十字", "CDLLONGLINE": "长蜡烛",
    "CDLMARUBOZU": "光头光脚", "CDLMATHOLD": "接力形态", "CDLMATCHINGLOW": "匹配低价",
    "CDLMORNINGDOJISTAR": "晨星十字", "CDLMORNINGSTAR": "晨星", "CDLONNECK": "颈上线",
    "CDLPIERCING": "穿刺线", "CDLRICKSHAWMAN": "风高浪大线", "CDLRISEFALL3METHODS": "三法形态",
    "CDLSEPARATINGLINES": "分离线", "CDLSHOOTINGSTAR": "流星线", "CDLSHORTLINE": "短蜡烛",
    "CDLSPINNINGTOP": "纺锤线", "CDLSTALLEDPATTERN": "停顿形态", "CDLSTICKSANDWICH": "三明治",
    "CDLTAKURI": "探水竿", "CDLTASUKIGAP": "跳空并列阴阳线", "CDLTHRUSTING": "刺透形态",
    "CDLTRISTAR": "三星形态", "CDLUNIQUE3RIVER": "奇特三河", "CDLUPSIDEGAP2CROWS": "向上跳空两只乌鸦",
    "CDLXSIDEGAP3METHODS": "跳空三法",
}

# 价格形态中文映射
PRICE_PATTERN_NAMES = {
    "bull_flag": "上涨旗形", "bear_flag": "下降旗形",
    "ascending_triangle": "上升三角形", "descending_triangle": "下降三角形",
    "symmetrical_triangle": "对称三角形", "rising_wedge": "上升楔形",
    "falling_wedge": "下降楔形", "rising_channel": "上升通道",
    "falling_channel": "下降通道", "horizontal_channel": "水平通道",
    "head_and_shoulder": "头肩顶", "inverse_head_and_shoulder": "头肩底",
    "double_top": "双顶", "double_bottom": "双底",
    "multiple_top_bottom_pattern": "多重顶底", "triangle_pattern": "三角形",
    "wedge_pattern": "楔形", "channel_pattern": "通道形态",
    "cup_and_handle": "杯柄形态", "rounding_bottom": "圆弧底",
    "broadening_top": "扩张顶", "broadening_bottom": "扩张底",
    "diamond_top": "钻石顶", "diamond_bottom": "钻石底",
    "rectangle": "矩形整理", "megaphone": "喇叭口",
}


# 缓存 talib CDL 函数列表
_TALIB_CDL_FUNCS = None

def _get_talib_cdl_funcs():
    """获取并缓存 talib CDL 函数"""
    global _TALIB_CDL_FUNCS
    if _TALIB_CDL_FUNCS is None:
        try:
            import talib
            _TALIB_CDL_FUNCS = [
                (fname, getattr(talib, fname))
                for fname in talib.get_function_groups().get("Pattern Recognition", [])
                if hasattr(talib, fname)
            ]
        except ImportError:
            _TALIB_CDL_FUNCS = []
    return _TALIB_CDL_FUNCS


def _detect_talib(df: pd.DataFrame) -> dict:
    """talib CDL 蜡烛形态检测"""
    if len(df) < 5:
        return {}
    cdl_funcs = _get_talib_cdl_funcs()
    if not cdl_funcs:
        return {}
    o, h, l, c = df["open"].values, df["high"].values, df["low"].values, df["close"].values
    results = {}
    for fname, fn in cdl_funcs:
        try:
            val = float(fn(o, h, l, c)[-1])
            if val != 0:
                results[fname] = val / 100.0
        except:
            pass
    return results


def _detect_tradingpatterns(ohlcv: pd.DataFrame) -> dict:
    """tradingpatterns 库检测（pip install tradingpattern --no-deps）"""
    results = {}
    try:
        from tradingpatterns import tradingpatterns as tp
        # 准备数据：需要 Open/High/Low/Close 列
        df = ohlcv.copy()
        for col in ["open", "high", "low", "close"]:
            if col in df.columns:
                df[col.capitalize()] = df[col]
        pivot_df = tp.find_pivots(df)
        
        detectors = [
            (tp.detect_head_shoulder, {"Head and Shoulder": -1.5, "Inverse Head and Shoulder": 1.5}),
            (tp.detect_double_top_bottom, {"Double Top": -1.2, "Double Bottom": 1.2}),
            (tp.detect_triangle_pattern, {"Ascending Triangle": 1.0, "Descending Triangle": -1.0, "Symmetrical Triangle": 0.8}),
            (tp.detect_wedge, {"Rising Wedge": -1.2, "Falling Wedge": 1.2}),
            (tp.detect_channel, {"Rising Channel": 1.0, "Falling Channel": -1.0, "Horizontal Channel": 0.5}),
        ]
        for fn, patterns in detectors:
            try:
                res = fn(pivot_df)
                if isinstance(res, pd.DataFrame):
                    for col in res.columns:
                        if "pattern" in col.lower():
                            last = res[col].dropna().iloc[-1] if len(res[col].dropna()) > 0 else None
                            if last and last in patterns:
                                key = last.lower().replace(" ", "_")
                                results[key] = patterns[last]
            except:
                pass
    except ImportError:
        pass
    return results


def _detect_patternpy(df: pd.DataFrame) -> dict:
    """patternpy 库检测"""
    results = {}
    try:
        from patternpy.tradingpatterns import (
            calculate_support_resistance, detect_channel, detect_double_top_bottom,
            detect_head_shoulder, detect_triangle_pattern, detect_wedge,
        )
        ohlcv = df.copy()
        for col in ["open", "high", "low", "close"]:
            if col in ohlcv.columns:
                ohlcv[col.capitalize()] = ohlcv[col]
        for need in ["Open", "High", "Low"]:
            if need not in ohlcv:
                ohlcv[need] = ohlcv["Close"]
        pivot_df = calculate_support_resistance(ohlcv)
        
        detectors = [
            (detect_head_shoulder, {"Head and Shoulder": ("head_and_shoulder", -1.5), "Inverse Head and Shoulder": ("inverse_head_and_shoulder", 1.5)}),
            (detect_double_top_bottom, {"Double Top": ("double_top", -1.2), "Double Bottom": ("double_bottom", 1.2)}),
            (detect_channel, {"Rising Channel": ("rising_channel", 1.0), "Falling Channel": ("falling_channel", -1.0), "Horizontal Channel": ("horizontal_channel", 0.5)}),
            (detect_triangle_pattern, {"Ascending Triangle": ("ascending_triangle", 1.0), "Descending Triangle": ("descending_triangle", -1.0), "Symmetrical Triangle": ("symmetrical_triangle", 0.8)}),
            (detect_wedge, {"Rising Wedge": ("rising_wedge", -1.2), "Falling Wedge": ("falling_wedge", 1.2)}),
        ]
        for fn, patterns in detectors:
            try:
                res = fn(pivot_df)
                if isinstance(res, pd.DataFrame):
                    for col in res.columns:
                        if "pattern" in col.lower():
                            last = res[col].dropna()
                            if len(last) > 0:
                                pat = last.iloc[-1]
                                if pat in patterns:
                                    key, val = patterns[pat]
                                    results[key] = val
            except:
                pass
    except ImportError:
        pass
    return results


def _detect_trendln(df: pd.DataFrame) -> dict:
    """trendln 库检测"""
    results = {}
    try:
        import trendln
        if len(df) >= 50:
            close = df["close"].values
            # accuracy=2 是最快的偶数精度
            mins, maxs = trendln.calc_support_resistance(close, method=trendln.METHOD_NSQUREDLOGN, accuracy=2)
            if len(mins) >= 2 and len(maxs) >= 2:
                if maxs[-1][1] > maxs[-2][1] and mins[-1][1] > mins[-2][1]:
                    results["rising_channel"] = 0.8
                elif maxs[-1][1] < maxs[-2][1] and mins[-1][1] < mins[-2][1]:
                    results["falling_channel"] = -0.8
                else:
                    results["horizontal_channel"] = 0.3
    except ImportError:
        pass
    except:
        pass
    return results


def _to_chinese(key: str) -> str:
    """英文形态名转中文"""
    if key in CDL_NAMES:
        return CDL_NAMES[key]
    if key in PRICE_PATTERN_NAMES:
        return PRICE_PATTERN_NAMES[key]
    # 尝试去掉 detect_ 前缀
    clean = key.replace("detect_", "")
    if clean in PRICE_PATTERN_NAMES:
        return PRICE_PATTERN_NAMES[clean]
    return key


@register
class KPattern(Indicator):
    meta = IndicatorMeta(name="K线形态扫描器.py", lookback=50, is_incremental=False, min_data=10)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if not self._check_data(df):
            return self._make_insufficient_result(df, symbol, interval, {"形态": None})
        
        # 准备 OHLCV 数据
        ohlcv = df.copy()
        for col in ["open", "high", "low", "close", "volume"]:
            if col in ohlcv.columns:
                ohlcv[col.capitalize()] = ohlcv[col]
        
        # 检测所有形态
        all_patterns = {}
        all_patterns.update(_detect_talib(df))
        all_patterns.update(_detect_tradingpatterns(ohlcv))
        all_patterns.update(_detect_patternpy(df))
        all_patterns.update(_detect_trendln(df))
        
        # 转中文
        cn_patterns = [_to_chinese(k) for k in all_patterns.keys()]
        pattern_str = ",".join(cn_patterns) if cn_patterns else "无形态"
        
        # 计算强度
        strength = sum(abs(v) for v in all_patterns.values())
        
        quote = df.get("quote_volume", df["volume"] * df["close"])
        turnover = float(quote.iloc[-1]) if not pd.isna(quote.iloc[-1]) else 0
        
        return self._make_result(df, symbol, interval, {
            "形态类型": pattern_str,
            "检测数量": len(all_patterns),
            "强度": round(strength, 2),
            "成交额（USDT）": turnover,
            "当前价格": float(df["close"].iloc[-1]),
        })
