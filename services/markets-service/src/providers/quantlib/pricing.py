"""QuantLib 衍生品定价工具"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import QuantLib as ql


@dataclass
class OptionGreeks:
    """期权希腊值"""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    price: float


class OptionPricer:
    """期权定价器 - Black-Scholes"""

    def __init__(self, risk_free_rate: float = 0.05, dividend_yield: float = 0.0):
        self.risk_free_rate = risk_free_rate
        self.dividend_yield = dividend_yield

    def price_european(
        self,
        spot: float,
        strike: float,
        expiry: date,
        volatility: float,
        option_type: Literal["call", "put"] = "call",
        valuation_date: date | None = None
    ) -> OptionGreeks:
        """计算欧式期权价格和希腊值"""

        val_date = valuation_date or date.today()
        ql.Settings.instance().evaluationDate = ql.Date(val_date.day, val_date.month, val_date.year)

        # 构建期权
        maturity = ql.Date(expiry.day, expiry.month, expiry.year)
        opt_type = ql.Option.Call if option_type == "call" else ql.Option.Put
        payoff = ql.PlainVanillaPayoff(opt_type, strike)
        exercise = ql.EuropeanExercise(maturity)
        option = ql.VanillaOption(payoff, exercise)

        # 市场数据
        spot_handle = ql.QuoteHandle(ql.SimpleQuote(spot))
        rate_handle = ql.YieldTermStructureHandle(
            ql.FlatForward(ql.Settings.instance().evaluationDate, self.risk_free_rate, ql.Actual365Fixed())
        )
        div_handle = ql.YieldTermStructureHandle(
            ql.FlatForward(ql.Settings.instance().evaluationDate, self.dividend_yield, ql.Actual365Fixed())
        )
        vol_handle = ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(ql.Settings.instance().evaluationDate, ql.NullCalendar(), volatility, ql.Actual365Fixed())
        )

        # BS 过程
        process = ql.BlackScholesMertonProcess(spot_handle, div_handle, rate_handle, vol_handle)
        option.setPricingEngine(ql.AnalyticEuropeanEngine(process))

        return OptionGreeks(
            delta=option.delta(),
            gamma=option.gamma(),
            theta=option.theta() / 365,  # 日 theta
            vega=option.vega() / 100,    # 1% vol 变动
            rho=option.rho() / 100,      # 1% rate 变动
            price=option.NPV(),
        )

    def implied_volatility(
        self,
        spot: float,
        strike: float,
        expiry: date,
        market_price: float,
        option_type: Literal["call", "put"] = "call",
    ) -> float:
        """计算隐含波动率"""

        val_date = date.today()
        ql.Settings.instance().evaluationDate = ql.Date(val_date.day, val_date.month, val_date.year)

        maturity = ql.Date(expiry.day, expiry.month, expiry.year)
        opt_type = ql.Option.Call if option_type == "call" else ql.Option.Put
        payoff = ql.PlainVanillaPayoff(opt_type, strike)
        exercise = ql.EuropeanExercise(maturity)
        option = ql.VanillaOption(payoff, exercise)

        spot_handle = ql.QuoteHandle(ql.SimpleQuote(spot))
        rate_handle = ql.YieldTermStructureHandle(
            ql.FlatForward(ql.Settings.instance().evaluationDate, self.risk_free_rate, ql.Actual365Fixed())
        )
        div_handle = ql.YieldTermStructureHandle(
            ql.FlatForward(ql.Settings.instance().evaluationDate, self.dividend_yield, ql.Actual365Fixed())
        )

        process = ql.BlackScholesMertonProcess(
            spot_handle, div_handle, rate_handle,
            ql.BlackVolTermStructureHandle(ql.BlackConstantVol(
                ql.Settings.instance().evaluationDate, ql.NullCalendar(), 0.2, ql.Actual365Fixed()
            ))
        )

        return option.impliedVolatility(market_price, process)


class YieldCurveBuilder:
    """收益率曲线构建器"""

    @staticmethod
    def build_from_rates(
        tenors: list[str],  # ["1M", "3M", "6M", "1Y", "2Y", "5Y", "10Y"]
        rates: list[float],  # 对应利率
        valuation_date: date | None = None
    ):
        """从利率数据构建收益率曲线"""

        val_date = valuation_date or date.today()
        ql.Settings.instance().evaluationDate = ql.Date(val_date.day, val_date.month, val_date.year)

        helpers = []
        for tenor, rate in zip(tenors, rates):
            period = ql.Period(tenor)
            helper = ql.DepositRateHelper(
                ql.QuoteHandle(ql.SimpleQuote(rate)),
                period, 2, ql.TARGET(), ql.ModifiedFollowing, False, ql.Actual360()
            )
            helpers.append(helper)

        curve = ql.PiecewiseLogCubicDiscount(
            ql.Settings.instance().evaluationDate, helpers, ql.Actual365Fixed()
        )
        return curve
