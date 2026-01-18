# -*- coding: utf-8 -*-
"""
AI 服务集成模块 - 桥接 telegram-service 和 ai-service

将 AI 分析的核心逻辑（ai-service）与 Telegram UI（本模块）解耦
"""
from __future__ import annotations

import asyncio
import logging
import re
import sys
from pathlib import Path
from typing import List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# 添加 ai-service 到 path
AI_SERVICE_PATH = Path(__file__).resolve().parents[3] / "ai-service"
if str(AI_SERVICE_PATH) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_PATH))

# 添加项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)

# 会话状态常量
SELECTING_COIN = 0
SELECTING_INTERVAL = 1

# 导入 ai-service 核心模块
try:
    from src.pipeline import run_analysis
    from src.prompt import PromptRegistry
    AI_SERVICE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ai-service 不可用: {e}")
    AI_SERVICE_AVAILABLE = False
    run_analysis = None
    PromptRegistry = None

# i18n
try:
    from libs.common.i18n import normalize_locale, build_i18n_from_env
    I18N = build_i18n_from_env()
except ImportError:
    I18N = None
    def normalize_locale(lang):
        return lang or "zh_CN"

# 提示词注册表
prompt_registry = PromptRegistry() if PromptRegistry else None


def get_configured_symbols() -> List[str]:
    """获取配置的币种列表"""
    try:
        from libs.common.symbols import get_configured_symbols as _get
        return _get()
    except Exception as e:
        logger.warning(f"获取配置币种失败: {e}")
        return ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT"]


class AIAnalysisHandler:
    """AI 分析处理器（Telegram UI）"""

    def __init__(self, symbols_provider=None):
        self._symbols_provider = symbols_provider
        self._cached_symbols: List[str] = []
        self._cache_time = 0
        self.default_prompt = "市场全局解析"

    @staticmethod
    def _get_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """获取用户语言"""
        if context and hasattr(context, "user_data"):
            lang = context.user_data.get("lang_preference")
            if lang:
                return normalize_locale(lang)
        if update and getattr(getattr(update, "effective_user", None), "language_code", None):
            return normalize_locale(update.effective_user.language_code)
        return "zh_CN"

    def _t(self, update: Update, context: ContextTypes.DEFAULT_TYPE, msgid: str, **kwargs) -> str:
        """翻译文本"""
        if I18N:
            lang = self._get_lang(update, context)
            return I18N.gettext(msgid, lang=lang, **kwargs)
        return msgid

    def get_supported_symbols(self) -> List[str]:
        """获取支持的币种列表"""
        import time
        now = time.time()

        if self._cached_symbols and (now - self._cache_time) < 300:
            return self._cached_symbols

        if self._symbols_provider:
            try:
                symbols = self._symbols_provider()
                if symbols:
                    self._cached_symbols = sorted([s for s in symbols if s.endswith("USDT")])
                    self._cache_time = now
                    return self._cached_symbols
            except Exception as e:
                logger.warning(f"外部币种提供器失败: {e}")

        self._cached_symbols = get_configured_symbols()
        self._cache_time = now
        return self._cached_symbols

    async def start_ai_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """AI 分析入口 - 展示可分析币种列表"""
        if not AI_SERVICE_AVAILABLE:
            text = "AI 分析服务不可用"
            if update.callback_query:
                await update.callback_query.edit_message_text(text)
            elif update.message:
                await update.message.reply_text(text)
            return SELECTING_COIN

        context.user_data.setdefault("ai_prompt_name", self.default_prompt)

        symbols = self.get_supported_symbols()
        coins = [s.replace("USDT", "") for s in symbols]
        coins_text = "\n".join(coins)

        text = (
            f"{self._t(update, context, 'ai.list.title')}\n"
            f"```\n{coins_text}\n```\n"
            f"{self._t(update, context, 'ai.list.supported', count=len(coins))}\n"
            f"{self._t(update, context, 'ai.list.usage')}"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(self._t(update, context, "menu.home"), callback_data="main_menu")],
        ])

        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        elif update.message:
            await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')

        return SELECTING_COIN

    async def handle_coin_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, coin: str) -> int:
        """处理用户输入的币种"""
        symbol = coin.upper().replace("USDT", "") + "USDT"

        symbols = self.get_supported_symbols()
        if symbol not in symbols:
            await update.message.reply_text(
                self._t(update, context, "ai.unsupported", coin=coin),
                parse_mode='Markdown'
            )
            return SELECTING_COIN

        context.user_data["ai_selected_symbol"] = symbol
        return await self._show_interval_selection(update, context, symbol)

    async def handle_interval_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """处理周期选择回调"""
        query = update.callback_query
        if not query or not query.data:
            return SELECTING_COIN
        # 即时响应已在 app.py 统一处理
        data = query.data

        if data == "ai_back_to_coin":
            return await self.start_ai_analysis(update, context)

        if data == "ai_select_prompt":
            return await self._show_prompt_selection(update, context)

        if data.startswith("ai_set_prompt_"):
            return await self._handle_prompt_selected(update, context)

        if data.startswith("ai_interval_"):
            interval = data.replace("ai_interval_", "")
            symbol = context.user_data.get("ai_selected_symbol")
            prompt_name = context.user_data.get("ai_prompt_name", self.default_prompt)

            if not symbol:
                await query.edit_message_text(self._t(update, context, "ai.no_symbol"), parse_mode='Markdown')
                return SELECTING_COIN

            await query.edit_message_text(
                self._t(update, context, "ai.analyzing", symbol=symbol.replace('USDT', ''), interval=interval),
                parse_mode='Markdown'
            )
            asyncio.create_task(self._run_analysis(update, context, symbol, interval, prompt_name))
            return SELECTING_COIN

        if data == "ai_cancel":
            await query.edit_message_text(self._t(update, context, "ai.cancelled"))
            return SELECTING_COIN

        return SELECTING_COIN

    async def handle_coin_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """处理币种选择相关回调"""
        query = update.callback_query
        if not query or not query.data:
            return SELECTING_COIN
        # 即时响应已在 app.py 统一处理
        data = query.data

        if data == "ai_select_prompt":
            return await self._show_prompt_selection(update, context)

        if data.startswith("ai_set_prompt_"):
            return await self._handle_prompt_selected(update, context)

        if data == "ai_cancel":
            await query.edit_message_text(self._t(update, context, "ai.cancelled"))
            return SELECTING_COIN

        return SELECTING_COIN

    async def _show_interval_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str) -> int:
        """显示周期选择界面"""
        current_prompt = context.user_data.get("ai_prompt_name", self.default_prompt)

        periods = ["5m", "15m", "1h", "4h", "1d"]
        row = []
        for p in periods:
            label = self._t(update, context, f"period.{p}")
            if label == f"period.{p}":
                label = p
            row.append(InlineKeyboardButton(label, callback_data=f"ai_interval_{p}"))
        keyboard = [row]

        if prompt_registry:
            prompts = prompt_registry.list_prompts(grouped=False)
            prompt_row = []
            for item in prompts:
                name = item["name"]
                title = item["title"]
                label = f"✅{title}" if name == current_prompt else title
                prompt_row.append(InlineKeyboardButton(label, callback_data=f"ai_set_prompt_{name}"))
            if prompt_row:
                keyboard.append(prompt_row)

        keyboard.append([
            InlineKeyboardButton(self._t(update, context, "menu.home"), callback_data="main_menu"),
        ])

        text = (
            f"{self._t(update, context, 'ai.interval.title')}\n"
            f"```\n📌 {symbol.replace('USDT', '')}\n🧠 {self._t(update, context, 'ai.prompt.label')}: {current_prompt}\n```\n"
            f"{self._t(update, context, 'ai.interval.choose')}"
        )
        markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode='Markdown')
        elif update.message:
            await update.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')

        return SELECTING_INTERVAL

    async def _show_prompt_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """显示提示词选择"""
        symbol = context.user_data.get("ai_selected_symbol")
        if symbol:
            return await self._show_interval_selection(update, context, symbol)
        return await self.start_ai_analysis(update, context)

    async def _handle_prompt_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """处理提示词选择"""
        query = update.callback_query
        if not query or not query.data:
            return SELECTING_COIN
        # 即时响应已在 app.py 统一处理

        prompt_key = query.data.replace("ai_set_prompt_", "", 1)
        context.user_data["ai_prompt_name"] = prompt_key

        symbol = context.user_data.get("ai_selected_symbol")
        if symbol:
            return await self._show_interval_selection(update, context, symbol)
        return await self.start_ai_analysis(update, context)

    async def _run_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                            symbol: str, interval: str, prompt: str):
        """执行 AI 分析（调用 ai-service）"""
        if not run_analysis:
            error_msg = "AI 分析服务不可用"
            if update.callback_query:
                await update.callback_query.edit_message_text(error_msg)
            return

        try:
            preferred_lang = None
            if context and hasattr(context, "user_data"):
                preferred_lang = context.user_data.get("lang_preference")
            if not preferred_lang and update.effective_user and update.effective_user.language_code:
                preferred_lang = normalize_locale(update.effective_user.language_code)

            # 调用 ai-service 核心分析
            result = await run_analysis(symbol, interval, prompt, lang=preferred_lang)
            analysis_text = result.get("analysis", "未生成 AI 分析结果")

            # Telegram 消息限制 4096 字符
            if len(analysis_text) > 4000:
                parts = [analysis_text[i:i + 4000] for i in range(0, len(analysis_text), 4000)]
                for i, part in enumerate(parts):
                    if i == 0:
                        if update.callback_query and update.callback_query.message:
                            await update.callback_query.edit_message_text(part)
                        elif update.message:
                            await update.message.reply_text(part)
                    else:
                        if update.callback_query and update.callback_query.message:
                            await update.callback_query.message.reply_text(part)
                        elif update.message:
                            await update.message.reply_text(part)
            else:
                if update.callback_query:
                    await update.callback_query.edit_message_text(analysis_text)
                elif update.message:
                    await update.message.reply_text(analysis_text)

        except Exception as exc:
            logger.exception("AI 分析失败")
            error_msg = f"❌ AI 分析失败：{exc}"
            if update.callback_query:
                await update.callback_query.edit_message_text(error_msg)
            elif update.message:
                await update.message.reply_text(error_msg)


# 模块级接口
_handler_instance: Optional[AIAnalysisHandler] = None


def get_ai_handler(symbols_provider=None) -> AIAnalysisHandler:
    """获取 AI 分析处理器单例"""
    global _handler_instance
    if _handler_instance is None:
        _handler_instance = AIAnalysisHandler(symbols_provider)
    return _handler_instance


def register_ai_handlers(application, symbols_provider=None):
    """注册 AI 分析处理器"""
    get_ai_handler(symbols_provider)
    logger.info("AI 分析模块已注册")


# AI 触发正则：币种名@
AI_TRIGGER_PATTERN = re.compile(r'^([A-Za-z0-9]+)@$')


def match_ai_trigger(text: str) -> Optional[str]:
    """匹配 AI 触发格式，返回币种名或 None"""
    if not text:
        return None
    m = AI_TRIGGER_PATTERN.match(text.strip())
    return m.group(1) if m else None


__all__ = [
    "AIAnalysisHandler",
    "get_ai_handler",
    "register_ai_handlers",
    "run_analysis",
    "PromptRegistry",
    "prompt_registry",
    "SELECTING_COIN",
    "SELECTING_INTERVAL",
    "AI_SERVICE_AVAILABLE",
    "match_ai_trigger",
]
