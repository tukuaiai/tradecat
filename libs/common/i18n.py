"""轻量级 i18n 工具

提供统一的语言规范化、翻译加载与占位符格式化。
默认使用 gettext，若缺少翻译文件则安全回退到源文案。
"""

from __future__ import annotations

import gettext
import os
import logging
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional

# ==================== 路径与默认配置 ====================
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOCALE_DIR = REPO_ROOT / "services" / "telegram-service" / "locales"
logger = logging.getLogger(__name__)


def normalize_locale(lang: Optional[str]) -> Optional[str]:
    """标准化语言代码，形如 zh-CN / en -> zh_CN / en。

    返回值用于 gettext 目录命名。
    """
    if not lang:
        return None
    code = lang.strip().replace("-", "_")
    if not code:
        return None
    parts = code.split("_", 1)
    if len(parts) == 1:
        return parts[0].lower()
    return f"{parts[0].lower()}_{parts[1].upper()}"


def parse_supported_locales(raw: Optional[str]) -> list[str]:
    """从环境变量解析支持的语言列表。"""
    if not raw:
        return []
    locales: list[str] = []
    for item in raw.split(","):
        norm = normalize_locale(item)
        if norm:
            locales.append(norm)
    return locales


class I18nService:
    """gettext 封装器"""

    def __init__(
        self,
        *,
        locale_dir: Path | str = DEFAULT_LOCALE_DIR,
        domain: str = "bot",
        default_locale: Optional[str] = "en",
        fallback_locale: Optional[str] = None,
        supported_locales: Optional[Iterable[str]] = None,
    ) -> None:
        self.locale_dir = Path(locale_dir)
        self.domain = domain
        self.default_locale = normalize_locale(default_locale) or "en"
        self.fallback_locale = normalize_locale(fallback_locale) or self.default_locale
        parsed = [normalize_locale(x) for x in (supported_locales or []) if normalize_locale(x)]
        self.supported_locales = parsed or [self.default_locale, "en"]
        self._missing_keys: set[tuple[str, str]] = set()

        if not self.locale_dir.exists():
            self.locale_dir.mkdir(parents=True, exist_ok=True)

    # ---------- 语言解析 ----------
    def resolve(self, lang: Optional[str]) -> str:
        """选择最合适的语言，不在列表则回退。"""
        norm = normalize_locale(lang)
        if norm and norm in self.supported_locales:
            return norm
        return self.default_locale if self.default_locale in self.supported_locales else self.supported_locales[0]

    # ---------- 翻译对象 ----------
    @lru_cache(maxsize=16)
    def _translation(self, lang: str):
        return gettext.translation(
            self.domain,
            localedir=str(self.locale_dir),
            languages=[lang, self.fallback_locale],
            fallback=True,
        )

    def gettext(self, message_id: str, lang: Optional[str] = None, **kwargs) -> str:
        """获取翻译并格式化占位符。"""
        resolved = self.resolve(lang)
        text = self._translation(resolved).gettext(message_id)
        if text == message_id:
            # 只记录一次缺失键，避免日志风暴
            key = (resolved, message_id)
            if key not in self._missing_keys:
                self._missing_keys.add(key)
                logger.warning("⚠️ 缺失翻译键: lang=%s key=%s", resolved, message_id)
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

    def get_lazy(self, lang: Optional[str] = None):
        """返回局部绑定语言的 gettext 函数。"""
        def _inner(message_id: str, **kwargs):
            return self.gettext(message_id, lang=lang, **kwargs)

        return _inner


def build_i18n_from_env(locale_dir: Path | str = DEFAULT_LOCALE_DIR) -> I18nService:
    """按环境变量构造 I18nService。"""
    default_locale = os.getenv("DEFAULT_LOCALE", "en")
    fallback_locale = os.getenv("FALLBACK_LOCALE", default_locale)
    supported_locales = parse_supported_locales(os.getenv("SUPPORTED_LOCALES", "zh-CN,en"))
    return I18nService(
        locale_dir=locale_dir,
        domain="bot",
        default_locale=default_locale,
        fallback_locale=fallback_locale,
        supported_locales=supported_locales,
    )


__all__ = [
    "I18nService",
    "build_i18n_from_env",
    "normalize_locale",
    "parse_supported_locales",
]
