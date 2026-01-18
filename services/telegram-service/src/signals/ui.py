"""
信号开关管理 - 按表开关
"""
import os
import sys
import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from cards.i18n import btn as _btn, gettext as _t, lang_context, resolve_lang, resolve_lang_by_user_id

# 从 signal-service 导入
_SIGNAL_SERVICE_SRC = Path(__file__).resolve().parents[4] / "services" / "signal-service" / "src"
if str(_SIGNAL_SERVICE_SRC) not in sys.path:
    sys.path.insert(0, str(_SIGNAL_SERVICE_SRC))

from rules import RULES_BY_TABLE
from storage.history import SignalHistory, get_history

logger = logging.getLogger(__name__)


def build_binance_url(symbol: str, market: str = "futures") -> str:
    """构造 Binance 跳转链接。默认永续，回退加 USDT。"""
    sym = symbol.upper().replace("/", "")
    if not sym.endswith("USDT"):
        sym = f"{sym}USDT"
    if market == "spot":
        base = sym.replace("USDT", "_USDT", 1)
        return f"https://www.binance.com/en/trade/{base}?type=spot"
    return f"https://www.binance.com/en/futures/{sym}?type=perpetual"

# 数据库路径
_SIGNALS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_SIGNALS_DIR))))
SUBS_DB_PATH = os.path.join(_PROJECT_ROOT, "libs/database/services/telegram-service/signal_subs.db")

# 表名映射为简短名称
TABLE_NAMES = {
    "智能RSI扫描器.py": "RSI",
    "KDJ随机指标扫描器.py": "KDJ",
    "CCI.py": "CCI",
    "WilliamsR.py": "WR",
    "MFI资金流量扫描器.py": "MFI",
    "ADX.py": "ADX",
    "谐波信号扫描器.py": "谐波",
    "SuperTrend.py": "SuperTrend",
    "超级精准趋势扫描器.py": "精准趋势",
    "Ichimoku.py": "一目均衡",
    "零延迟趋势扫描器.py": "零延迟",
    "趋势云反转扫描器.py": "趋势云",
    "趋势线榜单.py": "趋势线",
    "多空信号扫描器.py": "多空信号",
    "量能信号扫描器.py": "量能信号",
    "G，C点扫描器.py": "GC点",
    "布林带扫描器.py": "布林带",
    "ATR波幅扫描器.py": "ATR",
    "Donchian.py": "唐奇安",
    "Keltner.py": "肯特纳",
    "全量支撑阻力扫描器.py": "支撑阻力",
    "VWAP离线信号扫描.py": "VWAP",
    "MACD柱状扫描器.py": "MACD",
    "OBV能量潮扫描器.py": "OBV",
    "CVD信号排行榜.py": "CVD",
    "成交量比率扫描器.py": "量比",
    "主动买卖比扫描器.py": "买卖比",
    "期货情绪聚合表.py": "期货情绪",
    "K线形态扫描器.py": "K线形态",
    "大资金操盘扫描器.py": "SMC智能资金",
    "量能斐波狙击扫描器.py": "斐波那契",
    "VPVR排行生成器.py": "VPVR",
    "流动性扫描器.py": "流动性",
    "剥头皮信号扫描器.py": "剥头皮",
    "基础数据同步器.py": "基础数据",
}

# 所有表
ALL_TABLES = list(RULES_BY_TABLE.keys())

# 内存缓存
_subs: Dict[int, Dict] = {}


def _init_db():
    """初始化订阅数据库"""
    os.makedirs(os.path.dirname(SUBS_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(SUBS_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS signal_subs (
            user_id INTEGER PRIMARY KEY,
            enabled INTEGER DEFAULT 1,
            tables TEXT
        )
    """)
    conn.commit()
    conn.close()


def _load_sub(uid: int) -> Dict:
    """从数据库加载订阅"""
    try:
        conn = sqlite3.connect(SUBS_DB_PATH)
        row = conn.execute("SELECT enabled, tables FROM signal_subs WHERE user_id = ?", (uid,)).fetchone()
        conn.close()
        if row:
            tables = set(json.loads(row[1])) if row[1] else set(ALL_TABLES)
            return {"enabled": bool(row[0]), "tables": tables}
    except Exception as e:
        logger.warning(f"加载订阅失败 uid={uid}: {e}")
    return None


def _save_sub(uid: int, sub: Dict):
    """保存订阅到数据库"""
    try:
        conn = sqlite3.connect(SUBS_DB_PATH)
        conn.execute(
            "INSERT OR REPLACE INTO signal_subs (user_id, enabled, tables) VALUES (?, ?, ?)",
            (uid, int(sub["enabled"]), json.dumps(list(sub["tables"])))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"保存订阅失败 uid={uid}: {e}")


# 初始化数据库
_init_db()


def _get_subscribers() -> list:
    """获取所有启用推送的用户ID列表"""
    try:
        conn = sqlite3.connect(SUBS_DB_PATH)
        rows = conn.execute("SELECT user_id FROM signal_subs WHERE enabled = 1").fetchall()
        conn.close()
        return [r[0] for r in rows]
    except Exception as e:
        logger.warning(f"获取订阅用户失败: {e}")
        return []


def get_sub(uid: int) -> Dict:
    if uid not in _subs:
        # 先从数据库加载
        loaded = _load_sub(uid)
        if loaded:
            _subs[uid] = loaded
        else:
            # 默认开启推送，开启全部信号
            _subs[uid] = {"enabled": True, "tables": set(ALL_TABLES)}
            _save_sub(uid, _subs[uid])
    return _subs[uid]


def get_short_name(table: str) -> str:
    return TABLE_NAMES.get(table, table.replace(".py", "").replace("扫描器", ""))


def get_menu_text(uid: int) -> str:
    sub = get_sub(uid)
    status = "✅ 开启" if sub["enabled"] else "❌ 关闭"
    enabled = len(sub["tables"])
    total = len(ALL_TABLES)

    # 只显示已开启的
    enabled_list = []
    for table in ALL_TABLES:
        if table in sub["tables"]:
            name = get_short_name(table)
            count = len(RULES_BY_TABLE[table])
            enabled_list.append(f"{name} ({count}条)")

    if enabled_list:
        content = "\n".join(enabled_list)
    else:
        content = "暂无开启的信号"

    return f"🔔 信号\n<pre>{content}</pre>\n推送: {status} 已选: {enabled}/{total}"


def get_menu_kb(uid: int, update=None, lang: str | None = None) -> InlineKeyboardMarkup:
    sub = get_sub(uid)
    resolved = resolve_lang(update, lang)
    rows = []

    with lang_context(resolved):
        # 表开关 每行3个，选中的有✅，未选的只有文字
        for i in range(0, len(ALL_TABLES), 3):
            row = []
            for table in ALL_TABLES[i:i+3]:
                name = get_short_name(table)
                if len(name) > 6:
                    name = name[:5] + ".."
                if table in sub["tables"]:
                    row.append(InlineKeyboardButton(f"✅{name}", callback_data=f"sig_t_{table}"))
                else:
                    row.append(InlineKeyboardButton(name, callback_data=f"sig_t_{table}"))
            rows.append(row)

        # 开启/关闭
        if sub["enabled"]:
            rows.append([
                _btn(None, "signal.push.on", "sig_nop", active=True),
                _btn(None, "signal.push.off", "sig_toggle"),
            ])
        else:
            rows.append([
                _btn(None, "signal.push.on", "sig_toggle"),
                _btn(None, "signal.push.off", "sig_nop", active=True),
            ])

        rows.append([_btn(None, "btn.back_home", "main_menu")])

    return InlineKeyboardMarkup(rows)


async def handle(update, context) -> bool:
    """处理 sig_ 开头的回调"""
    q = update.callback_query
    data = q.data
    uid = q.from_user.id

    if not data.startswith("sig_"):
        return False

    # 即时响应已在 app.py 统一处理
    sub = get_sub(uid)

    if data == "sig_toggle":
        sub["enabled"] = not sub["enabled"]
        _save_sub(uid, sub)
    elif data == "sig_all":
        sub["tables"] = set(ALL_TABLES)
        _save_sub(uid, sub)
    elif data == "sig_none":
        sub["tables"] = set()
        _save_sub(uid, sub)
    elif data.startswith("sig_t_"):
        table = data[6:]
        # 白名单验证
        if table not in ALL_TABLES:
            return False
        if table in sub["tables"]:
            sub["tables"].discard(table)
        else:
            sub["tables"].add(table)
        _save_sub(uid, sub)
    elif data == "sig_menu":
        pass
    elif data == "sig_hist_recent":
        # 显示最近信号历史
        text = get_history_text(update=update, limit=20)
        await q.edit_message_text(text, reply_markup=get_history_kb(update=update))
        return True
    elif data == "sig_hist_stats":
        # 显示信号统计
        text = get_history_stats_text(update=update, days=7)
        await q.edit_message_text(text, reply_markup=get_history_kb(update=update))
        return True
    else:
        return False

    await q.edit_message_text(get_menu_text(uid), reply_markup=get_menu_kb(uid, update=update), parse_mode='HTML')
    return True


def is_table_enabled(uid: int, table: str) -> bool:
    """判断表是否启用"""
    sub = get_sub(uid)
    return sub["enabled"] and table in sub["tables"]


def get_signal_push_kb(symbol: str, *, uid: int | None = None, lang: str | None = None) -> InlineKeyboardMarkup:
    """信号推送消息的内联键盘，带币种分析和AI分析跳转"""
    # 去掉USDT后缀用于显示
    coin = symbol.replace("USDT", "")
    if lang is None:
        lang = resolve_lang_by_user_id(uid) if uid is not None else resolve_lang()
    analyze_text = f"🔍 {coin}{_t('btn.analyze', lang=lang)}"
    ai_text = f"🤖 {_t('btn.ai_analyze', lang=lang)}"
    binance_url = build_binance_url(symbol)
    binance_text = _t("btn.binance", lang=lang)
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(analyze_text, callback_data=f"single_query_{symbol}"),
            InlineKeyboardButton(ai_text, callback_data=f"ai_coin_{symbol}"),
            InlineKeyboardButton(binance_text, url=binance_url),
        ],
    ])


def get_history_text(update=None, *, limit: int = 20, symbol: str = None, lang: str | None = None) -> str:
    """获取信号历史文本（国际化）"""
    lang = resolve_lang(update, lang=lang)
    title = _t("signal.history.title", update=update, lang=lang)
    try:
        history = get_history()
        records = history.get_recent(limit=limit, symbol=symbol)
    except Exception as e:
        logger.warning(f"获取历史失败: {e}")
        records = []

    if not records:
        return _t("signal.history.empty", update=update, lang=lang)

    header = _t("signal.history.header", update=update, lang=lang, title=title, count=len(records))
    lines = [header, ""]

    dir_icons = {"BUY": "🟢", "SELL": "🔴", "ALERT": "⚠️"}
    detail_tpl = _t("signal.history.detail", update=update, lang=lang)

    for r in records[:15]:  # 最多显示15条
        ts = r.get("timestamp", "")[:16].replace("T", " ")
        symbol_text = r.get("symbol", "").replace("USDT", "")
        direction = r.get("direction", "")
        signal_type = r.get("signal_type", "")
        strength = r.get("strength", 0)
        icon = dir_icons.get(direction, "📊")

        lines.append(f"{icon} {symbol_text} | {signal_type}")
        try:
            lines.append(detail_tpl.format(time=ts, strength=strength))
        except Exception:
            lines.append(f"{ts} | strength: {strength}")

    if len(records) > 15:
        more = len(records) - 15
        lines.append("")
        lines.append(_t("signal.history.more", update=update, lang=lang, count=more))

    return "\n".join(lines)


def get_history_stats_text(update=None, *, days: int = 7, lang: str | None = None) -> str:
    """获取信号统计文本（国际化）"""
    lang = resolve_lang(update, lang=lang)
    title = _t("signal.stats.title", update=update, lang=lang, days=days)
    try:
        history = get_history()
        stats = history.get_stats(days=days)
    except Exception as e:
        logger.warning(f"获取统计失败: {e}")
        return _t("signal.stats.empty", update=update, lang=lang)

    if not stats or stats.get("total", 0) <= 0:
        return _t("signal.stats.empty", update=update, lang=lang)

    lines = [title, ""]
    lines.append(_t("signal.stats.total", update=update, lang=lang, total=stats["total"]))

    if stats.get("by_direction"):
        dir_icons = {"BUY": "🟢", "SELL": "🔴", "ALERT": "⚠️"}
        dir_text = " | ".join([f"{dir_icons.get(k, '')} {k}: {v}" for k, v in stats["by_direction"].items()])
        lines.append(_t("signal.stats.direction", update=update, lang=lang, text=dir_text))

    if stats.get("by_source"):
        src_text = " | ".join([f"{k}: {v}" for k, v in stats["by_source"].items()])
        lines.append(_t("signal.stats.source", update=update, lang=lang, text=src_text))

    if stats.get("by_symbol"):
        lines.append("")
        lines.append(_t("signal.stats.top", update=update, lang=lang))
        for item in stats["by_symbol"][:5]:
            sym = item["symbol"].replace("USDT", "")
            lines.append(_t("signal.stats.symbol_line", update=update, lang=lang, symbol=sym, count=item["count"]))

    return "\n".join(lines)


def get_history_kb(update=None) -> InlineKeyboardMarkup:
    """信号历史查询键盘（国际化）"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(_t("btn.history_recent", update=update), callback_data="sig_hist_recent"),
            InlineKeyboardButton(_t("btn.stats", update=update), callback_data="sig_hist_stats"),
        ],
        [_btn(update, "btn.back_home", "main_menu")]
    ])
