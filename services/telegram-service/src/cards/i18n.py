"""排行榜卡片与信号模块的轻量 i18n 辅助。

复用全局 gettext 配置，并按用户/Telegram 语言选择翻译。
仅做只读操作，不写入用户偏好文件。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from telegram import InlineKeyboardButton

from libs.common.i18n import build_i18n_from_env

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCALE_STORE = PROJECT_ROOT / "data" / "user_locale.json"
I18N = build_i18n_from_env()

_user_locale_map: dict[str, str] = {}

def _load_user_locale_map() -> dict[str, str]:
    global _user_locale_map
    if _user_locale_map:
        return _user_locale_map
    if LOCALE_STORE.exists():
        try:
            _user_locale_map = json.loads(LOCALE_STORE.read_text(encoding="utf-8"))
        except Exception:
            _user_locale_map = {}
    else:
        _user_locale_map = {}
    return _user_locale_map


def resolve_lang(update=None, lang: Optional[str] = None) -> str:
    """解析语言：显式 lang > 用户偏好文件 > Telegram 语言 > 默认。"""
    if lang:
        return I18N.resolve(lang)
    _load_user_locale_map()
    user_id = getattr(getattr(update, "effective_user", None), "id", None)
    if user_id is not None:
        pref = _user_locale_map.get(str(user_id))
        if pref:
            return I18N.resolve(pref)
    tg_lang = getattr(getattr(update, "effective_user", None), "language_code", None)
    if tg_lang:
        return I18N.resolve(tg_lang)
    return I18N.resolve(None)


def gettext(message_id: str, update=None, lang: Optional[str] = None, **kwargs) -> str:
    resolved = resolve_lang(update, lang)
    try:
        return I18N.gettext(message_id, lang=resolved, **kwargs)
    except Exception:
        return message_id


def btn(update, key: str, callback: str, *, active: bool = False, prefix: str = "✅") -> InlineKeyboardButton:
    text = gettext(key, update=update)
    if active and prefix:
        text = f"{prefix}{text}"
    return InlineKeyboardButton(text, callback_data=callback)

BUTTON_KEY_MAP = {
    "排序": "card.common.sort",
    "降序": "btn.sort.desc",
    "升序": "btn.sort.asc",
    "10条": "btn.limit.10",
    "20条": "btn.limit.20",
    "30条": "btn.limit.30",
    "现货": "market.spot",
    "期货": "market.futures",
    "🏠主菜单": "menu.home",
    "🏠 返回": "btn.back_home",
    "⬅️ 返回": "btn.back",
    "返回": "btn.back",
    "🔄刷新": "btn.refresh",
    "刷新": "btn.refresh",
    "⚙️设置": "btn.settings",
    "设置": "btn.settings",
    "开启推送": "signal.push.on",
    "关闭推送": "signal.push.off",
    "开启": "signal.push.on",
    "关闭": "signal.push.off",
}


def btn_auto(update, label: str, callback: str, *, active: bool = False, prefix: str = "✅") -> InlineKeyboardButton:
    """根据常见中文标签自动映射到词条；未命中则回退原文。"""
    key = BUTTON_KEY_MAP.get(label)
    if key:
        text = gettext(key, update=update)
    else:
        # 若传入的 label 本身是 key（带 .），尝试翻译；否则原文回退
        text = gettext(label, update=update) if "." in label else label
    if active and prefix:
        text = f"{prefix}{text}"
    return InlineKeyboardButton(text, callback_data=callback)


__all__ = ["gettext", "btn", "btn_auto", "resolve_lang", "I18N"]
