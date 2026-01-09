#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境变量管理模块 - 通过 Bot 管理 .env 配置

设计原则（为"最糟糕的用户"设计）：
- 所有操作最多 3 步
- 友好的文案，禁止责备性词汇
- 即时反馈，让用户知道发生了什么
- 主动提供帮助和示例
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# 项目根目录
_PROJECT_ROOT = Path(__file__).parents[4]
ENV_PATH = _PROJECT_ROOT / "config" / ".env"

# =============================================================================
# 配置白名单（允许通过 Bot 修改）
# 设计原则：用人话描述，提供清晰的帮助信息
# =============================================================================
EDITABLE_CONFIGS = {
    # 代理设置 - 最常见的配置需求
    "HTTP_PROXY": {
        "name": "🌐 HTTP 代理",
        "desc": "访问 Telegram/Binance 时使用的代理",
        "help": "格式：http://IP:端口\n例如：http://127.0.0.1:7890",
        "category": "proxy",
        "hot_reload": False,
        "placeholder": "http://127.0.0.1:7890",
        "icon": "🌐",
    },
    "HTTPS_PROXY": {
        "name": "🔒 HTTPS 代理",
        "desc": "通常和 HTTP 代理设置相同即可",
        "help": "格式：http://IP:端口\n大多数情况下填和 HTTP 代理一样的值",
        "category": "proxy",
        "hot_reload": False,
        "placeholder": "http://127.0.0.1:7890",
        "icon": "🔒",
    },
    
    # 币种管理 - 核心配置
    "SYMBOLS_GROUPS": {
        "name": "💰 监控币种",
        "desc": "选择要监控的币种范围",
        "help": "选择一个预设分组，或输入自定义",
        "category": "symbols",
        "hot_reload": True,
        "options": [
            {"value": "main4", "label": "🔥 主流4币", "detail": "BTC/ETH/SOL/BNB"},
            {"value": "main6", "label": "⭐ 主流6币", "detail": "+XRP/DOGE"},
            {"value": "main20", "label": "📊 主流20币", "detail": "常见主流币"},
            {"value": "auto", "label": "🤖 智能选择", "detail": "自动选高交易量币"},
            {"value": "all", "label": "🌍 全部币种", "detail": "600+币种，资源消耗大"},
        ],
        "icon": "💰",
    },
    "SYMBOLS_EXTRA": {
        "name": "➕ 额外添加",
        "desc": "在分组基础上额外添加的币种",
        "help": "输入币种代码，多个用逗号分隔\n例如：PEPEUSDT,WIFUSDT",
        "category": "symbols",
        "hot_reload": True,
        "placeholder": "PEPEUSDT,WIFUSDT",
        "icon": "➕",
    },
    "SYMBOLS_EXCLUDE": {
        "name": "➖ 排除币种",
        "desc": "从分组中排除这些币种",
        "help": "输入不想监控的币种\n例如：LUNAUSDT",
        "category": "symbols",
        "hot_reload": True,
        "placeholder": "LUNAUSDT",
        "icon": "➖",
    },
    "BLOCKED_SYMBOLS": {
        "name": "🚫 屏蔽显示",
        "desc": "这些币种不会出现在排行榜中",
        "help": "用于隐藏异常或不想看到的币种\n例如：BNXUSDT,ALPACAUSDT",
        "category": "symbols",
        "hot_reload": True,
        "placeholder": "BNXUSDT,ALPACAUSDT",
        "icon": "🚫",
    },
    
    # 功能开关 - 简单的开/关
    "DISABLE_SINGLE_TOKEN_QUERY": {
        "name": "🔍 单币查询",
        "desc": "发送 BTC! 查询单币详情",
        "help": "开启后可以发送如 BTC! 来查询单个币种",
        "category": "features",
        "hot_reload": True,
        "options": [
            {"value": "0", "label": "✅ 开启", "detail": "可用单币查询"},
            {"value": "1", "label": "⏸️ 关闭", "detail": "节省资源"},
        ],
        "icon": "🔍",
        "invert_display": True,  # 0=开启，显示逻辑反转
    },
    "BINANCE_API_DISABLED": {
        "name": "📡 实时数据",
        "desc": "从 Binance 获取实时价格",
        "help": "关闭后使用缓存数据，开启需要代理",
        "category": "features",
        "hot_reload": True,
        "options": [
            {"value": "0", "label": "✅ 开启", "detail": "实时价格，需代理"},
            {"value": "1", "label": "⏸️ 关闭", "detail": "使用缓存数据"},
        ],
        "icon": "📡",
        "invert_display": True,
    },
    
    # 展示设置
    "DEFAULT_LOCALE": {
        "name": "🌍 界面语言",
        "desc": "Bot 显示的语言",
        "help": "切换后立即生效",
        "category": "display",
        "hot_reload": True,
        "options": [
            {"value": "zh-CN", "label": "🇨🇳 中文", "detail": ""},
            {"value": "en", "label": "🇺🇸 English", "detail": ""},
        ],
        "icon": "🌍",
    },
    "SNAPSHOT_HIDDEN_FIELDS": {
        "name": "🙈 隐藏字段",
        "desc": "单币快照中不显示的字段",
        "help": "输入要隐藏的字段名，用逗号分隔",
        "category": "display",
        "hot_reload": True,
        "placeholder": "最近翻转时间",
        "icon": "🙈",
    },
    
    # 卡片开关
    "CARDS_ENABLED": {
        "name": "📊 启用卡片",
        "desc": "只显示这些排行卡片",
        "help": "留空显示全部，或输入要显示的卡片名",
        "category": "cards",
        "hot_reload": True,
        "placeholder": "资金流向,MACD",
        "icon": "📊",
    },
    "CARDS_DISABLED": {
        "name": "🚫 禁用卡片",
        "desc": "不显示这些排行卡片",
        "help": "输入要隐藏的卡片名，用逗号分隔",
        "category": "cards",
        "hot_reload": True,
        "placeholder": "K线形态",
        "icon": "🚫",
    },
    
    # 指标开关
    "INDICATORS_ENABLED": {
        "name": "📈 启用指标",
        "desc": "只计算这些指标",
        "help": "留空计算全部，需重启生效",
        "category": "indicators",
        "hot_reload": False,
        "placeholder": "macd,rsi",
        "icon": "📈",
    },
    "INDICATORS_DISABLED": {
        "name": "🚫 禁用指标",
        "desc": "不计算这些指标",
        "help": "可节省资源，需重启生效",
        "category": "indicators",
        "hot_reload": False,
        "placeholder": "k线形态",
        "icon": "🚫",
    },
}

# 只读配置（禁止修改）
READONLY_CONFIGS = {
    "BOT_TOKEN", "DATABASE_URL", 
    "BINANCE_API_KEY", "BINANCE_API_SECRET",
    "POSTGRES_PASSWORD", "POSTGRES_USER",
}

# 配置分类 - 用户最关心的放前面
CONFIG_CATEGORIES = {
    "symbols": {
        "name": "💰 币种管理",
        "desc": "设置要监控哪些币种",
        "icon": "💰",
        "priority": 1,
    },
    "features": {
        "name": "⚡ 功能开关",
        "desc": "开启或关闭某些功能",
        "icon": "⚡",
        "priority": 2,
    },
    "proxy": {
        "name": "🌐 网络代理",
        "desc": "国内访问需要设置代理",
        "icon": "🌐",
        "priority": 3,
    },
    "display": {
        "name": "🎨 显示设置",
        "desc": "语言、界面相关",
        "icon": "🎨",
        "priority": 4,
    },
    "cards": {
        "name": "📊 卡片管理",
        "desc": "控制显示哪些排行卡片",
        "icon": "📊",
        "priority": 5,
    },
    "indicators": {
        "name": "📈 指标计算",
        "desc": "控制计算哪些指标",
        "icon": "📈",
        "priority": 6,
    },
}

# =============================================================================
# 友好文案（禁止责备性词汇）
# =============================================================================
FRIENDLY_MESSAGES = {
    "save_success": "✨ 保存成功！",
    "save_success_hot": "✨ 保存成功，已立即生效！",
    "save_success_restart": "✨ 保存成功！重启后生效~",
    "validation_hint": "💡 小提示：",
    "input_prompt": "📝 请输入新的值：",
    "current_value": "当前：",
    "not_set": "未设置",
    "back": "⬅️ 返回",
    "cancel": "❌ 取消",
    "confirm": "✅ 确认",
    "clear": "🗑️ 清空",
}


def read_env() -> Dict[str, str]:
    """读取 .env 文件为字典"""
    result = {}
    if not ENV_PATH.exists():
        logger.warning(f".env 文件不存在: {ENV_PATH}")
        return result
    
    try:
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            # 去除引号
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            result[key] = value
    except Exception as e:
        logger.error(f"读取 .env 失败: {e}")
    
    return result


def read_env_raw() -> str:
    """读取 .env 文件原始内容"""
    if not ENV_PATH.exists():
        return ""
    return ENV_PATH.read_text(encoding="utf-8")


def get_config(key: str) -> Optional[str]:
    """获取单个配置值（优先环境变量，其次 .env 文件）"""
    # 优先从当前环境变量获取
    value = os.environ.get(key)
    if value is not None:
        return value
    # 其次从 .env 文件获取
    env_dict = read_env()
    return env_dict.get(key)


def set_config(key: str, value: str) -> Tuple[bool, str]:
    """
    设置配置值
    
    Returns:
        (success, message) - 使用友好文案
    """
    config_info = EDITABLE_CONFIGS.get(key, {})
    config_name = config_info.get("name", key)
    
    # 检查是否允许修改（友好提示）
    if key in READONLY_CONFIGS:
        return False, f"🔒 {config_name} 是系统核心配置，需要在文件中手动修改哦"
    
    if key not in EDITABLE_CONFIGS:
        return False, f"🤔 暂不支持修改 {key}，如有需要请联系管理员"
    
    # 读取当前文件内容
    if not ENV_PATH.exists():
        return False, f"📁 配置文件还没准备好，请先完成初始化"
    
    try:
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
        found = False
        new_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(f"{key}=") or stripped.startswith(f"{key} ="):
                new_lines.append(f"{key}={value}")
                found = True
            else:
                new_lines.append(line)
        
        if not found:
            new_lines.append(f"{key}={value}")
        
        ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        os.environ[key] = value
        
        # 触发热更新，使用友好反馈
        if config_info.get("hot_reload"):
            _trigger_hot_reload(key)
            # 显示友好的值
            display_value = _format_display_value(key, value)
            return True, f"✨ {config_name}\n\n已更新为：{display_value}\n\n🚀 立即生效！"
        else:
            display_value = _format_display_value(key, value)
            return True, f"✨ {config_name}\n\n已更新为：{display_value}\n\n💡 重启后生效~"
        
    except PermissionError:
        return False, f"😅 没有写入权限，请检查配置文件权限设置"
    except Exception as e:
        logger.error(f"写入 .env 失败: {e}")
        return False, f"😅 保存时遇到了问题，请稍后再试\n\n技术信息：{e}"


def _format_display_value(key: str, value: str) -> str:
    """格式化显示值，让用户更容易理解"""
    config_info = EDITABLE_CONFIGS.get(key, {})
    options = config_info.get("options", [])
    
    # 如果是选项类型，显示选项标签
    if options and isinstance(options[0], dict):
        for opt in options:
            if opt.get("value") == value:
                return f"{opt.get('label', value)}"
    
    # 空值友好显示
    if not value:
        return "（已清空）"
    
    return f"`{value}`"


def _trigger_hot_reload(key: str):
    """触发热更新"""
    try:
        if key in ("SYMBOLS_GROUPS", "SYMBOLS_EXTRA", "SYMBOLS_EXCLUDE"):
            # 重置币种缓存
            from cards.data_provider import reset_symbols_cache
            reset_symbols_cache()
            logger.info(f"已重置币种缓存: {key}")
        
        if key == "BLOCKED_SYMBOLS":
            # BLOCKED_SYMBOLS 通过动态获取，无需额外操作
            logger.info(f"已更新屏蔽币种: {key}")
        
        if key in ("CARDS_ENABLED", "CARDS_DISABLED"):
            # 卡片注册表热更新
            from cards.registry import reload_card_config
            reload_card_config()
            logger.info(f"已重载卡片配置: {key}")
            
    except ImportError as e:
        logger.warning(f"热更新模块导入失败: {e}")
    except Exception as e:
        logger.error(f"热更新失败: {e}")


def get_editable_configs_by_category() -> Dict[str, List[dict]]:
    """按分类获取可编辑的配置"""
    result = {cat: [] for cat in CONFIG_CATEGORIES}
    
    env_dict = read_env()
    
    for key, info in EDITABLE_CONFIGS.items():
        category = info.get("category", "other")
        current_value = os.environ.get(key) or env_dict.get(key, "")
        
        result[category].append({
            "key": key,
            "value": current_value,
            "desc": info.get("desc", key),
            "desc_en": info.get("desc_en", key),
            "hot_reload": info.get("hot_reload", False),
            "options": info.get("options"),
            "example": info.get("example"),
        })
    
    return result


def get_config_summary() -> str:
    """获取配置摘要（用于显示）"""
    env_dict = read_env()
    lines = []
    
    for category, cat_info in CONFIG_CATEGORIES.items():
        configs = [c for c in EDITABLE_CONFIGS.items() if c[1].get("category") == category]
        if not configs:
            continue
        
        lines.append(f"\n{cat_info['name']}")
        for key, info in configs:
            value = os.environ.get(key) or env_dict.get(key, "")
            display_value = value if len(value) < 30 else value[:27] + "..."
            hot = "🔥" if info.get("hot_reload") else "🔄"
            lines.append(f"  {hot} {info['desc']}: {display_value or '(未设置)'}")
    
    return "\n".join(lines)


def validate_config_value(key: str, value: str) -> Tuple[bool, str]:
    """
    验证配置值
    使用友好文案，告诉用户如何修正而不是责备
    """
    config_info = EDITABLE_CONFIGS.get(key)
    if not config_info:
        return False, "🤔 这个配置项暂不支持修改"
    
    # 允许清空
    if not value:
        return True, "OK"
    
    # 检查选项限制
    options = config_info.get("options")
    if options:
        # 新格式：[{value, label}, ...]
        if isinstance(options[0], dict):
            valid_values = [opt["value"] for opt in options]
            if value not in valid_values:
                labels = [f"{opt['label']}" for opt in options]
                return False, f"💡 请从以下选项中选择：\n" + "\n".join(labels)
        # 旧格式：["a", "b", ...]
        elif value not in options:
            return False, f"💡 请从以下选项中选择：{', '.join(options)}"
    
    # 代理格式验证
    if key in ("HTTP_PROXY", "HTTPS_PROXY") and value:
        if not re.match(r'^(http|https|socks5)://[\w\-\.]+:\d+$', value):
            return False, (
                "💡 代理格式需要这样写：\n"
                "• http://127.0.0.1:7890\n"
                "• socks5://127.0.0.1:1080\n\n"
                "请检查一下格式~"
            )
    
    # 币种格式验证
    if key in ("SYMBOLS_EXTRA", "SYMBOLS_EXCLUDE", "BLOCKED_SYMBOLS") and value:
        symbols = [s.strip().upper() for s in value.split(",") if s.strip()]
        invalid = [s for s in symbols if not re.match(r'^[A-Z0-9]+USDT$', s)]
        if invalid:
            return False, (
                f"💡 币种格式需要以 USDT 结尾\n\n"
                f"• 正确：BTCUSDT, ETHUSDT\n"
                f"• 你输入的：{', '.join(invalid)}\n\n"
                f"请修改一下~"
            )
    
    return True, "OK"
