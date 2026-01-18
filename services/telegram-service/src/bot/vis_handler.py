"""
可视化面板处理器 - 集成 vis-service 到 Telegram Bot

UI 流程：
1. 主菜单 → 📈可视化 → 选择图表类型
2. 单币图表：选择图表类型 → 选择币种 → 选择周期 → 渲染
3. 全市场图表：选择图表类型 → 选择周期 → 渲染
"""

import io
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# 添加 vis-service 路径
VIS_SERVICE_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "services-preview" / "vis-service" / "src"
if str(VIS_SERVICE_PATH) not in sys.path:
    sys.path.insert(0, str(VIS_SERVICE_PATH))

logger = logging.getLogger(__name__)

# 延迟导入 app 模块的 i18n 工具，避免循环导入
_app_module = None


def _get_app():
    """延迟获取 app 模块"""
    global _app_module
    if _app_module is None:
        from bot import app as _app
        _app_module = _app
    return _app_module


def _resolve_lang(update) -> str:
    """解析用户语言 - 委托给 app 模块"""
    try:
        app = _get_app()
        return app._resolve_lang(update)
    except Exception:
        return "zh_CN"


def _t(update, key: str, fallback: str = "", **kwargs) -> str:
    """获取翻译文本 - 使用 app 模块的 I18N 实例"""
    try:
        app = _get_app()
        lang = _resolve_lang(update)
        text = app.I18N.gettext(key, lang=lang, **kwargs)
        if text and text != key:
            return text
    except Exception:
        pass
    return fallback or key


def _btn(update, key: str, callback: str, active: bool = False, prefix: str = "✅") -> InlineKeyboardButton:
    """创建翻译按钮 - 使用 app 模块的标准方法"""
    try:
        app = _get_app()
        return app._btn(update, key, callback, active, prefix)
    except Exception:
        text = key
        if active:
            text = f"{prefix}{text}"
        return InlineKeyboardButton(text, callback_data=callback)


# ============================================================
# 模板配置：统一使用中划线格式，与 registry.py 一致
# ============================================================
VIS_TEMPLATES = {
    # 单币图表
    "vpvr-ridge": {
        "name_key": "vis.template.vpvr_ridge",
        "name_fallback": "📊 VPVR山脊图",
        "desc_key": "vis.template.vpvr_ridge_desc",
        "desc_fallback": "成交量分布随时间演变",
        "category": "single",  # 单币
        "intervals": ["5m", "15m", "1h", "4h", "1d"],
        "default_interval": "1h",
    },
    "kline-basic": {
        "name_key": "vis.template.kline",
        "name_fallback": "🕯️ K线图",
        "desc_key": "vis.template.kline_desc",
        "desc_fallback": "K线+均线+量能",
        "category": "single",
        "intervals": ["1m", "5m", "15m", "1h", "4h", "1d"],
        "default_interval": "1h",
    },
    "macd": {
        "name_key": "vis.template.macd",
        "name_fallback": "📈 MACD",
        "desc_key": "vis.template.macd_desc",
        "desc_fallback": "价格+MACD指标",
        "category": "single",
        "intervals": ["5m", "15m", "1h", "4h", "1d"],
        "default_interval": "1h",
    },
    # 全市场图表
    "vpvr-zone-strip": {
        "name_key": "vis.template.vpvr_strip",
        "name_fallback": "🎯 VPVR条带图",
        "desc_key": "vis.template.vpvr_strip_desc",
        "desc_fallback": "全市场价值区位置分布",
        "category": "market",  # 全市场
        "intervals": ["1h", "4h", "1d"],
        "default_interval": "1h",
    },
    "market-vpvr-heat": {
        "name_key": "vis.template.vpvr_heat",
        "name_fallback": "🔥 VPVR热力图",
        "desc_key": "vis.template.vpvr_heat_desc",
        "desc_fallback": "全市场成交量分布热力图",
        "category": "market",
        "intervals": ["1h", "4h", "1d"],
        "default_interval": "4h",
    },
    "vpvr-zone-grid": {
        "name_key": "vis.template.vpvr_grid",
        "name_fallback": "📋 VPVR卡片",
        "desc_key": "vis.template.vpvr_grid_desc",
        "desc_fallback": "全市场价值区卡片概览",
        "category": "market",
        "intervals": ["1h", "4h", "1d"],
        "default_interval": "4h",
    },
}

# 默认币种列表
DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT"]


# ============================================================
# 可视化处理器
# ============================================================
class VisHandler:
    """可视化面板处理器"""

    def __init__(self):
        self.user_states: Dict[int, Dict] = {}

    def _get_state(self, user_id: int) -> Dict:
        """获取用户状态"""
        if user_id not in self.user_states:
            self.user_states[user_id] = {
                "template": None,
                "symbol": "BTCUSDT",
                "interval": "1h",
                "category": "single",
            }
        return self.user_states[user_id]

    def _set_state(self, user_id: int, **kwargs):
        """设置用户状态"""
        state = self._get_state(user_id)
        state.update(kwargs)

    # ============================================================
    # 键盘构建
    # ============================================================
    def build_main_menu(self, update=None) -> InlineKeyboardMarkup:
        """可视化主菜单：按类别分组显示图表类型"""
        rows: List[List[InlineKeyboardButton]] = []

        # 单币图表分组
        rows.append([InlineKeyboardButton(
            _t(update, "vis.category.single", "📊 单币图表"),
            callback_data="vis_nop"
        )])
        single_row = []
        for tid, tpl in VIS_TEMPLATES.items():
            if tpl["category"] == "single":
                name = _t(update, tpl["name_key"], tpl["name_fallback"])
                single_row.append(InlineKeyboardButton(name, callback_data=f"vis_tpl_{tid}"))
                if len(single_row) == 3:
                    rows.append(single_row)
                    single_row = []
        if single_row:
            rows.append(single_row)

        # 全市场图表分组
        rows.append([InlineKeyboardButton(
            _t(update, "vis.category.market", "🌐 全市场图表"),
            callback_data="vis_nop"
        )])
        market_row = []
        for tid, tpl in VIS_TEMPLATES.items():
            if tpl["category"] == "market":
                name = _t(update, tpl["name_key"], tpl["name_fallback"])
                market_row.append(InlineKeyboardButton(name, callback_data=f"vis_tpl_{tid}"))
                if len(market_row) == 3:
                    rows.append(market_row)
                    market_row = []
        if market_row:
            rows.append(market_row)

        # 返回主菜单
        rows.append([_btn(update, "btn.back_home", "main_menu")])

        return InlineKeyboardMarkup(rows)

    def build_symbol_keyboard(self, template_id: str, update=None) -> InlineKeyboardMarkup:
        """构建币种选择键盘"""
        rows: List[List[InlineKeyboardButton]] = []

        # 币种按钮（每行 3 个）
        row = []
        for symbol in DEFAULT_SYMBOLS:
            display = symbol.replace("USDT", "")
            row.append(InlineKeyboardButton(display, callback_data=f"vis_sym_{template_id}_{symbol}"))
            if len(row) == 3:
                rows.append(row)
                row = []
        if row:
            rows.append(row)

        # 导航行
        rows.append([
            _btn(update, "btn.back", "vis_menu"),
            _btn(update, "btn.back_home", "main_menu"),
        ])

        return InlineKeyboardMarkup(rows)

    def build_interval_keyboard(self, template_id: str, symbol: str, update=None) -> InlineKeyboardMarkup:
        """构建周期选择键盘"""
        tpl = VIS_TEMPLATES.get(template_id, {})
        intervals = tpl.get("intervals", ["1h", "4h", "1d"])
        default_interval = tpl.get("default_interval", "1h")

        rows: List[List[InlineKeyboardButton]] = []

        # 周期按钮（每行 3 个）
        row = []
        for interval in intervals:
            label = f"✅{interval}" if interval == default_interval else interval
            cb = f"vis_itv_{template_id}_{symbol}_{interval}"
            row.append(InlineKeyboardButton(label, callback_data=cb))
            if len(row) == 3:
                rows.append(row)
                row = []
        if row:
            rows.append(row)

        # 导航行：返回币种选择或菜单
        category = tpl.get("category", "single")
        if category == "single":
            back_cb = f"vis_tpl_{template_id}"
        else:
            back_cb = "vis_menu"

        rows.append([
            _btn(update, "btn.back", back_cb),
            _btn(update, "btn.back_home", "main_menu"),
        ])

        return InlineKeyboardMarkup(rows)

    def build_result_keyboard(self, template_id: str, symbol: str, interval: str, update=None) -> InlineKeyboardMarkup:
        """构建结果页面键盘：周期快捷切换 + 刷新"""
        tpl = VIS_TEMPLATES.get(template_id, {})
        intervals = tpl.get("intervals", ["1h", "4h", "1d"])

        rows: List[List[InlineKeyboardButton]] = []

        # 周期快捷切换（最多 5 个）
        row = []
        for itv in intervals[:5]:
            label = f"✅{itv}" if itv == interval else itv
            row.append(InlineKeyboardButton(label, callback_data=f"vis_itv_{template_id}_{symbol}_{itv}"))
        if row:
            rows.append(row)

        # 控制行：刷新使用当前周期的回调
        refresh_cb = f"vis_itv_{template_id}_{symbol}_{interval}"
        rows.append([
            InlineKeyboardButton(_t(update, "btn.refresh", "🔄"), callback_data=refresh_cb),
            _btn(update, "btn.back", "vis_menu"),
            _btn(update, "btn.back_home", "main_menu"),
        ])

        return InlineKeyboardMarkup(rows)

    # ============================================================
    # 渲染逻辑
    # ============================================================
    async def render_chart(self, template_id: str, symbol: str, interval: str, update=None) -> Tuple[Optional[bytes], str]:
        """渲染图表"""
        try:
            from templates.registry import register_defaults

            registry = register_defaults()
            result = registry.get(template_id)
            if not result:
                return None, _t(update, "error.unknown_template", f"未知模板: {template_id}")

            meta, render_fn = result
            tpl = VIS_TEMPLATES.get(template_id, {})

            # 构建参数
            params = {
                "interval": interval,
            }

            # 单币图表需要 symbol
            if tpl.get("category") == "single":
                params["symbol"] = symbol
                params["periods"] = 10
                params["show_ohlc"] = True

            # 全市场图表需要从数据库获取多币种数据
            if tpl.get("category") == "market":
                market_data = await self._fetch_market_data(interval)
                if not market_data:
                    return None, _t(update, "vis.error.no_data", "无法获取市场数据")
                params["data"] = market_data

            # 添加标题
            name = _t(update, tpl.get("name_key", ""), tpl.get("name_fallback", template_id))
            if tpl.get("category") == "single":
                params["title"] = f"{symbol} {name} - {interval}"
            else:
                params["title"] = f"{name} - {interval}"

            # 渲染
            data, content_type = render_fn(params, "png")
            if content_type == "image/png":
                return data, ""
            else:
                return None, _t(update, "vis.error.render_failed", "渲染失败")

        except Exception as e:
            logger.error(f"渲染图表失败: {e}", exc_info=True)
            return None, str(e)

    async def _fetch_market_data(self, interval: str) -> List[Dict]:
        """获取全市场 VPVR 数据（从 SQLite 或 trading-service）"""
        try:
            # 尝试从 trading-service 获取 VPVR 数据
            trading_service_path = Path(__file__).resolve().parent.parent.parent.parent.parent / "trading-service" / "src"
            if str(trading_service_path) not in sys.path:
                sys.path.insert(0, str(trading_service_path))

            from indicators.batch.vpvr import compute_vpvr_zone

            market_data = []
            for symbol in DEFAULT_SYMBOLS[:6]:  # 最多 6 个
                try:
                    result = compute_vpvr_zone(symbol, interval, lookback=200)
                    if result:
                        market_data.append({
                            "symbol": symbol,
                            "price": result.get("close", 0),
                            "value_area_low": result.get("value_area_low", 0),
                            "value_area_high": result.get("value_area_high", 0),
                            "poc": result.get("poc", 0),
                            "coverage": result.get("coverage", 0.7),
                            "price_change": result.get("price_change", 0),
                        })
                except Exception as e:
                    logger.warning(f"获取 {symbol} VPVR 数据失败: {e}")
                    continue

            return market_data
        except ImportError:
            logger.warning("无法导入 VPVR 计算模块")
            return []
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            return []

    # ============================================================
    # 回调处理
    # ============================================================
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """处理可视化相关回调"""
        query = update.callback_query
        if not query:
            return False

        data = query.data
        user_id = query.from_user.id

        # 无操作占位
        if data == "vis_nop":
            # 即时响应已在 app.py 统一处理
            return True

        # 可视化主菜单
        if data == "vis_menu":
            # 即时响应已在 app.py 统一处理
            text = _t(update, "vis.menu.title", "📈 选择图表类型")
            keyboard = self.build_main_menu(update)
            try:
                await query.edit_message_text(text, reply_markup=keyboard)
            except Exception:
                await query.edit_message_caption(caption=text, reply_markup=keyboard)
            return True

        # 选择模板
        if data.startswith("vis_tpl_"):
            template_id = data.replace("vis_tpl_", "")
            # 即时响应已在 app.py 统一处理

            tpl = VIS_TEMPLATES.get(template_id)
            if not tpl:
                await query.answer(_t(update, "error.unknown_template", "未知模板"), show_alert=True)
                return True

            self._set_state(user_id, template=template_id, category=tpl.get("category", "single"))

            name = _t(update, tpl["name_key"], tpl["name_fallback"])
            desc = _t(update, tpl.get("desc_key", ""), tpl.get("desc_fallback", ""))

            if tpl.get("category") == "single":
                # 单币图表：选择币种
                text = f"{name}\n{desc}\n\n" + _t(update, "vis.select_symbol", "选择币种：")
                keyboard = self.build_symbol_keyboard(template_id, update)
            else:
                # 全市场图表：直接选择周期
                text = f"{name}\n{desc}\n\n" + _t(update, "vis.select_interval", "选择周期：")
                keyboard = self.build_interval_keyboard(template_id, "_market_", update)

            try:
                await query.edit_message_text(text, reply_markup=keyboard)
            except Exception:
                await query.edit_message_caption(caption=text, reply_markup=keyboard)
            return True

        # 选择币种
        if data.startswith("vis_sym_"):
            parts = data.replace("vis_sym_", "").split("_", 1)
            if len(parts) < 2:
                return False
            template_id, symbol = parts
            # 即时响应已在 app.py 统一处理

            self._set_state(user_id, symbol=symbol)

            tpl = VIS_TEMPLATES.get(template_id, {})
            name = _t(update, tpl.get("name_key", ""), tpl.get("name_fallback", ""))
            text = f"{name} - {symbol}\n" + _t(update, "vis.select_interval", "选择周期：")
            keyboard = self.build_interval_keyboard(template_id, symbol, update)
            try:
                await query.edit_message_text(text, reply_markup=keyboard)
            except Exception:
                await query.edit_message_caption(caption=text, reply_markup=keyboard)
            return True

        # 选择周期并渲染
        if data.startswith("vis_itv_"):
            parts = data.replace("vis_itv_", "").split("_")
            if len(parts) < 3:
                return False
            template_id = parts[0]
            symbol = parts[1]
            interval = parts[2]

            # 即时响应已在 app.py 统一处理 ("📈 正在渲染图表...")

            self._set_state(user_id, interval=interval)

            # 渲染图表
            image_data, error = await self.render_chart(template_id, symbol, interval, update)

            if error:
                keyboard = self.build_result_keyboard(template_id, symbol, interval, update)
                error_text = _t(update, "vis.render_error", f"渲染失败: {error}", error=error)
                try:
                    await query.edit_message_text(error_text, reply_markup=keyboard)
                except Exception:
                    await query.edit_message_caption(caption=error_text, reply_markup=keyboard)
                return True

            # 发送图片
            keyboard = self.build_result_keyboard(template_id, symbol, interval, update)
            tpl = VIS_TEMPLATES.get(template_id, {})
            name = _t(update, tpl.get("name_key", ""), tpl.get("name_fallback", template_id))

            if symbol == "_market_":
                caption = f"{name} - {interval}"
            else:
                caption = f"{symbol} {name} - {interval}"

            try:
                # 删除旧消息，发送新图片
                await query.message.delete()
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=io.BytesIO(image_data),
                    caption=caption,
                    reply_markup=keyboard,
                )
            except Exception as e:
                logger.warning(f"发送图片失败: {e}")
                # 降级：发送新消息
                try:
                    await context.bot.send_photo(
                        chat_id=query.message.chat_id,
                        photo=io.BytesIO(image_data),
                        caption=caption,
                        reply_markup=keyboard,
                    )
                except Exception as e2:
                    logger.error(f"降级发送也失败: {e2}")

            return True

        return False


# ============================================================
# 全局实例
# ============================================================
_vis_handler: Optional[VisHandler] = None


def get_vis_handler() -> VisHandler:
    """获取可视化处理器单例"""
    global _vis_handler
    if _vis_handler is None:
        _vis_handler = VisHandler()
    return _vis_handler


async def vis_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """可视化回调处理入口"""
    handler = get_vis_handler()
    return await handler.handle_callback(update, context)
