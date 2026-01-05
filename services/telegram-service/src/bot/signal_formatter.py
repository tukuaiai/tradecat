#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信号格式化系统
基于CoinGlass数据实现三种信号类型：
1. 狙击信号（资金费率）
2. 趋势信号（持仓量）
3. 情绪信号（RSI）
并扩展对 TradingView 三个买卖信号（UT Bot / Supertrend / AlphaTrend）的实时推送格式化
支持币安API获取资金费率数据
"""

import os
import json
import logging
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
from typing import Dict, List, Any, Optional, Tuple, Iterable

当前目录 = Path(__file__).resolve().parent
根目录 = 当前目录.parent
if str(根目录) not in sys.path:
    sys.path.append(str(根目录))

# 导入智能格式化函数（避免循环依赖，失败则降级为简单格式）
try:
    from main import smart_price_format, smart_percentage_format, smart_volume_format
except Exception:
    def smart_price_format(price: float) -> str:
        return f"{price:.4f}"

    def smart_percentage_format(value: float) -> str:
        return f"{value:.2f}%"

    def smart_volume_format(volume: float) -> str:
        return f"{volume:.0f}"

logger = logging.getLogger(__name__)

class BinanceAPIClient:
    """币安API客户端 - 专门用于获取资金费率数据"""

    def __init__(self):
        self.base_url = "https://fapi.binance.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        self._exchange_info = None
        self._symbols_cache = None

    def get_funding_rate(self, symbol: str = None) -> Optional[Dict]:
        """获取资金费率数据"""
        try:
            url = f"{self.base_url}/fapi/v1/premiumIndex"
            params = {}
            if symbol:
                params['symbol'] = symbol

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if symbol:
                # 返回单个币种数据
                return data
            else:
                # 返回所有币种数据
                return {item['symbol']: item for item in data}

        except Exception as e:
            logger.error(f"❌ 获取币安资金费率数据失败: {e}")
            return None

    def get_24hr_ticker(self, symbol: str = None) -> Optional[Dict]:
        """获取24小时价格变动数据"""
        try:
            url = f"{self.base_url}/fapi/v1/ticker/24hr"
            params = {}
            if symbol:
                params['symbol'] = symbol

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if symbol:
                return data
            else:
                return {item['symbol']: item for item in data}

        except Exception as e:
            logger.error(f"❌ 获取币安24小时数据失败: {e}")
            return None

    def get_exchange_info(self) -> Optional[Dict]:
        """获取币安交易所信息（包含所有交易对）"""
        try:
            if self._exchange_info is None:
                url = f"{self.base_url}/fapi/v1/exchangeInfo"
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                self._exchange_info = response.json()
                logger.info(f"获取到 {len(self._exchange_info.get('symbols', []))} 个交易对信息")
            return self._exchange_info
        except Exception as e:
            logger.error(f"❌ 获取币安交易所信息失败: {e}")
            return None

    def get_all_symbols(self) -> List[str]:
        """获取所有USDT交易对列表"""
        try:
            if self._symbols_cache is None:
                exchange_info = self.get_exchange_info()
                if exchange_info and 'symbols' in exchange_info:
                    # 筛选出状态为TRADING的USDT交易对
                    usdt_symbols = []
                    for symbol_info in exchange_info['symbols']:
                        symbol = symbol_info.get('symbol', '')
                        status = symbol_info.get('status', '')
                        if symbol.endswith('USDT') and status == 'TRADING':
                            usdt_symbols.append(symbol)
                    self._symbols_cache = usdt_symbols
                    logger.info(f"缓存了 {len(usdt_symbols)} 个USDT交易对")
                else:
                    self._symbols_cache = []
            return self._symbols_cache or []
        except Exception as e:
            logger.error(f"❌ 获取币安交易对列表失败: {e}")
            return []

class SignalFormatter:
    """信号格式化器"""

    def __init__(self, coinglass_data_dir: str = None):
        """初始化信号格式化器"""
        self.coinglass_data_dir = coinglass_data_dir or os.path.join(os.path.dirname(__file__), "data", "coinglass")
        self.futures_data = []
        self.spot_data = []
        self.last_update_time = None

        # 初始化币安API客户端
        self.binance_client = BinanceAPIClient()

        self.load_data()

    def load_data(self):
        """加载最新的CoinGlass数据"""
        try:
            if not os.path.exists(self.coinglass_data_dir):
                logger.warning(f"CoinGlass数据目录不存在: {self.coinglass_data_dir}")
                return

            # 获取最新的数据目录
            cache_dirs = []
            for item in os.listdir(self.coinglass_data_dir):
                item_path = os.path.join(self.coinglass_data_dir, item)
                if os.path.isdir(item_path):
                    cache_dirs.append(item)

            if not cache_dirs:
                logger.warning("没有找到CoinGlass缓存目录")
                return

            # 按时间排序，获取最新的
            cache_dirs.sort(reverse=True)
            latest_cache_dir = os.path.join(self.coinglass_data_dir, cache_dirs[0])

            # 读取futures数据
            futures_file = os.path.join(latest_cache_dir, "futures.json")
            if os.path.exists(futures_file):
                with open(futures_file, 'r', encoding='utf-8') as f:
                    self.futures_data = json.load(f)
                logger.info(f"成功加载 {len(self.futures_data)} 个合约数据")

            # 读取spot数据
            spot_file = os.path.join(latest_cache_dir, "spot.json")
            if os.path.exists(spot_file):
                with open(spot_file, 'r', encoding='utf-8') as f:
                    self.spot_data = json.load(f)
                logger.info(f"成功加载 {len(self.spot_data)} 个现货数据")

            self.last_update_time = datetime.now()

        except Exception as e:
            logger.error(f"加载CoinGlass数据失败: {e}")

    def get_coin_data(self, symbol: str) -> Tuple[Optional[Dict], Optional[Dict]]:
        """获取指定币种的合约和现货数据"""
        futures_coin = None
        spot_coin = None

        # 查找合约数据
        for coin in self.futures_data:
            if coin.get('symbol', '').upper() == symbol.upper():
                futures_coin = coin
                break

        # 查找现货数据
        for coin in self.spot_data:
            if coin.get('symbol', '').upper() == symbol.upper():
                spot_coin = coin
                break

        return futures_coin, spot_coin

    def get_binance_data(self, symbol: str) -> Dict[str, Any]:
        """获取币安API数据（资金费率和价格数据）"""
        binance_data = {
            'funding_rate': 0.0,
            'mark_price': 0.0,
            'price_24h_change': 0.0,
            'volume_24h': 0.0,
            'next_funding_time': 0
        }

        try:
            # 转换币种符号：CoinGlass格式转币安格式
            binance_symbol = self.convert_to_binance_symbol(symbol)

            # 获取资金费率数据
            funding_data = self.binance_client.get_funding_rate(binance_symbol)
            if funding_data:
                binance_data['funding_rate'] = float(funding_data.get('lastFundingRate', 0))
                binance_data['mark_price'] = float(funding_data.get('markPrice', 0))
                binance_data['next_funding_time'] = funding_data.get('nextFundingTime', 0)

            # 获取24小时价格数据
            ticker_data = self.binance_client.get_24hr_ticker(binance_symbol)
            if ticker_data:
                binance_data['price_24h_change'] = float(ticker_data.get('priceChangePercent', 0))
                binance_data['volume_24h'] = float(ticker_data.get('quoteVolume', 0))
                # 如果mark_price为0，使用最新价格
                if binance_data['mark_price'] == 0:
                    binance_data['mark_price'] = float(ticker_data.get('lastPrice', 0))

        except Exception as e:
            logger.error(f"❌ 获取币安数据失败 {symbol}: {e}")

        return binance_data

    def convert_to_binance_symbol(self, coinglass_symbol: str) -> str:
        """将CoinGlass符号转换为币安符号 - 智能匹配"""
        # 移除可能的斜杠和空格
        symbol = coinglass_symbol.replace('/', '').replace(' ', '').upper()

        # 如果已经是USDT结尾，直接返回
        if symbol.endswith('USDT'):
            return symbol

        # 获取所有币安交易对
        all_symbols = self.binance_client.get_all_symbols()

        # 常见的特殊映射（处理一些特殊情况）
        special_mappings = {
            '1000PEPE': '1000PEPEUSDT',
            '1000SHIB': '1000SHIBUSDT',
            '1000FLOKI': '1000FLOKIUSDT',
            '1000BONK': '1000BONKUSDT',
            '1000RATS': '1000RATSUSDT',
            '1000SATS': '1000SATSUSDT',
            'BTCDOM': 'BTCDOMUSDT',
            'ETHDOM': 'ETHDOMUSDT'
        }

        # 检查特殊映射
        if symbol in special_mappings:
            target_symbol = special_mappings[symbol]
            if target_symbol in all_symbols:
                return target_symbol

        # 智能匹配算法
        possible_symbols = [
            f"{symbol}USDT",  # 直接添加USDT
            f"1000{symbol}USDT",  # 某些meme币需要1000前缀
        ]

        # 检查可能的符号是否存在于币安
        for possible_symbol in possible_symbols:
            if possible_symbol in all_symbols:
                logger.info(f"匹配成功: {coinglass_symbol} -> {possible_symbol}")
                return possible_symbol

        # 如果都找不到，尝试模糊匹配
        for binance_symbol in all_symbols:
            # 移除USDT后缀进行比较
            base_symbol = binance_symbol.replace('USDT', '')
            if base_symbol == symbol:
                logger.info(f"模糊匹配成功: {coinglass_symbol} -> {binance_symbol}")
                return binance_symbol
            # 检查是否包含目标符号
            if symbol in base_symbol or base_symbol in symbol:
                logger.info(f"部分匹配成功: {coinglass_symbol} -> {binance_symbol}")
                return binance_symbol

        # 如果完全找不到，返回默认格式
        default_symbol = f"{symbol}USDT"
        logger.warning(f"未找到匹配的币安交易对，使用默认格式: {coinglass_symbol} -> {default_symbol}")
        return default_symbol

    def _format_amount_with_unit(self, amount: float) -> str:
        """智能格式化金额显示，小金额使用K，大金额使用M，保留两位小数"""
        if abs(amount) >= 1000:  # 大于等于1000M，使用B单位
            return f"{amount/1000:.2f}B" if amount >= 0 else f"{amount/1000:.2f}B"
        elif abs(amount) >= 1:  # 大于等于1M，使用M单位
            return f"{amount:.2f}M" if amount >= 0 else f"{amount:.2f}M"
        elif abs(amount) >= 0.001:  # 大于等于0.001M（即1K），使用K单位
            return f"{amount*1000:.2f}K" if amount >= 0 else f"{amount*1000:.2f}K"
        else:  # 小于1K，直接显示原始金额
            return f"{amount*1000000:.2f}" if amount >= 0 else f"{amount*1000000:.2f}"

    def calculate_derived_indicators(self, futures_data: Dict, spot_data: Dict = None, binance_data: Dict = None) -> Dict:
        """计算衍生指标"""
        indicators = {}

        try:
            # 基础数据 - 优先使用币安数据
            if binance_data:
                price = binance_data.get('mark_price', 0)
                funding_rate = binance_data.get('funding_rate', 0)
                price_change_24h = binance_data.get('price_24h_change', 0)
                volume_24h = binance_data.get('volume_24h', 0)
            else:
                price = futures_data.get('current_price', 0)
                funding_rate = futures_data.get('avg_funding_rate_by_oi', 0)
                price_change_24h = futures_data.get('price_change_percent_24h', 0)
                volume_24h = futures_data.get('volume_change_usd_24h', 0)

            oi_usd = futures_data.get('open_interest_usd', 0)
            oi_24h_change = futures_data.get('open_interest_change_percent_24h', 0)

            # 多空比例数据
            ls_ratio_1h = futures_data.get('long_short_ratio_1h', 1)
            ls_ratio_4h = futures_data.get('long_short_ratio_4h', 1)
            ls_ratio_24h = futures_data.get('long_short_ratio_24h', 1)

            # 爆仓数据
            liq_24h = futures_data.get('liquidation_usd_24h', 0)
            long_liq_24h = futures_data.get('long_liquidation_usd_24h', 0)
            short_liq_24h = futures_data.get('short_liquidation_usd_24h', 0)

            # 计算恐贪指数 (0-100)
            fear_greed = 50
            if funding_rate > 0.01:
                fear_greed += 30
            elif funding_rate < -0.01:
                fear_greed -= 30

            if oi_24h_change > 5:
                fear_greed += 10
            elif oi_24h_change < -5:
                fear_greed -= 10

            fear_greed = max(0, min(100, fear_greed))

            # 计算市场活跃度
            market_activity = min(100, abs(volume_24h) / 1000000) if volume_24h > 0 else 50

            # 计算综合风险评分
            risk_score = 50
            if abs(funding_rate) > 0.01:
                risk_score += 20
            if abs(oi_24h_change) > 10:
                risk_score += 15
            if liq_24h > 10000000:  # 1000万以上爆仓
                risk_score += 15
            risk_score = max(0, min(100, risk_score))

            # 计算波动率
            price_changes = [
                futures_data.get('price_change_percent_1h', 0),
                futures_data.get('price_change_percent_4h', 0),
                price_change_24h
            ]
            volatility = sum(abs(x) for x in price_changes) / len(price_changes)

            # 计算动量趋势
            momentum = price_change_24h

            # 计算持仓效率
            oi_vol_ratio = futures_data.get('open_interest_volume_ratio', 0)
            position_efficiency = min(100, oi_vol_ratio * 100)

            # 计算主力倾向
            if ls_ratio_24h > 1.2:
                main_tendency = "多头主导"
            elif ls_ratio_24h < 0.8:
                main_tendency = "空头主导"
            else:
                main_tendency = "均衡"

            # 计算净流入（使用CoinGlass合约数据的多周期资金流向）
            # 优先使用实际的多空成交量数据
            long_vol_1h = futures_data.get('long_volume_usd_1h', 0)
            short_vol_1h = futures_data.get('short_volume_usd_1h', 0)
            long_vol_4h = futures_data.get('long_volume_usd_4h', 0)
            short_vol_4h = futures_data.get('short_volume_usd_4h', 0)
            long_vol_24h = futures_data.get('long_volume_usd_24h', 0)
            short_vol_24h = futures_data.get('short_volume_usd_24h', 0)

            # 方法1: 基于多空成交量差计算净流入 (主要方法)
            if long_vol_1h > 0 or short_vol_1h > 0:
                net_inflow_1h = (long_vol_1h - short_vol_1h) / 1000000  # 转换为百万
            else:
                net_inflow_1h = 0

            if long_vol_4h > 0 or short_vol_4h > 0:
                net_inflow_4h = (long_vol_4h - short_vol_4h) / 1000000  # 转换为百万
            else:
                net_inflow_4h = 0

            if long_vol_24h > 0 or short_vol_24h > 0:
                net_inflow_24h = (long_vol_24h - short_vol_24h) / 1000000  # 转换为百万
            else:
                net_inflow_24h = 0

            # 方法2: 如果没有多空成交量数据，使用持仓量变化结合价格变化估算
            if abs(net_inflow_1h) < 0.1 and abs(net_inflow_4h) < 0.1 and abs(net_inflow_24h) < 0.1:
                oi_change_1h = futures_data.get('open_interest_change_usd_1h', 0)
                oi_change_4h = futures_data.get('open_interest_change_usd_4h', 0)
                oi_change_24h = futures_data.get('open_interest_change_usd_24h', 0)

                if oi_change_1h != 0:
                    # 持仓量增加且价格上涨 = 资金流入，持仓量增加且价格下跌 = 资金流出
                    price_change_1h = futures_data.get('price_change_percent_1h', 0)
                    direction_factor = 1 if price_change_1h > 0 else -1
                    net_inflow_1h = abs(oi_change_1h) * direction_factor / 1000000

                if oi_change_4h != 0:
                    price_change_4h = futures_data.get('price_change_percent_4h', 0)
                    direction_factor = 1 if price_change_4h > 0 else -1
                    net_inflow_4h = abs(oi_change_4h) * direction_factor / 1000000

                if oi_change_24h != 0:
                    price_change_24h_val = futures_data.get('price_change_percent_24h', 0)
                    direction_factor = 1 if price_change_24h_val > 0 else -1
                    net_inflow_24h = abs(oi_change_24h) * direction_factor / 1000000

                # 方法3: 最后降级方案 - 使用资金费率和持仓量估算
                if abs(net_inflow_1h) < 0.1:
                    net_inflow_1h = funding_rate * oi_usd / 8 / 1000000
                if abs(net_inflow_4h) < 0.1:
                    net_inflow_4h = funding_rate * oi_usd / 2 / 1000000
                if abs(net_inflow_24h) < 0.1:
                    net_inflow_24h = funding_rate * oi_usd * 3 / 1000000

            # 重新计算资金流向强度和趋势 - 基于实际净流入数据
            net_flow_abs_24h = abs(net_inflow_24h)

            # 计算资金流向强度 (基于24小时净流入绝对值)
            if net_flow_abs_24h > 100:  # 大于亿1美元
                capital_intensity = "强"
            elif net_flow_abs_24h > 10:  # 大于1000万美元
                capital_intensity = "中"
            else:
                capital_intensity = "弱"

            # 计算资金流向趋势 (基于24小时净流入方向和规模)
            if net_inflow_24h > 100:
                capital_trend = "大幅流入"
                capital_flow = "大量流入"
            elif net_inflow_24h > 10:
                capital_trend = "稳定流入"
                capital_flow = "流入"
            elif net_inflow_24h < -100:
                capital_trend = "大幅流出"
                capital_flow = "大量流出"
            elif net_inflow_24h < -10:
                capital_trend = "稳定流出"
                capital_flow = "流出"
            else:
                capital_trend = "平衡"
                capital_flow = "平衡"

            # 计算买卖力量 - 使用实际成交量数据
            total_vol = long_vol_24h + short_vol_24h

            if total_vol > 0:
                buy_power = (long_vol_24h / total_vol) * 100
                sell_power = (short_vol_24h / total_vol) * 100
            else:
                buy_power = 50
                sell_power = 50

            # 基差溢价计算
            if spot_data:
                spot_price = spot_data.get('current_price', price)
                basis_premium = ((price - spot_price) / spot_price) * 100 if spot_price > 0 else 0
            else:
                basis_premium = 0

            indicators = {
                'fear_greed_index': round(fear_greed, 1),
                'market_activity': round(market_activity, 1),
                'risk_score': round(risk_score, 1),
                'volatility': round(volatility, 2),
                'momentum': round(momentum, 2),
                'position_efficiency': round(position_efficiency, 1),
                'main_tendency': main_tendency,
                'capital_flow': capital_flow,
                'capital_intensity': capital_intensity,
                'capital_trend': capital_trend,
                'net_inflow_1h': round(net_inflow_1h, 2),
                'net_inflow_4h': round(net_inflow_4h, 2),
                'net_inflow_24h': round(net_inflow_24h, 1),
                'buy_power': round(buy_power, 1),
                'sell_power': round(sell_power, 1),
                'basis_premium': round(basis_premium, 3),
                'funding_rate_8h': round(funding_rate * 3, 4),  # 8小时费率
                'oi_change_5h': round(futures_data.get('open_interest_change_percent_4h', 0), 2),
                'ls_ratio_avg': round((ls_ratio_1h + ls_ratio_4h + ls_ratio_24h) / 3, 3),
                'liq_ratio': round((long_liq_24h / (long_liq_24h + short_liq_24h)) * 100, 1) if (long_liq_24h + short_liq_24h) > 0 else 50
            }

        except Exception as e:
            logger.error(f"计算衍生指标失败: {e}")
            # 返回默认值
            indicators = {
                'fear_greed_index': 50.0,
                'market_activity': 50.0,
                'risk_score': 50.0,
                'volatility': 2.0,
                'momentum': 0.0,
                'position_efficiency': 50.0,
                'main_tendency': "均衡",
                'capital_flow': "平衡",
                'capital_intensity': "弱",
                'capital_trend': "平衡",
                'net_inflow_1h': 0.0,
                'net_inflow_4h': 0.0,
                'net_inflow_24h': 0.0,
                'buy_power': 50.0,
                'sell_power': 50.0,
                'basis_premium': 0.0,
                'funding_rate_8h': 0.0,
                'oi_change_5h': 0.0,
                'ls_ratio_avg': 1.0,
                'liq_ratio': 50.0
            }

        return indicators

    def format_funding_rate_signal(self, symbol: str, alert_value: float) -> str:
        """格式化资金费率信号（狙击信号）"""
        futures_data, spot_data = self.get_coin_data(symbol)

        if not futures_data:
            # 静默处理，不向用户显示错误消息
            logger.warning(f"📊 未找到 {symbol} 的数据，跳过信号生成")
            return None  # 返回None而不是错误消息

        # 检查1H爆仓金额条件：必须大于等于5000
        liquidation_1h = futures_data.get('liquidation_usd_1h', 0)
        if liquidation_1h < 5000:
            logger.debug(f"📊 {symbol} 1H爆仓金额 ${liquidation_1h:,.0f} 低于5000门槛，跳过信号生成")
            return None

        # 获取币安数据
        binance_data = self.get_binance_data(symbol)

        # 计算衍生指标
        indicators = self.calculate_derived_indicators(futures_data, spot_data, binance_data)

        # 获取当前时间 - 修改为精确到分钟
        current_time = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")

        # 使用币安数据或CoinGlass数据 - 将24h改为4h
        current_price = binance_data.get('mark_price', 0) or futures_data.get('current_price', 0)
        price_change_4h = binance_data.get('price_4h_change', 0) or futures_data.get('price_change_percent_4h', 0)
        market_cap = futures_data.get('market_cap_usd', 0)
        volume_4h = binance_data.get('volume_4h', 0) or futures_data.get('volume_change_usd_4h', 0)
        funding_rate = binance_data.get('funding_rate', 0) or futures_data.get('avg_funding_rate_by_oi', 0)
        funding_rate_percent = funding_rate * 100  # 转换为百分比

        # 获取今日播报次数并更新计数
        try:
            from main import daily_signal_counter
            # 增加计数并获取新的计数值
            daily_count = daily_signal_counter.increment_count(symbol)
        except Exception:
            daily_count = 1

        # 构建信号消息 - 严格按照用户示例格式
        message = f"""🎯 {symbol} / USDT 狙击信号 (今日第{daily_count}次)

⏰ 时间: {current_time}
🏷 价格: ${current_price:.4f}
📊 4H涨跌: {price_change_4h:.2f}%
🔥 4H交易额: ${self._format_amount_with_unit(volume_4h/1000000)}
💎 市值: ${self._format_amount_with_unit(market_cap/1000000)}
💰 资金费率: {funding_rate_percent:.6f}%

💥 爆仓详情
├ 4H总爆仓: ${futures_data.get('liquidation_usd_4h', 0):,.0f}
└ 多头: ${futures_data.get('long_liquidation_usd_4h', 0):,.0f} / 空头: ${futures_data.get('short_liquidation_usd_4h', 0):,.0f}

💵 资金流向
├ 方向 / 强度: {indicators['capital_flow']} / {indicators['capital_intensity']}
├ 1H / 4H净流入: {'+' if indicators['net_inflow_1h'] >= 0 else ''}${indicators['net_inflow_1h']:.2f}M / {'+' if indicators['net_inflow_4h'] >= 0 else ''}${indicators['net_inflow_4h']:.2f}M
├ 主力 / 多空均衡: {indicators['main_tendency']} / {indicators['ls_ratio_avg']:.3f}
└ 买卖力量: 多{indicators['buy_power']:.1f}% / 空{indicators['sell_power']:.1f}%

📊 AI分析
├ 短期波动 / 动量: {indicators['volatility']:.2f}% / {indicators['momentum']:.2f}%
├ 波动 / 趋势强度: {'高' if indicators['volatility'] > 3 else '中' if indicators['volatility'] > 1 else '低'} / {'强' if abs(indicators['momentum']) > 2 else '弱'}
├ 持仓成交比 / 效率: {futures_data.get('open_interest_volume_ratio', 0):.3f} / {indicators['position_efficiency']:.1f}%
├ 资金利用 / 参与度: {'高' if indicators['position_efficiency'] > 70 else '中' if indicators['position_efficiency'] > 30 else '低'} / {'活跃' if indicators['position_efficiency'] > 50 else '一般'}
├ 指数 / 情绪: {indicators['fear_greed_index']:.1f} / {'极度贪婪' if indicators['fear_greed_index'] > 80 else '贪婪' if indicators['fear_greed_index'] > 60 else '中性' if indicators['fear_greed_index'] > 40 else '恐惧' if indicators['fear_greed_index'] > 20 else '极度恐惧'}
└ 活跃度 / 风险分: {indicators['market_activity']:.1f}% / {indicators['risk_score']:.1f}%

⚠️ 风险提示: 合约交易风险高，请谨慎操作。"""

        return message

    def format_open_interest_signal(self, symbol: str, alert_value: float) -> str:
        """格式化持仓量信号（趋势信号）"""
        futures_data, spot_data = self.get_coin_data(symbol)

        if not futures_data:
            # 静默处理，不向用户显示错误消息
            logger.warning(f"📊 未找到 {symbol} 的数据，跳过信号生成")
            return None  # 返回None而不是错误消息

        # 检查1H爆仓金额条件：必须大于等于5000
        liquidation_1h = futures_data.get('liquidation_usd_1h', 0)
        if liquidation_1h < 5000:
            logger.debug(f"📊 {symbol} 1H爆仓金额 ${liquidation_1h:,.0f} 低于5000门槛，跳过信号生成")
            return None

        # 获取币安数据
        binance_data = self.get_binance_data(symbol)

        # 计算衍生指标
        indicators = self.calculate_derived_indicators(futures_data, spot_data, binance_data)

        # 获取当前时间 - 修改为精确到分钟
        current_time = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")

        # 使用币安数据或CoinGlass数据 - 将24h改为4h
        current_price = binance_data.get('mark_price', 0) or futures_data.get('current_price', 0)
        price_change_4h = binance_data.get('price_4h_change', 0) or futures_data.get('price_change_percent_4h', 0)
        market_cap = futures_data.get('market_cap_usd', 0)
        volume_4h = binance_data.get('volume_4h', 0) or futures_data.get('volume_change_usd_4h', 0)
        funding_rate = binance_data.get('funding_rate', 0) or futures_data.get('avg_funding_rate_by_oi', 0)
        funding_rate_percent = funding_rate * 100  # 转换为百分比

        # 获取今日播报次数并更新计数
        try:
            from main import daily_signal_counter
            # 增加计数并获取新的计数值
            daily_count = daily_signal_counter.increment_count(symbol)
        except Exception:
            daily_count = 1

        # 构建信号消息 - 严格按照用户示例格式
        message = f"""🎯 {symbol} / USDT 趋势信号 (今日第{daily_count}次)

⏰ 时间: {current_time}
🏷 价格: ${current_price:.4f}
📊 4H涨跌: {price_change_4h:.2f}%
🔥 4H交易额: ${self._format_amount_with_unit(volume_4h/1000000)}
💎 市值: ${self._format_amount_with_unit(market_cap/1000000)}
💰 资金费率: {funding_rate_percent:.6f}%

💥 爆仓详情
├ 4H总爆仓: ${futures_data.get('liquidation_usd_4h', 0):,.0f}
└ 多头: ${futures_data.get('long_liquidation_usd_4h', 0):,.0f} / 空头: ${futures_data.get('short_liquidation_usd_4h', 0):,.0f}

💵 资金流向
├ 方向 / 强度: {indicators['capital_flow']} / {indicators['capital_intensity']}
├ 1H / 4H净流入: {'+' if indicators['net_inflow_1h'] >= 0 else ''}${indicators['net_inflow_1h']:.2f}M / {'+' if indicators['net_inflow_4h'] >= 0 else ''}${indicators['net_inflow_4h']:.2f}M
├ 主力 / 多空均衡: {indicators['main_tendency']} / {indicators['ls_ratio_avg']:.3f}
└ 买卖力量: 多{indicators['buy_power']:.1f}% / 空{indicators['sell_power']:.1f}%

📊 AI分析
├ 短期波动 / 动量: {indicators['volatility']:.2f}% / {indicators['momentum']:.2f}%
├ 波动 / 趋势强度: {'高' if indicators['volatility'] > 3 else '中' if indicators['volatility'] > 1 else '低'} / {'强' if abs(indicators['momentum']) > 2 else '弱'}
├ 持仓成交比 / 效率: {futures_data.get('open_interest_volume_ratio', 0):.3f} / {indicators['position_efficiency']:.1f}%
├ 资金利用 / 参与度: {'高' if indicators['position_efficiency'] > 70 else '中' if indicators['position_efficiency'] > 30 else '低'} / {'活跃' if indicators['position_efficiency'] > 50 else '一般'}
├ 指数 / 情绪: {indicators['fear_greed_index']:.1f} / {'极度贪婪' if indicators['fear_greed_index'] > 80 else '贪婪' if indicators['fear_greed_index'] > 60 else '中性' if indicators['fear_greed_index'] > 40 else '恐惧' if indicators['fear_greed_index'] > 20 else '极度恐惧'}
└ 活跃度 / 风险分: {indicators['market_activity']:.1f}% / {indicators['risk_score']:.1f}%

⚠️ 风险提示: 合约交易风险高，请谨慎操作。"""

        return message

    def format_rsi_signal(self, symbol: str, alert_value: float) -> str:
        """格式化RSI信号（情绪信号）"""
        futures_data, spot_data = self.get_coin_data(symbol)

        if not futures_data:
            # 静默处理，不向用户显示错误消息
            logger.warning(f"📊 未找到 {symbol} 的数据，跳过信号生成")
            return None  # 返回None而不是错误消息

        # 检查1H爆仓金额条件：必须大于等于5000
        liquidation_1h = futures_data.get('liquidation_usd_1h', 0)
        if liquidation_1h < 5000:
            logger.debug(f"📊 {symbol} 1H爆仓金额 ${liquidation_1h:,.0f} 低于5000门槛，跳过信号生成")
            return None

        # 获取币安数据
        binance_data = self.get_binance_data(symbol)

        # 计算衍生指标
        indicators = self.calculate_derived_indicators(futures_data, spot_data, binance_data)

        # 获取当前时间 - 修改为精确到分钟
        current_time = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")

        # 使用币安数据或CoinGlass数据 - 将24h改为4h
        current_price = binance_data.get('mark_price', 0) or futures_data.get('current_price', 0)
        price_change_4h = binance_data.get('price_4h_change', 0) or futures_data.get('price_change_percent_4h', 0)
        market_cap = futures_data.get('market_cap_usd', 0)
        volume_4h = binance_data.get('volume_4h', 0) or futures_data.get('volume_change_usd_4h', 0)
        funding_rate = binance_data.get('funding_rate', 0) or futures_data.get('avg_funding_rate_by_oi', 0)
        funding_rate_percent = funding_rate * 100  # 转换为百分比

        # 获取今日播报次数并更新计数
        try:
            from main import daily_signal_counter
            # 增加计数并获取新的计数值
            daily_count = daily_signal_counter.increment_count(symbol)
        except Exception:
            daily_count = 1

        # 构建信号消息 - 严格按照用户示例格式
        message = f"""🎯 {symbol} / USDT 情绪信号 (今日第{daily_count}次)

⏰ 时间: {current_time}
🏷 价格: ${current_price:.4f}
📊 4H涨跌: {price_change_4h:.2f}%
🔥 4H交易额: ${self._format_amount_with_unit(volume_4h/1000000)}
💎 市值: ${self._format_amount_with_unit(market_cap/1000000)}
💰 资金费率: {funding_rate_percent:.6f}%

💥 爆仓详情
├ 4H总爆仓: ${futures_data.get('liquidation_usd_4h', 0):,.0f}
└ 多头: ${futures_data.get('long_liquidation_usd_4h', 0):,.0f} / 空头: ${futures_data.get('short_liquidation_usd_4h', 0):,.0f}

💵 资金流向
├ 方向 / 强度: {indicators['capital_flow']} / {indicators['capital_intensity']}
├ 1H / 4H净流入: {'+' if indicators['net_inflow_1h'] >= 0 else ''}${indicators['net_inflow_1h']:.2f}M / {'+' if indicators['net_inflow_4h'] >= 0 else ''}${indicators['net_inflow_4h']:.2f}M
├ 主力 / 多空均衡: {indicators['main_tendency']} / {indicators['ls_ratio_avg']:.3f}
└ 买卖力量: 多{indicators['buy_power']:.1f}% / 空{indicators['sell_power']:.1f}%

📊 AI分析
├ 短期波动 / 动量: {indicators['volatility']:.2f}% / {indicators['momentum']:.2f}%
├ 波动 / 趋势强度: {'高' if indicators['volatility'] > 3 else '中' if indicators['volatility'] > 1 else '低'} / {'强' if abs(indicators['momentum']) > 2 else '弱'}
├ 持仓成交比 / 效率: {futures_data.get('open_interest_volume_ratio', 0):.3f} / {indicators['position_efficiency']:.1f}%
├ 资金利用 / 参与度: {'高' if indicators['position_efficiency'] > 70 else '中' if indicators['position_efficiency'] > 30 else '低'} / {'活跃' if indicators['position_efficiency'] > 50 else '一般'}
├ 指数 / 情绪: {indicators['fear_greed_index']:.1f} / {'极度贪婪' if indicators['fear_greed_index'] > 80 else '贪婪' if indicators['fear_greed_index'] > 60 else '中性' if indicators['fear_greed_index'] > 40 else '恐惧' if indicators['fear_greed_index'] > 20 else '极度恐惧'}
└ 活跃度 / 风险分: {indicators['market_activity']:.1f}% / {indicators['risk_score']:.1f}%

⚠️ 风险提示: 合约交易风险高，请谨慎操作。"""

        return message

    def format_signal(self, signal_type: str, symbol: str, alert_value: float) -> str:
        """格式化信号消息"""
        if signal_type == "funding_rate":
            result = self.format_funding_rate_signal(symbol, alert_value)
        elif signal_type == "open_interest":
            result = self.format_open_interest_signal(symbol, alert_value)
        elif signal_type == "rsi":
            result = self.format_rsi_signal(symbol, alert_value)
        elif signal_type in {"realtime_ut", "realtime_supertrend", "realtime_alphatrend"}:
            # 兼容旧接口：alert_value 仅占位；真实信号应通过 format_realtime_trade_signal 传入完整字典
            logger.warning("实时买卖信号需要传入完整字典，当前仅返回占位文本")
            result = "⚡ 实时买卖信号：请传入包含币种/周期/最新价格/动作/强度/时间/信号/触发原因的字典"
        else:
            return f"❌ 未知的信号类型: {signal_type}"

        # 如果结果为None，表示数据不可用，返回None而不是错误消息
        return result

    # --- TradingView 实时买卖信号扩展 ---------------------------------
    @staticmethod
    def _校验实时信号字段(signal: Dict[str, Any]) -> Optional[str]:
        必需字段 = ["币种", "周期", "最新价格", "动作", "强度", "时间", "信号", "触发原因"]
        缺失 = [f for f in 必需字段 if f not in signal]
        return None if not 缺失 else "缺少字段: " + ", ".join(缺失)

    def format_realtime_trade_signal(self, signal: Dict[str, Any]) -> Optional[str]:
        """
        将 TradingView 系列实时买卖信号（UT Bot / Supertrend / AlphaTrend 等）格式化为 Telegram 文本
        期望字段（中文）：币种, 周期, 最新价格, 动作(买入/卖出), 强度, 时间(ISO 或已格式化), 信号, 触发原因
        返回 None 表示字段不足，调用方可选择跳过
        """
        校验 = self._校验实时信号字段(signal)
        if 校验:
            logger.warning("实时买卖信号字段不完整: %s", 校验)
            return None

        # 处理时间格式，统一为北京时间显示
        try:
            原始时间 = signal.get("时间")
            if isinstance(原始时间, datetime):
                北京时间值 = 原始时间.astimezone(timezone(timedelta(hours=8)))
            else:
                北京时间值 = datetime.fromisoformat(str(原始时间)).astimezone(timezone(timedelta(hours=8)))
            时间文本 = 北京时间值.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            时间文本 = str(signal.get("时间"))

        币种 = signal["币种"]
        周期 = signal["周期"]
        价格 = signal.get("最新价格", 0)
        动作 = signal.get("动作", "")
        强度 = signal.get("强度", 0)
        名称 = signal.get("信号", "实时信号")
        原因 = signal.get("触发原因", "")

        消息 = f"""⚡ {名称} 实时信号

⏰ 时间：{时间文本}
🎯 标的：{币种} / {周期}
💰 最新价：{价格:.6f}
🔔 动作：{动作}    强度：{强度:.4f}
🧭 触发：{原因}

提示：信号基于收盘数据计算，合约交易需自负盈亏。"""

        return 消息

    def format_realtime_trade_signals(self, signals: Iterable[Dict[str, Any]]) -> List[str]:
        """批量格式化实时买卖信号，过滤字段不完整的记录"""
        结果: List[str] = []
        for sig in signals:
            文本 = self.format_realtime_trade_signal(sig)
            if 文本:
                结果.append(文本)
        return 结果

    def get_available_symbols(self) -> List[str]:
        """获取可用的币种列表"""
        symbols = set()

        # 从合约数据中获取
        for coin in self.futures_data:
            if coin.get('symbol'):
                symbols.add(coin['symbol'])

        # 从现货数据中获取
        for coin in self.spot_data:
            if coin.get('symbol'):
                symbols.add(coin['symbol'])

        return sorted(list(symbols))

    def refresh_data(self):
        """刷新数据"""
        self.load_data()
