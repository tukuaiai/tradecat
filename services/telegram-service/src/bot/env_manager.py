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
from typing import Dict, List, Optional, Tuple, Callable

logger = logging.getLogger(__name__)

# 项目根目录
_PROJECT_ROOT = Path(__file__).parents[4]
ENV_PATH = _PROJECT_ROOT / "config" / ".env"

# =============================================================================
# i18n 支持
# =============================================================================
def _get_i18n() -> Callable[[str, str], str]:
    """获取 i18n 翻译函数"""
    try:
        from bot.app import I18N
        return lambda key, lang=None: I18N.gettext(key, lang=lang)
    except ImportError:
        return lambda key, lang=None: key


def _t(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """翻译辅助函数"""
    i18n_func = _get_i18n()
    text = i18n_func(key, lang)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


# =============================================================================
# 配置白名单（允许通过 Bot 修改）
# 使用 i18n 键替代硬编码文案
# =============================================================================
EDITABLE_CONFIGS = {
    # 代理设置 - 最常见的配置需求
    "HTTP_PROXY": {
        "name_key": "env.http_proxy.name",
        "desc_key": "env.http_proxy.desc",
        "help_key": "env.http_proxy.help",
        "category": "proxy",
        "hot_reload": False,
        "placeholder": "http://127.0.0.1:7890",
        "icon": "🌐",
    },
    "HTTPS_PROXY": {
        "name_key": "env.https_proxy.name",
        "desc_key": "env.https_proxy.desc",
        "help_key": "env.https_proxy.help",
        "category": "proxy",
        "hot_reload": False,
        "placeholder": "http://127.0.0.1:7890",
        "icon": "🔒",
    },
    
    # 币种管理 - 核心配置
    "SYMBOLS_GROUPS": {
        "name_key": "env.symbols_groups.name",
        "desc_key": "env.symbols_groups.desc",
        "help_key": "env.symbols_groups.help",
        "category": "symbols",
        "hot_reload": True,
        "options": [
            {"value": "main4", "label_key": "env.symbols_groups.opt.main4", "detail_key": "env.symbols_groups.opt.main4_detail"},
            {"value": "main6", "label_key": "env.symbols_groups.opt.main6", "detail_key": "env.symbols_groups.opt.main6_detail"},
            {"value": "main20", "label_key": "env.symbols_groups.opt.main20", "detail_key": "env.symbols_groups.opt.main20_detail"},
            {"value": "auto", "label_key": "env.symbols_groups.opt.auto", "detail_key": "env.symbols_groups.opt.auto_detail"},
            {"value": "all", "label_key": "env.symbols_groups.opt.all", "detail_key": "env.symbols_groups.opt.all_detail"},
        ],
        "icon": "💰",
    },
    "SYMBOLS_EXTRA": {
        "name_key": "env.symbols_extra.name",
        "desc_key": "env.symbols_extra.desc",
        "help_key": "env.symbols_extra.help",
        "category": "symbols",
        "hot_reload": True,
        "placeholder": "PEPEUSDT,WIFUSDT",
        "icon": "➕",
    },
    "SYMBOLS_EXCLUDE": {
        "name_key": "env.symbols_exclude.name",
        "desc_key": "env.symbols_exclude.desc",
        "help_key": "env.symbols_exclude.help",
        "category": "symbols",
        "hot_reload": True,
        "placeholder": "LUNAUSDT",
        "icon": "➖",
    },
    "BLOCKED_SYMBOLS": {
        "name_key": "env.blocked_symbols.name",
        "desc_key": "env.blocked_symbols.desc",
        "help_key": "env.blocked_symbols.help",
        "category": "symbols",
        "hot_reload": True,
        "placeholder": "BNXUSDT,ALPACAUSDT",
        "icon": "🚫",
    },
    
    # 功能开关 - 简单的开/关
    "DISABLE_SINGLE_TOKEN_QUERY": {
        "name_key": "env.single_query.name",
        "desc_key": "env.single_query.desc",
        "help_key": "env.single_query.help",
        "category": "features",
        "hot_reload": True,
        "options": [
            {"value": "0", "label_key": "env.opt.enabled", "detail_key": "env.single_query.enabled_detail"},
            {"value": "1", "label_key": "env.opt.disabled", "detail_key": "env.single_query.disabled_detail"},
        ],
        "icon": "🔍",
        "invert_display": True,
    },
    "BINANCE_API_DISABLED": {
        "name_key": "env.realtime_data.name",
        "desc_key": "env.realtime_data.desc",
        "help_key": "env.realtime_data.help",
        "category": "features",
        "hot_reload": True,
        "options": [
            {"value": "0", "label_key": "env.opt.enabled", "detail_key": "env.realtime_data.enabled_detail"},
            {"value": "1", "label_key": "env.opt.disabled", "detail_key": "env.realtime_data.disabled_detail"},
        ],
        "icon": "📡",
        "invert_display": True,
    },
    
    # 展示设置
    "DEFAULT_LOCALE": {
        "name_key": "env.locale.name",
        "desc_key": "env.locale.desc",
        "help_key": "env.locale.help",
        "category": "display",
        "hot_reload": True,
        "options": [
            {"value": "zh-CN", "label_key": "env.locale.opt.zh", "detail_key": ""},
            {"value": "en", "label_key": "env.locale.opt.en", "detail_key": ""},
        ],
        "icon": "🌍",
    },
    "SNAPSHOT_HIDDEN_FIELDS": {
        "name_key": "env.hidden_fields.name",
        "desc_key": "env.hidden_fields.desc",
        "help_key": "env.hidden_fields.help",
        "category": "display",
        "hot_reload": True,
        "placeholder_key": "env.hidden_fields.placeholder",
        "icon": "🙈",
    },
    
    # 卡片开关
    "CARDS_ENABLED": {
        "name_key": "env.cards_enabled.name",
        "desc_key": "env.cards_enabled.desc",
        "help_key": "env.cards_enabled.help",
        "category": "cards",
        "hot_reload": True,
        "placeholder_key": "env.cards_enabled.placeholder",
        "icon": "📊",
    },
    "CARDS_DISABLED": {
        "name_key": "env.cards_disabled.name",
        "desc_key": "env.cards_disabled.desc",
        "help_key": "env.cards_disabled.help",
        "category": "cards",
        "hot_reload": True,
        "placeholder_key": "env.cards_disabled.placeholder",
        "icon": "🚫",
    },
    
    # 指标开关
    "INDICATORS_ENABLED": {
        "name_key": "env.indicators_enabled.name",
        "desc_key": "env.indicators_enabled.desc",
        "help_key": "env.indicators_enabled.help",
        "category": "indicators",
        "hot_reload": False,
        "placeholder": "macd,rsi",
        "icon": "📈",
    },
    "INDICATORS_DISABLED": {
        "name_key": "env.indicators_disabled.name",
        "desc_key": "env.indicators_disabled.desc",
        "help_key": "env.indicators_disabled.help",
        "category": "indicators",
        "hot_reload": False,
        "placeholder_key": "env.indicators_disabled.placeholder",
        "icon": "🚫",
    },
}

# 只读配置（禁止修改）
READONLY_CONFIGS = {
    "BOT_TOKEN", "DATABASE_URL", 
    "BINANCE_API_KEY", "BINANCE_API_SECRET",
    "POSTGRES_PASSWORD", "POSTGRES_USER",
}

# 配置分类 - 使用 i18n 键
CONFIG_CATEGORIES = {
    "symbols": {
        "name_key": "env.cat.symbols.name",
        "desc_key": "env.cat.symbols.desc",
        "icon": "💰",
        "priority": 1,
    },
    "features": {
        "name_key": "env.cat.features.name",
        "desc_key": "env.cat.features.desc",
        "icon": "⚡",
        "priority": 2,
    },
    "proxy": {
        "name_key": "env.cat.proxy.name",
        "desc_key": "env.cat.proxy.desc",
        "icon": "🌐",
        "priority": 3,
    },
    "display": {
        "name_key": "env.cat.display.name",
        "desc_key": "env.cat.display.desc",
        "icon": "🎨",
        "priority": 4,
    },
    "cards": {
        "name_key": "env.cat.cards.name",
        "desc_key": "env.cat.cards.desc",
        "icon": "📊",
        "priority": 5,
    },
    "indicators": {
        "name_key": "env.cat.indicators.name",
        "desc_key": "env.cat.indicators.desc",
        "icon": "📈",
        "priority": 6,
    },
}


# =============================================================================
# 辅助函数：获取本地化文案
# =============================================================================
def get_config_name(key: str, lang: Optional[str] = None) -> str:
    """获取配置项名称"""
    config_info = EDITABLE_CONFIGS.get(key, {})
    name_key = config_info.get("name_key")
    if name_key:
        return _t(name_key, lang)
    return key


def get_config_desc(key: str, lang: Optional[str] = None) -> str:
    """获取配置项描述"""
    config_info = EDITABLE_CONFIGS.get(key, {})
    desc_key = config_info.get("desc_key")
    if desc_key:
        return _t(desc_key, lang)
    return ""


def get_config_help(key: str, lang: Optional[str] = None) -> str:
    """获取配置项帮助"""
    config_info = EDITABLE_CONFIGS.get(key, {})
    help_key = config_info.get("help_key")
    if help_key:
        return _t(help_key, lang)
    return ""


def get_option_label(opt: dict, lang: Optional[str] = None) -> str:
    """获取选项标签"""
    label_key = opt.get("label_key")
    if label_key:
        return _t(label_key, lang)
    return opt.get("label", opt.get("value", ""))


def get_option_detail(opt: dict, lang: Optional[str] = None) -> str:
    """获取选项详情"""
    detail_key = opt.get("detail_key")
    if detail_key:
        return _t(detail_key, lang)
    return opt.get("detail", "")


def get_category_name(cat_key: str, lang: Optional[str] = None) -> str:
    """获取分类名称"""
    cat_info = CONFIG_CATEGORIES.get(cat_key, {})
    name_key = cat_info.get("name_key")
    if name_key:
        return _t(name_key, lang)
    return cat_key


def get_category_desc(cat_key: str, lang: Optional[str] = None) -> str:
    """获取分类描述"""
    cat_info = CONFIG_CATEGORIES.get(cat_key, {})
    desc_key = cat_info.get("desc_key")
    if desc_key:
        return _t(desc_key, lang)
    return ""


# =============================================================================
# 核心功能函数
# =============================================================================
def read_env() -> Dict[str, str]:
    """读取 .env 文件为字典"""
    result = {}
    if not ENV_PATH.exists():
        logger.warning(f".env file not found: {ENV_PATH}")
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
        logger.error(f"Failed to read .env: {e}")
    
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


def set_config(key: str, value: str, lang: Optional[str] = None) -> Tuple[bool, str]:
    """
    设置配置值
    
    Returns:
        (success, message) - 使用友好文案
    """
    config_name = get_config_name(key, lang)
    config_info = EDITABLE_CONFIGS.get(key, {})
    
    # 检查是否允许修改
    if key in READONLY_CONFIGS:
        return False, _t("env.msg.readonly", lang, name=config_name)
    
    if key not in EDITABLE_CONFIGS:
        return False, _t("env.msg.not_supported", lang, key=key)
    
    # 读取当前文件内容
    if not ENV_PATH.exists():
        return False, _t("env.msg.file_not_ready", lang)
    
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
        
        # 格式化显示值
        display_value = _format_display_value(key, value, lang)
        
        # 触发热更新
        if config_info.get("hot_reload"):
            _trigger_hot_reload(key)
            return True, _t("env.msg.save_hot", lang, name=config_name, value=display_value)
        else:
            return True, _t("env.msg.save_restart", lang, name=config_name, value=display_value)
        
    except PermissionError:
        return False, _t("env.msg.no_permission", lang)
    except Exception as e:
        logger.error(f"Failed to write .env: {e}")
        return False, _t("env.msg.save_error", lang, error=str(e))


def _format_display_value(key: str, value: str, lang: Optional[str] = None) -> str:
    """格式化显示值"""
    config_info = EDITABLE_CONFIGS.get(key, {})
    options = config_info.get("options", [])
    
    # 如果是选项类型，显示选项标签
    if options:
        for opt in options:
            if opt.get("value") == value:
                return get_option_label(opt, lang)
    
    # 空值友好显示
    if not value:
        return _t("env.msg.cleared", lang)
    
    return f"`{value}`"


def _trigger_hot_reload(key: str):
    """触发热更新"""
    try:
        if key in ("SYMBOLS_GROUPS", "SYMBOLS_EXTRA", "SYMBOLS_EXCLUDE"):
            from cards.data_provider import reset_symbols_cache
            reset_symbols_cache()
            logger.info(f"Reset symbols cache: {key}")
        
        if key == "BLOCKED_SYMBOLS":
            logger.info(f"Updated blocked symbols: {key}")
        
        if key in ("CARDS_ENABLED", "CARDS_DISABLED"):
            from cards.registry import reload_card_config
            reload_card_config()
            logger.info(f"Reloaded card config: {key}")
            
    except ImportError as e:
        logger.warning(f"Hot reload module import failed: {e}")
    except Exception as e:
        logger.error(f"Hot reload failed: {e}")


def get_editable_configs_by_category(lang: Optional[str] = None) -> Dict[str, List[dict]]:
    """按分类获取可编辑的配置"""
    result = {cat: [] for cat in CONFIG_CATEGORIES}
    
    env_dict = read_env()
    
    for key, info in EDITABLE_CONFIGS.items():
        category = info.get("category", "other")
        current_value = os.environ.get(key) or env_dict.get(key, "")
        
        result[category].append({
            "key": key,
            "value": current_value,
            "name": get_config_name(key, lang),
            "desc": get_config_desc(key, lang),
            "help": get_config_help(key, lang),
            "hot_reload": info.get("hot_reload", False),
            "options": info.get("options"),
            "icon": info.get("icon", ""),
        })
    
    return result


def get_config_summary(lang: Optional[str] = None) -> str:
    """获取配置摘要（用于显示）"""
    env_dict = read_env()
    lines = []
    
    for category, cat_info in CONFIG_CATEGORIES.items():
        configs = [c for c in EDITABLE_CONFIGS.items() if c[1].get("category") == category]
        if not configs:
            continue
        
        lines.append(f"\n{get_category_name(category, lang)}")
        for key, info in configs:
            value = os.environ.get(key) or env_dict.get(key, "")
            display_value = value if len(value) < 30 else value[:27] + "..."
            hot = "🔥" if info.get("hot_reload") else "🔄"
            desc = get_config_desc(key, lang)
            not_set = _t("env.msg.not_set", lang)
            lines.append(f"  {hot} {desc}: {display_value or f'({not_set})'}")
    
    return "\n".join(lines)


def validate_config_value(key: str, value: str, lang: Optional[str] = None) -> Tuple[bool, str]:
    """
    验证配置值
    使用友好文案，告诉用户如何修正
    """
    config_info = EDITABLE_CONFIGS.get(key)
    if not config_info:
        return False, _t("env.msg.not_supported_edit", lang)
    
    # 允许清空
    if not value:
        return True, "OK"
    
    # 检查选项限制
    options = config_info.get("options")
    if options:
        valid_values = [opt["value"] for opt in options]
        if value not in valid_values:
            labels = [get_option_label(opt, lang) for opt in options]
            return False, _t("env.msg.choose_option", lang) + "\n" + "\n".join(labels)
    
    # 代理格式验证
    if key in ("HTTP_PROXY", "HTTPS_PROXY") and value:
        if not re.match(r'^(http|https|socks5)://[\w\-\.]+:\d+$', value):
            return False, _t("env.msg.proxy_format", lang)
    
    # 币种格式验证
    if key in ("SYMBOLS_EXTRA", "SYMBOLS_EXCLUDE", "BLOCKED_SYMBOLS") and value:
        symbols = [s.strip().upper() for s in value.split(",") if s.strip()]
        invalid = [s for s in symbols if not re.match(r'^[A-Z0-9]+USDT$', s)]
        if invalid:
            return False, _t("env.msg.symbol_format", lang, invalid=", ".join(invalid))
    
    return True, "OK"
