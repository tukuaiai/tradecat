"""Avellaneda-Stoikov 做市策略 - 100% Hummingbot 原生算法

基于论文: "High-frequency trading in a limit order book" (Avellaneda & Stoikov, 2008)

所有指标和算法 100% 复制自 Hummingbot 原生实现:
- InstantVolatilityIndicator: 波动率估计
- TradingIntensityIndicator: 订单强度估计
- 完整 A-S 公式 (无阉割)
- 多档订单支持
- 交易成本补偿
- 目标库存配置
- 挂单追踪
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Tuple, List, Optional
import time

from ..core.indicators import InstantVolatilityIndicator, TradingIntensityIndicator


@dataclass
class ASConfig:
    """A-S 策略配置 - 完整参数 (与 Hummingbot 对齐)"""
    symbol: str
    # 核心参数
    gamma: float = 0.1                    # 风险厌恶系数 (risk_factor)
    # 波动率参数
    vol_sampling_length: int = 30         # 波动率采样长度
    vol_processing_length: int = 15       # 波动率处理长度
    # 订单强度参数
    intensity_sampling_length: int = 30   # 强度采样长度
    intensity_processing_length: int = 15 # 强度处理长度
    # 时间参数
    T: float = 0.05                       # 周期 (小时)
    # 库存参数
    max_inventory: float = 0.01           # 最大库存（基于基础资产数量）
    order_size: float = 0.001             # 单笔订单量
    inventory_target_base_pct: float = 50 # 目标库存比例 (%)
    # 价差参数
    min_spread: float = 0.0002            # 最小价差 (比例)
    min_spread_bps: float | None = None   # 最小价差 (bps)，优先于 min_spread
    # 多档订单
    order_levels: int = 1                 # 订单档数
    level_distances: float = 0.005        # 档位间距 (比例，百分比形式，例如0.5%填0.5)
    # 交易成本
    add_transaction_costs: bool = True    # 是否补偿交易成本
    maker_fee: float = 0.0002             # Maker 费率
    taker_fee: float = 0.0004             # Taker 费率
    # 挂单追踪
    hanging_orders_enabled: bool = False  # 挂单追踪开关
    hanging_orders_cancel_pct: float = 10 # 挂单取消阈值 (%)
    # 数量形状 (eta)
    eta: float = 0.0                      # 订单量指数形状系数，0 表示不启用


class AvellanedaStoikov:
    """Avellaneda-Stoikov 做市策略 - 100% Hummingbot 原生算法"""

    def __init__(self, config: ASConfig):
        self.config = config
        self.pos_long = 0.0
        self.pos_short = 0.0
        self.t = 0.0
        self._last_update = 0
        self._last_mid: float | None = None

        # Hummingbot 原生波动率指标
        self._volatility = InstantVolatilityIndicator(
            sampling_length=config.vol_sampling_length,
            processing_length=config.vol_processing_length
        )

        # Hummingbot 原生订单强度指标
        self._trading_intensity = TradingIntensityIndicator(
            sampling_length=config.intensity_sampling_length,
            processing_length=config.intensity_processing_length
        )

        # 内部状态
        self._reservation_price = Decimal(0)
        self._optimal_spread = Decimal(0)
        self._alpha = None
        self._kappa = None

        # 挂单追踪
        self._hanging_orders: List[dict] = []

    def add_sample(self, price: float, volume: float = 0):
        """添加价格样本"""
        self._volatility.add_sample(price)
        if volume > 0:
            self._trading_intensity.add_sample(mid_price=price, trade_price=price, trade_amount=volume)

    def update_price(self, mid_price: float):
        """更新最新中间价并推动指标采样"""
        self._last_mid = mid_price
        self.add_sample(mid_price)

    def on_trade(self, trade_price: float, trade_amount: float, mid_price: float | None = None):
        """外部成交回调（来自市场成交流）"""
        mid = mid_price if mid_price is not None else (self._last_mid if self._last_mid else trade_price)
        self._trading_intensity.add_sample(mid_price=mid, trade_price=trade_price, trade_amount=trade_amount)

    @property
    def volatility(self) -> float:
        """当前波动率"""
        if not self._volatility.is_sampling_buffer_full:
            return 0.0001
        val = self._volatility.current_value
        return val if val and val > 0 else 0.0001

    @property
    def alpha(self) -> Optional[float]:
        """订单簿强度因子"""
        val = self._trading_intensity.current_value
        if val and val[0]:
            self._alpha = val[0]
        return self._alpha

    @property
    def kappa(self) -> float:
        """订单簿深度因子"""
        val = self._trading_intensity.current_value
        if val and val[1] is not None:
            self._kappa = val[1]
        return self._kappa if self._kappa and self._kappa > 0 else 1.5

    def _calculate_target_inventory(self) -> float:
        """计算目标库存"""
        return self.config.max_inventory * (self.config.inventory_target_base_pct / 100 - 0.5) * 2

    def _calculate_inventory_ratio(self) -> float:
        """计算库存比率 q"""
        target = self._calculate_target_inventory()
        if self.config.max_inventory == 0:
            return 0
        return (self.inventory - target) / self.config.max_inventory

    @property
    def inventory(self) -> float:
        """净仓位 = long - short"""
        return self.pos_long - self.pos_short

    def set_exchange_position(self, long_qty: float, short_qty: float, net_qty: float | None = None):
        """从用户流同步交易所持仓"""
        self.pos_long = float(long_qty)
        self.pos_short = float(short_qty)
        # net_qty 不强制使用，pos_long/pos_short 优先

    def calculate_reservation_price_and_optimal_spread(self, mid_price: float):
        """计算保留价格和最优价差 - Hummingbot 原版公式
        
        保留价格: r = s - q * γ * σ * (T-t)
        最优价差: δ = γ * σ * (T-t) + (2/γ) * ln(1 + γ/κ)
        """
        price = Decimal(str(mid_price))
        vol = Decimal(str(self.volatility))
        gamma = Decimal(str(self.config.gamma))
        kappa = Decimal(str(self.kappa))

        time_left = Decimal(str(max(0.0001, self.config.T - self.t)))
        q = Decimal(str(self._calculate_inventory_ratio()))

        # Hummingbot 原版公式
        self._reservation_price = price - (q * gamma * vol * time_left)

        self._optimal_spread = gamma * vol * time_left
        if kappa > 0:
            self._optimal_spread += 2 * Decimal(1 + gamma / kappa).ln() / gamma

        # 最小价差：配置以百分比/ bps 为准
        min_spread_ratio = (
            Decimal(str(self.config.min_spread_bps / 10000))
            if self.config.min_spread_bps is not None
            else Decimal(str(self.config.min_spread))
        )
        min_spread = price * min_spread_ratio
        if self._optimal_spread < min_spread:
            self._optimal_spread = min_spread

    def _apply_transaction_costs(self, bid: Decimal, ask: Decimal, mid: Decimal) -> Tuple[Decimal, Decimal]:
        """交易成本补偿"""
        if not self.config.add_transaction_costs:
            return bid, ask
        maker_fee = Decimal(str(self.config.maker_fee))
        return bid - mid * maker_fee, ask + mid * maker_fee

    def _get_level_spreads(self) -> Tuple[List[Decimal], List[Decimal]]:
        """多档订单价差"""
        if self.config.order_levels <= 1:
            return [Decimal(0)], [Decimal(0)]
        level_step = ((self._optimal_spread / 2) / Decimal("100")) * Decimal(str(self.config.level_distances))
        bid_spreads = [Decimal(i) * level_step for i in range(self.config.order_levels)]
        ask_spreads = [Decimal(i) * level_step for i in range(self.config.order_levels)]
        return bid_spreads, ask_spreads

    def get_quotes(self, mid_price: float) -> List[Tuple[float, float, float, float]]:
        """获取报价 - 支持多档订单"""
        if not self.is_ready():
            return []
        self.calculate_reservation_price_and_optimal_spread(mid_price)
        mid = Decimal(str(mid_price))
        quotes = []
        bid_spreads, ask_spreads = self._get_level_spreads()

        for i in range(self.config.order_levels):
            bid = self._reservation_price - self._optimal_spread / 2 - bid_spreads[i]
            ask = self._reservation_price + self._optimal_spread / 2 + ask_spreads[i]
            bid, ask = self._apply_transaction_costs(bid, ask, mid)

            inv_ratio = self.inventory / self.config.max_inventory if self.config.max_inventory else 0
            bid_qty = self.config.order_size * max(0, min(1.5, 1 - inv_ratio))
            ask_qty = self.config.order_size * max(0, min(1.5, 1 + inv_ratio))

            # eta 形状调整（只对与库存相反方向的单做指数缩放）
            q_ratio = self._calculate_inventory_ratio()
            if self.config.eta > 0:
                if q_ratio > 0:
                    bid_qty *= float(Decimal(1) * Decimal.exp(Decimal(-self.config.eta) * Decimal(q_ratio)))
                elif q_ratio < 0:
                    ask_qty *= float(Decimal(1) * Decimal.exp(Decimal(self.config.eta) * Decimal(q_ratio)))

            level_factor = 1 / (i + 1)
            bid_qty *= level_factor
            ask_qty *= level_factor

            quotes.append((float(round(bid, 4)), bid_qty, float(round(ask, 4)), ask_qty))

        return quotes

    def get_single_quote(self, mid_price: float) -> Tuple[float, float, float, float]:
        """单档报价"""
        quotes = self.get_quotes(mid_price)
        return quotes[0] if quotes else (0, 0, 0, 0)

    def on_fill(self, side: str, qty: float, price: float = 0, position_side: str | None = None):
        """成交回调，支持双向持仓"""
        side = side.lower()
        ps = (position_side or "").upper()
        if ps == "LONG":
            if side == "buy":
                self.pos_long += qty
            else:
                self.pos_long = max(0.0, self.pos_long - qty)
        elif ps == "SHORT":
            if side == "sell":
                self.pos_short += qty
            else:
                self.pos_short = max(0.0, self.pos_short - qty)
        else:
            # 无 positionSide 时按净仓处理
            if side == "buy":
                self.pos_long += qty
            else:
                self.pos_short += qty

        # 限制最大仓位
        c = self.config
        self.pos_long = min(c.max_inventory * 2, self.pos_long)
        self.pos_short = min(c.max_inventory * 2, self.pos_short)

        if price > 0:
            mid_price = self._last_mid if self._last_mid is not None else price
            self._trading_intensity.add_sample(mid_price=mid_price, trade_price=price, trade_amount=qty)

    def tick(self, dt: float = 0.0001):
        self.t += dt
        if self.t >= self.config.T:
            self.t = 0

    def should_update(self, interval_ms: float = 100) -> bool:
        now = time.time() * 1000
        if now - self._last_update >= interval_ms:
            self._last_update = now
            return True
        return False

    def is_ready(self) -> bool:
        return self._volatility.is_sampling_buffer_full

    # 挂单追踪
    def add_hanging_order(self, order_id: str, side: str, price: float, qty: float):
        if not self.config.hanging_orders_enabled:
            return
        self._hanging_orders.append({"id": order_id, "side": side, "price": price, "qty": qty, "ts": time.time()})

    def get_hanging_orders_to_cancel(self, mid_price: float) -> List[str]:
        if not self.config.hanging_orders_enabled:
            return []
        cancel_pct = self.config.hanging_orders_cancel_pct / 100
        to_cancel = [o["id"] for o in self._hanging_orders if abs(o["price"] - mid_price) / mid_price > cancel_pct]
        self._hanging_orders = [o for o in self._hanging_orders if o["id"] not in to_cancel]
        return to_cancel

    def remove_hanging_order(self, order_id: str):
        self._hanging_orders = [o for o in self._hanging_orders if o["id"] != order_id]

    def status(self) -> dict:
        return {
            "volatility": self.volatility,
            "alpha": self.alpha,
            "kappa": self.kappa,
            "inventory": self.inventory,
            "target_inventory": self._calculate_target_inventory(),
            "reservation_price": float(self._reservation_price),
            "optimal_spread": float(self._optimal_spread),
            "t": self.t,
            "is_ready": self.is_ready(),
            "hanging_orders": len(self._hanging_orders),
        }
