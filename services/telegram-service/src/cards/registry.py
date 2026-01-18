"""排行榜卡片注册表"""

from __future__ import annotations

import importlib
import logging
import os
import pkgutil
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from cards.base import RankingCard
from cards.i18n import btn as _btn, lang_context, resolve_lang


# 从环境变量读取卡片配置
CARDS_ENABLED = [c.strip().lower() for c in os.environ.get("CARDS_ENABLED", "").split(",") if c.strip()]
CARDS_DISABLED = [c.strip().lower() for c in os.environ.get("CARDS_DISABLED", "").split(",") if c.strip()]


class RankingRegistry:
    """自动扫描并注册排行榜卡片插件"""

    # 黑名单：暂时隐藏的卡片（不出现在菜单，不处理回调）
    # 隐藏/停用的卡片列表
    BLACKLIST = {
        "position_ranking",          # 持仓排行
        "market_depth",              # 市场深度
        "funding_rate",              # 资金费率
        "liquidation_ranking",       # 爆仓排行（兼容旧ID）
        "__disabled_liquidation__",  # 已硬禁用的爆仓卡片
    }

    def __init__(self, package_name: str = "cards") -> None:
        self.package_name = package_name
        self._cards: Dict[str, RankingCard] = {}
        self._logger = logging.getLogger(__name__)
    
    def _is_card_enabled(self, card_id: str) -> bool:
        """检查卡片是否启用"""
        card_id_lower = card_id.lower()
        # 检查禁用列表
        for d in CARDS_DISABLED:
            if d in card_id_lower:
                return False
        # 检查启用列表（空=全部启用）
        if CARDS_ENABLED:
            for e in CARDS_ENABLED:
                if e in card_id_lower:
                    return True
            return False
        return True

    def load_cards(self) -> None:
        """扫描包目录并载入所有卡片"""
        self._cards.clear()
        package = importlib.import_module(self.package_name)
        package_path = Path(package.__file__).resolve().parent

        # 确保 src 包所在的项目根目录在 sys.path 中，避免卡片导入失败
        added_paths: List[str] = []
        parents = package_path.parents
        # parents[3] -> 项目根目录；parents[2] -> src 目录
        for path in (parents[3] if len(parents) > 3 else None, parents[2] if len(parents) > 2 else None):
            if path and str(path) not in sys.path:
                sys.path.insert(0, str(path))
                added_paths.append(str(path))
        if added_paths:
            self._logger.info("🔧 补齐排行榜卡片依赖路径: %s", added_paths)

        for module_info in pkgutil.walk_packages(
            [str(package_path)],
            prefix=f"{self.package_name}."
        ):
            name = module_info.name  # 例如 cards.basic.MACD柱状排行卡片
            short = name.split(".")[-1]

            # 跳过内部模块
            if short.startswith("_") or short in {"base", "registry"}:
                continue

            try:
                module = importlib.import_module(name)
            except Exception as exc:  # pylint: disable=broad-except
                self._logger.error("❌ 加载排行榜模块失败 %s: %s", name, exc)
                continue

            card = getattr(module, "CARD", None)
            if isinstance(card, RankingCard):
                self._hydrate_field_defaults(card)
                self._wrap_field_settings(card)
                if card.card_id in self.BLACKLIST:
                    self._logger.info("⏸️ 已跳过黑名单卡片: %s", card.card_id)
                    continue
                if not self._is_card_enabled(card.card_id):
                    self._logger.info("⏸️ 已跳过禁用卡片: %s", card.card_id)
                    continue
                self.register_card(card)
            else:
                # 仅当是叶子模块才提示，包/__init__ 没导出 CARD 不算错误
                if not module_info.ispkg:
                    self._logger.warning("⚠️ 模块 %s 未导出 CARD 或类型不符", name)

        self._logger.info("✅ 共载入 %d 个排行榜卡片", len(self._cards))

    def register_card(self, card: RankingCard) -> None:
        """注册单个卡片"""
        self._cards[card.card_id] = card

    def card_count(self) -> int:
        return len(self._cards)

    def iter_cards(self) -> Iterable[RankingCard]:
        return self._cards.values()

    def iter_cards_by_category(self, category: str) -> List[RankingCard]:
        cards = [card for card in self._cards.values() if card.category == category]
        cards.sort(key=lambda card: (card.priority, card.button_text))
        return cards

    def find_by_callback(self, callback_data: str) -> Optional[RankingCard]:
        for card in self._cards.values():
            if card.handles_callback(callback_data):
                return card
        return None

    async def dispatch(self, update, context, services: Dict[str, object]) -> bool:
        """根据 callback_data 分发给具体卡片"""
        query = update.callback_query
        if not query:
            return False

        card = self.find_by_callback(query.data)
        if not card:
            # 无操作按钮兜底 (即时响应已在 app.py 统一处理)
            data = query.data or ""
            if data.endswith("nop") or data.endswith("_nop"):
                return True
            return False

        lang = resolve_lang(update)
        with lang_context(lang):
            return await card.handle_callback(update, context, services)

    # ---------- 内部工具 ----------
    def _hydrate_field_defaults(self, card: RankingCard) -> None:
        """
        自动补全卡片 default_state 中的字段开关默认值。
        场景：部分卡片将 `_fields` 默认写成 {}，导致首次进入设置页无状态、回调无效。
        通过调用卡片自身的 `_ensure_field_state` 生成默认状态并回填到 default_state。
        """
        try:
            defaults = getattr(card, "default_state", None)
            if not isinstance(defaults, dict):
                return

            changed = False
            for key, val in list(defaults.items()):
                if not (isinstance(key, str) and key.endswith("_fields")):
                    continue
                if val:  # 已有默认值则保持不动
                    continue
                ensure_fn = getattr(card, "_ensure_field_state", None)
                if not callable(ensure_fn):
                    continue
                dummy = type("DummyHandler", (), {"user_states": {}})()
                state = ensure_fn(dummy)  # type: ignore[arg-type]
                if isinstance(state, dict) and state:
                    defaults[key] = state.copy()
                    changed = True
            if changed:
                self._logger.info("🔧 补全卡片字段默认状态: %s", card.card_id)
        except Exception as exc:  # pragma: no cover - 防御性日志
            self._logger.warning("⚠️ 补全字段默认状态失败 %s: %s", getattr(card, "card_id", "?"), exc)

    # ---------- 统一字段开关迁移到设置页 ----------
    def _wrap_field_settings(self, card: RankingCard) -> None:
        toggle_prefix = self._find_toggle_prefix(card)
        if not toggle_prefix:
            return

        settings_cb, back_cb, fields_key = self._derive_settings_tokens(card, toggle_prefix)
        if not settings_cb or not back_cb or not fields_key:
            return

        for cb in (settings_cb, back_cb):
            if cb not in getattr(card, "callback_prefixes", []):
                card.callback_prefixes.append(cb)

        orig_handle = card.handle_callback
        orig_build_keyboard = getattr(card, "_build_keyboard", None)

        async def handle_wrapper(update, context, services: Dict[str, object]) -> bool:
            query = update.callback_query
            data = query.data if query else ""
            h = services.get("user_handler")
            ensure = services.get("ensure_valid_text")
            user_id = getattr(getattr(query, "from_user", None), "id", None)

            if data == settings_cb:
                await self._render_settings(card, query, h, ensure, back_cb, toggle_prefix)
                try:
                    self._logger.info("⚙️ settings_open card=%s user=%s", card.card_id, user_id)
                except Exception:
                    pass
                return True

            if data == back_cb:
                if hasattr(card, "_edit"):
                    await card._edit(query, h, ensure)  # type: ignore[attr-defined]
                    try:
                        self._logger.info("↩️ settings_back card=%s user=%s", card.card_id, user_id)
                    except Exception:
                        pass
                    return True

            if data.startswith(toggle_prefix):
                if h:
                    state = card._ensure_field_state(h)  # type: ignore[attr-defined]
                    col = data.replace(toggle_prefix, "")
                    if col in state and not getattr(card, "_is_core", lambda _: False)(col):
                        prev = bool(state.get(col, False))
                        state[col] = not prev
                        h.user_states[fields_key] = state
                        try:
                            self._logger.info(
                                "🔀 field_toggle card=%s user=%s field=%s new_state=%s",
                                card.card_id,
                                user_id,
                                col,
                                state[col],
                            )
                        except Exception:
                            pass
                await self._render_settings(card, query, h, ensure, back_cb, toggle_prefix)
                return True

            return await orig_handle(update, context, services)

        card.handle_callback = handle_wrapper  # type: ignore[assignment]

        def keyboard_wrapper(*args: Any, **kwargs: Any):
            if orig_build_keyboard is None:
                return None
            kb = orig_build_keyboard(*args, **kwargs)
            try:
                rows: List[List[InlineKeyboardButton]] = []
                for row in kb.inline_keyboard:  # type: ignore[attr-defined]
                    new_row = [btn for btn in row if not getattr(btn, "callback_data", "").startswith(toggle_prefix)]
                    if new_row:
                        rows.append(new_row)
                rows = self._inject_settings_row(card, rows, settings_cb)
                return InlineKeyboardMarkup(rows)
            except Exception:
                return kb

        if orig_build_keyboard:
            card._build_keyboard = keyboard_wrapper  # type: ignore[assignment]

    async def _render_settings(
        self,
        card: RankingCard,
        query,
        h,
        ensure,
        back_cb: str,
        toggle_prefix: str,
    ) -> None:
        if not query:
            return
        if hasattr(card, "_build_settings_payload"):
            text, kb = await card._build_settings_payload(h, ensure)  # type: ignore[attr-defined]
            await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
            return

        # 传入 query 以便卡片获取用户语言偏好
        text, _ = await card._build_payload(h, ensure, None, query)  # type: ignore[attr-defined]
        settings_kb = self._build_settings_keyboard_generic(card, h, toggle_prefix, back_cb)
        await query.edit_message_text(text, reply_markup=settings_kb, parse_mode="Markdown")

    def _build_settings_keyboard_generic(
        self,
        card: RankingCard,
        h,
        toggle_prefix: str,
        back_cb: str,
    ) -> InlineKeyboardMarkup:
        fields_state = card._ensure_field_state(h)  # type: ignore[attr-defined]

        def _iter_fields(field_list):
            for tpl in field_list:
                if len(tpl) == 3:
                    yield tpl
                elif len(tpl) == 2:
                    col, label = tpl
                    yield col, label, False

        rows: List[List[InlineKeyboardButton]] = []
        for flist in (
            getattr(card, "general_display_fields", []),
            getattr(card, "special_display_fields", []),
        ):
            if not flist:
                continue
            row: List[InlineKeyboardButton] = []
            for col_id, label, is_core in _iter_fields(flist):
                state_on = fields_state.get(col_id, is_core or True)
                show_label = f"✅{label}" if state_on else label
                cb = f"{toggle_prefix}{col_id}"
                row.append(InlineKeyboardButton(show_label, callback_data=cb))
            rows.append(row)

        rows.append([_btn(None, "btn.back", back_cb)])
        return InlineKeyboardMarkup(rows)

    def _inject_settings_row(
        self,
        card: RankingCard,
        rows: List[List[InlineKeyboardButton]],
        settings_cb: str,
    ) -> List[List[InlineKeyboardButton]]:
        for row in rows:
            for btn in row:
                if getattr(btn, "callback_data", "") == settings_cb:
                    return rows

        main_btn = None
        refresh_btn = None
        control_row_idx = None
        for idx, row in enumerate(rows):
            for btn in row:
                data = getattr(btn, "callback_data", "") or ""
                if data in {"ranking_menu", "main_menu"}:
                    main_btn = btn
                if "refresh" in data or data == getattr(card, "card_id", ""):
                    refresh_btn = btn
                    control_row_idx = idx
        if main_btn is None:
            main_btn = _btn(None, "menu.home", "ranking_menu")
        if refresh_btn is None:
            refresh_btn = _btn(None, "btn.refresh", getattr(card, "card_id", "refresh"))

        settings_btn = _btn(None, "btn.settings", settings_cb)

        if control_row_idx is not None:
            row = rows[control_row_idx]
            cbs = [getattr(b, "callback_data", "") for b in row]
            # 目标顺序：主菜单 / ⚙️设置 / 刷新
            # 如果行中已有主菜单和刷新，则重排为 [主菜单, ⚙️设置, 刷新]，保留其他按钮在末尾
            if settings_cb not in cbs and getattr(main_btn, "callback_data", "") in cbs and getattr(refresh_btn, "callback_data", "") in cbs:
                new_row = []
                # 主菜单
                new_row.append(main_btn)
                # 设置
                new_row.append(settings_btn)
                # 刷新
                new_row.append(refresh_btn)
                # 追加其他剩余按钮（保持原顺序且不重复）
                for b in row:
                    cb = getattr(b, "callback_data", "")
                    if cb in {getattr(main_btn, "callback_data", ""), getattr(refresh_btn, "callback_data", ""), settings_cb}:
                        continue
                    new_row.append(b)
                rows[control_row_idx] = new_row
            elif settings_cb not in cbs:
                rows[control_row_idx] = [main_btn, settings_btn, refresh_btn] + [b for b in row if getattr(b, "callback_data", "") not in {getattr(main_btn, "callback_data", ""), getattr(refresh_btn, "callback_data", ""), settings_cb}]
        else:
            rows.append([settings_btn, main_btn, refresh_btn])
        return rows

    @staticmethod
    def _find_toggle_prefix(card: RankingCard) -> Optional[str]:
        for p in getattr(card, "callback_prefixes", []):
            if p.startswith("field_") and p.endswith("_"):
                return p
        return None

    @staticmethod
    def _derive_settings_tokens(card: RankingCard, toggle_prefix: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        base = toggle_prefix.replace("field_", "")
        if "_toggle_" in base:
            base = base.split("_toggle_")[0]
        base = base.rstrip("_")
        if not base:
            return None, None, None
        settings_cb = f"{base}_settings"
        back_cb = f"{base}_settings_back"
        fields_key = None
        for k in getattr(card, "default_state", {}):
            if k.endswith("_fields") and k.startswith(base):
                fields_key = k
                break
        if fields_key is None:
            fields_key = f"{base}_fields"
        return settings_cb, back_cb, fields_key
