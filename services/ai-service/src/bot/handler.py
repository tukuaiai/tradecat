# -*- coding: utf-8 -*-
"""
AI 分析 Telegram 交互模块
- 展示可分析币种列表 -> 用户输入币种名 -> 选择周期 -> 触发 AI 分析
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.prompt import PromptRegistry
from src.pipeline import run_analysis
from src.config import PROJECT_ROOT
from libs.common.i18n import normalize_locale

logger = logging.getLogger(__name__)

# 会话状态
SELECTING_COIN = 0
SELECTING_INTERVAL = 1

# 提示词注册表
prompt_registry = PromptRegistry()


def get_configured_symbols() -> List[str]:
    """获取配置的币种列表（从 common.symbols）"""
    try:
        import sys
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
        from libs.common.symbols import get_configured_symbols as _get
        return _get()
    except Exception as e:
        logger.warning(f"获取配置币种失败: {e}")
        return ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT"]


class AIAnalysisHandler:
    """AI 分析处理器"""

    def __init__(self, symbols_provider=None):
        self._symbols_provider = symbols_provider
        self._cached_symbols: List[str] = []
        self._cache_time = 0
        self.default_prompt = "市场全局解析"

    def get_supported_symbols(self) -> List[str]:
        """获取支持的币种列表"""
        import time
        now = time.time()
        
        if self._cached_symbols and (now - self._cache_time) < 300:
            return self._cached_symbols
        
        # 优先使用外部提供的币种列表
        if self._symbols_provider:
            try:
                symbols = self._symbols_provider()
                if symbols:
                    self._cached_symbols = sorted([s for s in symbols if s.endswith("USDT")])
                    self._cache_time = now
                    return self._cached_symbols
            except Exception as e:
                logger.warning(f"外部币种提供器失败: {e}")
        
        # 回退到配置的币种
        self._cached_symbols = get_configured_symbols()
        self._cache_time = now
        return self._cached_symbols

    # -------- 入口：展示币种列表 --------
    async def start_ai_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """AI 分析入口 - 展示可分析币种列表"""
        context.user_data.setdefault("ai_prompt_name", self.default_prompt)
        
        symbols = self.get_supported_symbols()
        # 去掉 USDT 后缀，每行一个
        coins = [s.replace("USDT", "") for s in symbols]
        coins_text = "\n".join(coins)
        
        prompt_name = context.user_data.get("ai_prompt_name", self.default_prompt)
        
        text = (
            "🤖 *AI 分析*\n"
            f"```\n{coins_text}\n```\n"
            f"📊 可分析币种 ({len(coins)} 个)\n"
            "💡 使用方法: 发送 `币种名@` 触发分析\n"
            "例如: `BTC@` 或 `ETH@`"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 返回主菜单", callback_data="main_menu")],
        ])
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        elif update.message:
            await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
        return SELECTING_COIN

    # -------- 处理用户输入的币种 --------
    async def handle_coin_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, coin: str) -> int:
        """处理用户输入的币种，进入周期选择"""
        symbol = coin.upper().replace("USDT", "") + "USDT"
        
        # 验证币种是否支持
        symbols = self.get_supported_symbols()
        if symbol not in symbols:
            await update.message.reply_text(
                f"❌ 不支持的币种: {coin}\n\n请从支持列表中选择",
                parse_mode='Markdown'
            )
            return SELECTING_COIN
        
        context.user_data["ai_selected_symbol"] = symbol
        return await self._show_interval_selection(update, context, symbol)

    # -------- 周期选择 --------
    async def handle_interval_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """处理周期选择回调"""
        query = update.callback_query
        if not query or not query.data:
            return SELECTING_COIN
        await query.answer()
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
                await query.edit_message_text("❌ 未选择币种，请重新发送 `币种名@`", parse_mode='Markdown')
                return SELECTING_COIN
            
            await query.edit_message_text(
                f"🔄 正在分析 *{symbol.replace('USDT','')}* @ {interval} ...\n\n"
                f"⏳ AI 分析需要 30-60 秒，请稍候",
                parse_mode='Markdown'
            )
            asyncio.create_task(self._run_analysis(update, context, symbol, interval, prompt_name))
            return SELECTING_COIN

        if data == "ai_cancel":
            await query.edit_message_text("已取消 AI 分析")
            return SELECTING_COIN

        return SELECTING_COIN

    # -------- 币种选择回调（兼容旧逻辑） --------
    async def handle_coin_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """处理币种选择相关回调"""
        query = update.callback_query
        if not query or not query.data:
            return SELECTING_COIN
        await query.answer()
        data = query.data

        if data == "ai_select_prompt":
            return await self._show_prompt_selection(update, context)
        
        if data.startswith("ai_set_prompt_"):
            return await self._handle_prompt_selected(update, context)

        if data == "ai_cancel":
            await query.edit_message_text("已取消 AI 分析")
            return SELECTING_COIN

        return SELECTING_COIN

    # -------- 视图构建 --------
    async def _show_interval_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str) -> int:
        """显示周期选择界面"""
        current_prompt = context.user_data.get("ai_prompt_name", self.default_prompt)
        
        # 周期按钮
        keyboard = [
            [
                InlineKeyboardButton("5m", callback_data="ai_interval_5m"),
                InlineKeyboardButton("15m", callback_data="ai_interval_15m"),
                InlineKeyboardButton("1h", callback_data="ai_interval_1h"),
                InlineKeyboardButton("4h", callback_data="ai_interval_4h"),
                InlineKeyboardButton("1d", callback_data="ai_interval_1d"),
            ],
        ]
        
        # 提示词按钮（直接显示，选中的有 ✅）
        prompts = prompt_registry.list_prompts(grouped=False)
        prompt_row = []
        for item in prompts:
            name = item["name"]
            title = item["title"]
            if name == current_prompt:
                label = f"✅{title}"
            else:
                label = title
            prompt_row.append(InlineKeyboardButton(label, callback_data=f"ai_set_prompt_{name}"))
        if prompt_row:
            keyboard.append(prompt_row)
        
        # 底部按钮
        keyboard.append([
            InlineKeyboardButton("🏠 返回主菜单", callback_data="main_menu"),
        ])
        
        text = (
            f"🤖 *AI 深度分析*\n"
            f"```\n📌 币种: {symbol.replace('USDT','')}\n🧠 提示词: {current_prompt}\n```\n"
            f"请选择分析周期:"
        )
        markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode='Markdown')
        elif update.message:
            await update.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')
        
        return SELECTING_INTERVAL

    async def _show_prompt_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """显示提示词选择（兼容旧逻辑，重定向到周期选择）"""
        symbol = context.user_data.get("ai_selected_symbol")
        if symbol:
            return await self._show_interval_selection(update, context, symbol)
        return await self.start_ai_analysis(update, context)

    async def _handle_prompt_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """处理提示词选择 - 切换后刷新当前界面"""
        query = update.callback_query
        if not query or not query.data:
            return SELECTING_COIN
        await query.answer()
        
        prompt_key = query.data.replace("ai_set_prompt_", "", 1)
        context.user_data["ai_prompt_name"] = prompt_key
        
        # 刷新周期选择界面
        symbol = context.user_data.get("ai_selected_symbol")
        if symbol:
            return await self._show_interval_selection(update, context, symbol)
        return await self.start_ai_analysis(update, context)

    # -------- 分析执行 --------
    async def _run_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                            symbol: str, interval: str, prompt: str):
        """执行 AI 分析"""
        try:
            user_lang = None
            if update.effective_user and update.effective_user.language_code:
                user_lang = normalize_locale(update.effective_user.language_code)
            result = await run_analysis(symbol, interval, prompt, lang=user_lang)
            analysis_text = result.get("analysis", "未生成 AI 分析结果")
            
            # Telegram 消息限制 4096 字符
            if len(analysis_text) > 4000:
                parts = [analysis_text[i:i+4000] for i in range(0, len(analysis_text), 4000)]
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


# -------- 模块级接口 --------
_handler_instance: Optional[AIAnalysisHandler] = None


def get_ai_handler(symbols_provider=None) -> AIAnalysisHandler:
    """获取 AI 分析处理器单例"""
    global _handler_instance
    if _handler_instance is None:
        _handler_instance = AIAnalysisHandler(symbols_provider)
    return _handler_instance


def register_ai_handlers(application, symbols_provider=None):
    """注册 AI 分析处理器（预留接口）"""
    handler = get_ai_handler(symbols_provider)
    logger.info("✅ AI 分析模块已注册")


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
    "prompt_registry",
    "SELECTING_COIN",
    "SELECTING_INTERVAL",
    "match_ai_trigger",
]
