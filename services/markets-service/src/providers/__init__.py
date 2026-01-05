"""Providers 模块 - 数据源适配器"""
# 导入时自动注册到 ProviderRegistry

# 加密货币
# A股/国内
# 美股/全球
# 宏观经济
# 衍生品定价
# 综合聚合 (降级备份)
from . import akshare, baostock, ccxt, cryptofeed, fredapi, openbb, quantlib, yfinance

__all__ = [
    "ccxt", "cryptofeed",
    "akshare", "baostock",
    "yfinance",
    "fredapi",
    "quantlib",
    "openbb",
]
