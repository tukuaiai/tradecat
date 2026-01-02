"""VPVR排行生成器 - 完整复刻原代码"""
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Tuple
from ..base import Indicator, IndicatorMeta, register


@dataclass(slots=True)
class 成交密度桶:
    下沿价格: float
    上沿价格: float
    总成交量: float = 0.0
    主动买量: float = 0.0
    主动卖量: float = 0.0

    @property
    def 中心价格(self) -> float:
        return (self.下沿价格 + self.上沿价格) / 2


def _钳制比例(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _提取节点(桶集合: List[成交密度桶], 条件) -> tuple:
    return tuple(桶.中心价格 for 桶 in 桶集合 if 条件(桶))


def _计算价值区(桶集合: List[成交密度桶], 控制点索引: int, 覆盖目标: float, 总成交量: float):
    left = right = 控制点索引
    当前覆盖 = 桶集合[控制点索引].总成交量 / 总成交量
    while 当前覆盖 < 覆盖目标 and (left > 0 or right < len(桶集合) - 1):
        左值 = 桶集合[left - 1].总成交量 if left > 0 else -1
        右值 = 桶集合[right + 1].总成交量 if right < len(桶集合) - 1 else -1
        if 左值 >= 右值 and left > 0:
            left -= 1
            当前覆盖 += 左值 / 总成交量
        elif right < len(桶集合) - 1:
            right += 1
            当前覆盖 += 右值 / 总成交量
        else:
            break
    return 桶集合[left].下沿价格, 桶集合[right].上沿价格, 当前覆盖


@register
class VPVR(Indicator):
    meta = IndicatorMeta(name="VPVR排行生成器.py", lookback=200, is_incremental=False, min_data=5)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        桶数量 = 48
        价值区占比 = 0.7
        高节点系数 = 0.7
        低节点系数 = 0.25

        if not self._check_data(df):
            return self._make_insufficient_result(df, symbol, interval, {"控制点价格": None})

        价格下限 = float(df["low"].min())
        价格上限 = float(df["high"].max())
        if 价格上限 <= 价格下限:
            调整 = max(价格下限 * 0.001, 1e-6)
            价格上限 += 调整
            价格下限 -= 调整

        桶宽 = (价格上限 - 价格下限) / 桶数量
        桶集合: List[成交密度桶] = [
            成交密度桶(价格下限 + i * 桶宽, 价格下限 + (i + 1) * 桶宽) for i in range(桶数量)
        ]

        总成交量 = 0.0
        for _, row in df.iterrows():
            成交量 = float(row.get("volume", 0.0) or 0.0)
            if 成交量 <= 0:
                continue
            主动买 = float(row.get("taker_buy_volume", 成交量 * 0.5) or 成交量 * 0.5)
            主动卖 = max(成交量 - 主动买, 0.0)
            典型价 = (row["high"] + row["low"] + row["close"]) / 3
            相对 = (典型价 - 价格下限) / (价格上限 - 价格下限)
            索引 = min(max(int(相对 * 桶数量), 0), 桶数量 - 1)
            桶 = 桶集合[索引]
            桶.总成交量 += 成交量
            桶.主动买量 += 主动买
            桶.主动卖量 += 主动卖
            总成交量 += 成交量

        if 总成交量 <= 0:
            return self._make_insufficient_result(df, symbol, interval, {"控制点价格": None})

        控制点索引 = max(range(桶数量), key=lambda i: 桶集合[i].总成交量)
        控制点桶 = 桶集合[控制点索引]
        价值区下沿, 价值区上沿, 覆盖率 = _计算价值区(
            桶集合, 控制点索引, _钳制比例(价值区占比, 0.1, 0.95), 总成交量
        )
        高阈值 = 控制点桶.总成交量 * max(高节点系数, 0.1)
        低阈值 = 控制点桶.总成交量 * max(min(低节点系数, 高节点系数), 0.05)
        高节点 = _提取节点(桶集合, lambda 桶: 桶.总成交量 >= 高阈值)
        低节点 = _提取节点(桶集合, lambda 桶: 0 < 桶.总成交量 <= 低阈值)

        last_price = float(df["close"].iloc[-1])
        if last_price > 价值区上沿:
            价值区位置 = "价值区上方"
        elif last_price < 价值区下沿:
            价值区位置 = "价值区下方"
        else:
            价值区位置 = "价值区内"

        return self._make_result(df, symbol, interval, {
            "VPVR价格": round(控制点桶.中心价格, 6),
            "成交量分布": round(控制点桶.总成交量, 2),
            "价值区下沿": round(价值区下沿, 6),
            "价值区上沿": round(价值区上沿, 6),
            "价值区宽度": round(价值区上沿 - 价值区下沿, 6),
            "价值区宽度百分比": round((价值区上沿 - 价值区下沿) / 控制点桶.中心价格 * 100, 4) if 控制点桶.中心价格 else 0,
            "价值区覆盖率": round(覆盖率 * 100, 2),
            "高成交节点": ",".join(str(round(p, 2)) for p in 高节点),
            "低成交节点": ",".join(str(round(p, 2)) for p in 低节点),
            "价值区位置": 价值区位置,
        })
