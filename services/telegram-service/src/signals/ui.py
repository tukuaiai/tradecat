"""
信号开关管理 - 按表开关
"""
import os
import json
import sqlite3
import logging
from typing import Dict
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from cards.i18n import btn as _btn, resolve_lang, gettext as _t

from .rules import RULES_BY_TABLE

logger = logging.getLogger(__name__)

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


def get_menu_text(uid: int, lang: str = "zh_CN") -> str:
    sub = get_sub(uid)
    status = _t("signal.status_on", None, lang=lang) if sub["enabled"] else _t("signal.status_off", None, lang=lang)
    enabled = len(sub["tables"])
    total = len(ALL_TABLES)

    # 只显示已开启的
    enabled_list = []
    for table in ALL_TABLES:
        if table in sub["tables"]:
            name = get_short_name(table)
            count = len(RULES_BY_TABLE[table])
            enabled_list.append(f"{name} ({_t('signal.rules_count', None, lang=lang).format(count=count)})")

    if enabled_list:
        content = "\n".join(enabled_list)
    else:
        content = _t("signal.no_enabled", None, lang=lang)

    title = _t("signal.menu_title", None, lang=lang)
    push = _t("signal.menu_push", None, lang=lang)
    selected = _t("signal.menu_selected", None, lang=lang)
    return f"{title}\n<pre>{content}</pre>\n{push}: {status} {selected}: {enabled}/{total}"


def get_menu_kb(uid: int) -> InlineKeyboardMarkup:
    sub = get_sub(uid)
    resolve_lang()
    rows = []

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

    await q.answer()
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
    else:
        return False

    await q.edit_message_text(get_menu_text(uid), reply_markup=get_menu_kb(uid), parse_mode='HTML')
    return True


def is_table_enabled(uid: int, table: str) -> bool:
    """判断表是否启用"""
    sub = get_sub(uid)
    return sub["enabled"] and table in sub["tables"]


def get_signal_push_kb(symbol: str, lang: str = "zh_CN") -> InlineKeyboardMarkup:
    """信号推送消息的内联键盘，带币种分析和AI分析跳转"""
    # 去掉USDT后缀用于显示
    coin = symbol.replace("USDT", "")
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(_t("signal.btn_analysis", None, lang=lang).format(coin=coin), callback_data=f"single_query_{symbol}"),
            InlineKeyboardButton(_t("signal.btn_ai", None, lang=lang), callback_data=f"ai_coin_{symbol}"),
        ]
    ])
