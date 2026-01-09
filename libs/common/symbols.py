"""币种管理模块

统一的币种过滤逻辑，供所有服务使用。
读取环境变量：SYMBOLS_GROUPS, SYMBOLS_GROUP_*, SYMBOLS_EXTRA, SYMBOLS_EXCLUDE
"""
import os
from typing import List, Optional, Set


def _parse_list(val: str) -> List[str]:
    """解析逗号分隔的列表"""
    return [s.strip().upper() for s in val.split(",") if s.strip()]


def _load_symbol_groups() -> dict:
    """从环境变量加载所有分组"""
    groups = {}
    for key, val in os.environ.items():
        if key.startswith("SYMBOLS_GROUP_") and val:
            name = key[14:].lower()
            groups[name] = _parse_list(val)
    return groups


def get_configured_symbols() -> Optional[List[str]]:
    """
    根据环境变量获取币种列表
    
    Returns:
        List[str]: 配置的币种列表
        None: 使用 auto/all 模式，由调用方决定具体币种
    """
    groups_str = os.environ.get("SYMBOLS_GROUPS", "auto")
    extra = _parse_list(os.environ.get("SYMBOLS_EXTRA", ""))
    exclude = set(_parse_list(os.environ.get("SYMBOLS_EXCLUDE", "")))
    
    selected_groups = [g.strip().lower() for g in groups_str.split(",") if g.strip()]
    
    # auto/all 返回 None
    if "auto" in selected_groups or "all" in selected_groups:
        return None
    
    # 加载分组
    all_groups = _load_symbol_groups()
    symbols = set()
    for g in selected_groups:
        if g in all_groups:
            symbols.update(all_groups[g])
    
    symbols.update(extra)
    symbols -= exclude
    
    return sorted(symbols) if symbols else None


def get_configured_symbols_set() -> Optional[Set[str]]:
    """
    根据环境变量获取币种集合（用于过滤）
    
    Returns:
        Set[str]: 配置的币种集合
        None: 使用 auto/all 模式，不过滤
    """
    result = get_configured_symbols()
    return set(result) if result else None


def reload_symbols():
    """
    强制重新加载币种配置（用于热更新）
    
    注意：此函数本身不缓存，每次调用 get_configured_symbols() 都会重新读取环境变量。
    此函数主要用于通知依赖模块（如 data_provider）刷新其缓存。
    """
    # symbols.py 本身每次都从 os.environ 读取，无需清理
    # 但需要通知其他模块刷新缓存
    pass
