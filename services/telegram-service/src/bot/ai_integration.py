# -*- coding: utf-8 -*-
"""
AI 服务集成模块 - 桥接 telegram-service 和 ai-service
"""
from __future__ import annotations

import sys
from pathlib import Path

# 添加 ai-service 到 path
AI_SERVICE_PATH = Path(__file__).resolve().parents[3] / "ai-service"
if str(AI_SERVICE_PATH) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_PATH))

# 会话状态常量
SELECTING_COIN = 0
SELECTING_INTERVAL = 1

# 导入 ai-service 模块
try:
    from src import (
        AIAnalysisHandler,
        get_ai_handler,
        register_ai_handlers,
        run_analysis,
        PromptRegistry,
    )
    from src.bot.handler import match_ai_trigger
    AI_SERVICE_AVAILABLE = True
except ImportError:
    AI_SERVICE_AVAILABLE = False
    AIAnalysisHandler = None
    get_ai_handler = None
    register_ai_handlers = None
    run_analysis = None
    PromptRegistry = None
    match_ai_trigger = None

__all__ = [
    "AIAnalysisHandler",
    "get_ai_handler",
    "register_ai_handlers",
    "run_analysis",
    "PromptRegistry",
    "SELECTING_COIN",
    "SELECTING_INTERVAL",
    "AI_SERVICE_AVAILABLE",
    "match_ai_trigger",
]
