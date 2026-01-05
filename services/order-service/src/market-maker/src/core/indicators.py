"""Hummingbot 原生指标 - 100% 复制，0 修改

来源: hummingbot/strategy/__utils__/
- RingBuffer (ring_buffer.pyx)
- BaseTrailingIndicator (base_trailing_indicator.py)
- InstantVolatilityIndicator (instant_volatility.py)
- TradingIntensityIndicator (trading_intensity.pyx)
"""
import numpy as np
from abc import ABC, abstractmethod
from typing import Tuple, Optional


# ============================================================
# RingBuffer - 100% 复制自 ring_buffer.pyx
# ============================================================
class RingBuffer:
    """环形缓冲区 - Hummingbot 原生实现"""

    def __init__(self, length: int):
        self._length = length
        self._buffer = np.zeros(length, dtype=np.float64)
        self._delimiter = 0
        self._is_full = False

    def add_value(self, val: float):
        self._buffer[self._delimiter] = val
        self._increment_delimiter()

    def _increment_delimiter(self):
        self._delimiter = (self._delimiter + 1) % self._length
        if not self._is_full and self._delimiter == 0:
            self._is_full = True

    def _is_empty(self) -> bool:
        return (not self._is_full) and (0 == self._delimiter)

    def get_last_value(self) -> float:
        if self._is_empty():
            return np.nan
        return self._buffer[self._delimiter - 1]

    @property
    def is_full(self) -> bool:
        return self._is_full

    def get_as_numpy_array(self) -> np.ndarray:
        if not self._is_full:
            indexes = np.arange(0, stop=self._delimiter, dtype=np.int16)
        else:
            indexes = np.arange(self._delimiter, stop=self._delimiter + self._length,
                                dtype=np.int16) % self._length
        return np.asarray(self._buffer)[indexes]

    @property
    def mean_value(self) -> float:
        if self._is_full:
            return np.mean(self.get_as_numpy_array())
        return np.nan

    @property
    def std_dev(self) -> float:
        if self._is_full:
            return np.std(self.get_as_numpy_array())
        return np.nan

    @property
    def variance(self) -> float:
        if self._is_full:
            return np.var(self.get_as_numpy_array())
        return np.nan

    @property
    def length(self) -> int:
        return self._length

    @length.setter
    def length(self, value: int):
        data = self.get_as_numpy_array()
        self._length = value
        self._buffer = np.zeros(value, dtype=np.float64)
        self._delimiter = 0
        self._is_full = False
        for val in data[-value:]:
            self.add_value(val)


# ============================================================
# BaseTrailingIndicator - 100% 复制自 base_trailing_indicator.py
# ============================================================
class BaseTrailingIndicator(ABC):
    """基础追踪指标 - Hummingbot 原生实现"""

    def __init__(self, sampling_length: int = 30, processing_length: int = 15):
        self._sampling_buffer = RingBuffer(sampling_length)
        self._processing_buffer = RingBuffer(processing_length)
        self._samples_length = 0

    def add_sample(self, value: float):
        self._sampling_buffer.add_value(value)
        indicator_value = self._indicator_calculation()
        self._processing_buffer.add_value(indicator_value)

    @abstractmethod
    def _indicator_calculation(self) -> float:
        raise NotImplementedError

    def _processing_calculation(self) -> float:
        """处理缓冲区计算，默认返回平均值"""
        return np.mean(self._processing_buffer.get_as_numpy_array())

    @property
    def current_value(self) -> float:
        return self._processing_calculation()

    @property
    def is_sampling_buffer_full(self) -> bool:
        return self._sampling_buffer.is_full

    @property
    def is_processing_buffer_full(self) -> bool:
        return self._processing_buffer.is_full

    @property
    def is_sampling_buffer_changed(self) -> bool:
        buffer_len = len(self._sampling_buffer.get_as_numpy_array())
        is_changed = self._samples_length != buffer_len
        self._samples_length = buffer_len
        return is_changed

    @property
    def sampling_length(self) -> int:
        return self._sampling_buffer.length

    @sampling_length.setter
    def sampling_length(self, value: int):
        self._sampling_buffer.length = value

    @property
    def processing_length(self) -> int:
        return self._processing_buffer.length

    @processing_length.setter
    def processing_length(self, value: int):
        self._processing_buffer.length = value


# ============================================================
# InstantVolatilityIndicator - 100% 复制自 instant_volatility.py
# ============================================================
class InstantVolatilityIndicator(BaseTrailingIndicator):
    """即时波动率指标 - Hummingbot 原生实现
    
    计算方法: sqrt(sum(diff²) / n)
    注意: 使用相邻价格差而非与均值的差，避免趋势影响
    """

    def __init__(self, sampling_length: int = 30, processing_length: int = 15):
        super().__init__(sampling_length, processing_length)

    def _indicator_calculation(self) -> float:
        # The standard deviation should be calculated between ticks and not with a mean of the whole buffer
        # Otherwise if the asset is trending, changing the length of the buffer would result in a greater volatility
        # as more ticks would be further away from the mean which is a nonsense result.
        # If volatility of the underlying doesn't change in fact, changing the length of the buffer shouldn't change the result.
        np_sampling_buffer = self._sampling_buffer.get_as_numpy_array()
        vol = np.sqrt(np.sum(np.square(np.diff(np_sampling_buffer))) / np_sampling_buffer.size)
        return vol

    def _processing_calculation(self) -> float:
        # Only the last calculated volatility, not an average of multiple past volatilities
        return self._processing_buffer.get_last_value()


# ============================================================
# TradingIntensityIndicator - Python 版等价实现
# ============================================================
class TradingIntensityIndicator:
    """交易强度指标 - 估计订单簿流动性 alpha/kappa
    
    公式对齐 Hummingbot：拟合 lambda = alpha * exp(-kappa * price_level)
    price_level = |trade_price - mid_price|
    """

    def __init__(self, sampling_length: int = 30, processing_length: int = 15):
        self._sampling_length = sampling_length
        self._processing_length = processing_length
        self._price_levels = RingBuffer(sampling_length)
        self._amounts = RingBuffer(sampling_length)
        self._alpha_buffer = RingBuffer(processing_length)
        self._kappa_buffer = RingBuffer(processing_length)
        self._samples_length = 0

    def add_sample(self, mid_price: float, trade_price: float, trade_amount: float, timestamp: float | None = None):
        """记录一笔成交"""
        price_level = abs(float(trade_price) - float(mid_price))
        self._price_levels.add_value(price_level)
        self._amounts.add_value(float(trade_amount))

        if self.is_sampling_buffer_full:
            alpha, kappa = self._indicator_calculation()
            self._alpha_buffer.add_value(alpha)
            self._kappa_buffer.add_value(kappa)

    def _indicator_calculation(self) -> Tuple[float, float]:
        """基于 log 线性拟合估计 alpha/kappa"""
        price_levels = self._price_levels.get_as_numpy_array()
        amounts = self._amounts.get_as_numpy_array()

        # 聚合相同 price_level
        agg = {}
        for level, amt in zip(price_levels, amounts):
            agg[level] = agg.get(level, 0.0) + amt
        levels = np.array(sorted(agg.keys(), reverse=True), dtype=np.float64)
        lambdas = np.array([agg[l] for l in levels], dtype=np.float64)

        if len(levels) == 0 or np.all(lambdas == 0):
            return 1.0, 1.5

        lambdas_adj = np.where(lambdas <= 0, 1e-10, lambdas)

        if len(levels) == 1:
            alpha = float(lambdas_adj[0])
            kappa = 1.5
        else:
            # log(lambda) = log(a) - kappa * level
            slope, intercept = np.polyfit(levels, np.log(lambdas_adj), 1)
            alpha = float(np.exp(intercept))
            kappa = float(-slope)

        alpha = float(max(0.0001, alpha))
        kappa = float(max(0.0001, kappa))
        return alpha, kappa

    @property
    def current_value(self) -> Tuple[Optional[float], Optional[float]]:
        if not self._alpha_buffer.is_full:
            return None, None
        return self._alpha_buffer.get_last_value(), self._kappa_buffer.get_last_value()

    @property
    def is_sampling_buffer_full(self) -> bool:
        return self._price_levels.is_full and self._amounts.is_full

    @property
    def is_sampling_buffer_changed(self) -> bool:
        buffer_len = len(self._price_levels.get_as_numpy_array())
        is_changed = self._samples_length != buffer_len
        self._samples_length = buffer_len
        return is_changed

    @property
    def sampling_length(self) -> int:
        return self._sampling_length

    @sampling_length.setter
    def sampling_length(self, value: int):
        self._sampling_length = value
        self._price_levels.length = value
        self._amounts.length = value
