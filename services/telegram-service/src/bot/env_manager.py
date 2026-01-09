#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境变量管理模块 - 通过 Bot 管理 .env 配置

功能：
- 读取/写入 config/.env 文件
- 白名单控制可修改的配置项
- 支持热更新（修改后立即生效）
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
# =============================================================================
EDITABLE_CONFIGS = {
    # 代理设置
    "HTTP_PROXY": {
        "desc": "HTTP 代理",
        "desc_en": "HTTP Proxy",
        "category": "proxy",
        "hot_reload": False,
        "example": "http://127.0.0.1:7890",
    },
    "HTTPS_PROXY": {
        "desc": "HTTPS 代理",
        "desc_en": "HTTPS Proxy",
        "category": "proxy",
        "hot_reload": False,
        "example": "http://127.0.0.1:7890",
    },
    # 币种管理
    "SYMBOLS_GROUPS": {
        "desc": "币种分组",
        "desc_en": "Symbol Groups",
        "category": "symbols",
        "hot_reload": True,
        "example": "main4",
        "options": ["main4", "main6", "main20", "auto", "all"],
    },
    "SYMBOLS_EXTRA": {
        "desc": "额外添加币种",
        "desc_en": "Extra Symbols",
        "category": "symbols",
        "hot_reload": True,
        "example": "BTCUSDT,ETHUSDT",
    },
    "SYMBOLS_EXCLUDE": {
        "desc": "排除币种",
        "desc_en": "Exclude Symbols",
        "category": "symbols",
        "hot_reload": True,
        "example": "LUNAUSDT",
    },
    "BLOCKED_SYMBOLS": {
        "desc": "屏蔽币种（不显示）",
        "desc_en": "Blocked Symbols",
        "category": "symbols",
        "hot_reload": True,
        "example": "BNXUSDT,ALPACAUSDT",
    },
    # 功能开关
    "DISABLE_SINGLE_TOKEN_QUERY": {
        "desc": "禁用单币查询",
        "desc_en": "Disable Single Token Query",
        "category": "features",
        "hot_reload": True,
        "options": ["0", "1"],
    },
    "BINANCE_API_DISABLED": {
        "desc": "禁用 Binance API",
        "desc_en": "Disable Binance API",
        "category": "features",
        "hot_reload": True,
        "options": ["0", "1"],
    },
    # 展示设置
    "DEFAULT_LOCALE": {
        "desc": "默认语言",
        "desc_en": "Default Language",
        "category": "display",
        "hot_reload": True,
        "options": ["zh-CN", "en"],
    },
    "SNAPSHOT_HIDDEN_FIELDS": {
        "desc": "单币快照隐藏字段",
        "desc_en": "Hidden Fields in Snapshot",
        "category": "display",
        "hot_reload": True,
        "example": "最近翻转时间",
    },
    # 卡片开关
    "CARDS_ENABLED": {
        "desc": "启用的卡片",
        "desc_en": "Enabled Cards",
        "category": "cards",
        "hot_reload": True,
        "example": "资金流向,MACD",
    },
    "CARDS_DISABLED": {
        "desc": "禁用的卡片",
        "desc_en": "Disabled Cards",
        "category": "cards",
        "hot_reload": True,
        "example": "K线形态",
    },
    # 指标开关
    "INDICATORS_ENABLED": {
        "desc": "启用的指标",
        "desc_en": "Enabled Indicators",
        "category": "indicators",
        "hot_reload": False,
        "example": "macd,rsi",
    },
    "INDICATORS_DISABLED": {
        "desc": "禁用的指标",
        "desc_en": "Disabled Indicators",
        "category": "indicators",
        "hot_reload": False,
        "example": "k线形态",
    },
}

# 只读配置（禁止修改）
READONLY_CONFIGS = {
    "BOT_TOKEN", "DATABASE_URL", 
    "BINANCE_API_KEY", "BINANCE_API_SECRET",
    "POSTGRES_PASSWORD", "POSTGRES_USER",
}

# 配置分类
CONFIG_CATEGORIES = {
    "proxy": {"name": "🌐 代理设置", "name_en": "Proxy Settings"},
    "symbols": {"name": "💰 币种管理", "name_en": "Symbol Management"},
    "features": {"name": "⚡ 功能开关", "name_en": "Feature Switches"},
    "display": {"name": "🎨 展示设置", "name_en": "Display Settings"},
    "cards": {"name": "📊 卡片开关", "name_en": "Card Switches"},
    "indicators": {"name": "📈 指标开关", "name_en": "Indicator Switches"},
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
        (success, message)
    """
    # 检查是否允许修改
    if key in READONLY_CONFIGS:
        return False, f"❌ {key} 是只读配置，不允许修改"
    
    if key not in EDITABLE_CONFIGS:
        return False, f"❌ {key} 不在可修改的配置列表中"
    
    # 读取当前文件内容
    if not ENV_PATH.exists():
        return False, f"❌ .env 文件不存在: {ENV_PATH}"
    
    try:
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
        found = False
        new_lines = []
        
        for line in lines:
            stripped = line.strip()
            # 匹配 KEY= 或 KEY =
            if stripped.startswith(f"{key}=") or stripped.startswith(f"{key} ="):
                new_lines.append(f"{key}={value}")
                found = True
            else:
                new_lines.append(line)
        
        # 如果没找到，添加到文件末尾
        if not found:
            new_lines.append(f"{key}={value}")
        
        # 写回文件
        ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        
        # 同步更新当前进程的环境变量
        os.environ[key] = value
        
        # 触发热更新
        config_info = EDITABLE_CONFIGS.get(key, {})
        if config_info.get("hot_reload"):
            _trigger_hot_reload(key)
            return True, f"✅ {key} 已更新为: {value}\n（已热更新，立即生效）"
        else:
            return True, f"✅ {key} 已更新为: {value}\n⚠️ 需要重启服务才能生效"
        
    except PermissionError:
        return False, f"❌ 没有写入权限: {ENV_PATH}"
    except Exception as e:
        logger.error(f"写入 .env 失败: {e}")
        return False, f"❌ 写入失败: {e}"


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
    """验证配置值"""
    config_info = EDITABLE_CONFIGS.get(key)
    if not config_info:
        return False, "未知的配置项"
    
    # 检查选项限制
    options = config_info.get("options")
    if options and value not in options:
        return False, f"值必须是以下之一: {', '.join(options)}"
    
    # 特定配置的格式验证
    if key in ("HTTP_PROXY", "HTTPS_PROXY") and value:
        if not re.match(r'^(http|https|socks5)://[\w\-\.]+:\d+$', value):
            return False, "代理格式应为: http://IP:端口 或 socks5://IP:端口"
    
    if key in ("SYMBOLS_EXTRA", "SYMBOLS_EXCLUDE", "BLOCKED_SYMBOLS") and value:
        # 验证币种格式
        symbols = [s.strip().upper() for s in value.split(",") if s.strip()]
        invalid = [s for s in symbols if not re.match(r'^[A-Z0-9]+USDT$', s)]
        if invalid:
            return False, f"无效的币种格式: {', '.join(invalid)}（应以 USDT 结尾）"
    
    return True, "OK"
