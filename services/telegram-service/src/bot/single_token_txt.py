# -*- coding: utf-8 -*-
"""
单币种完整 TXT 导出 - psql 风格表格

触发方式: BTC!! (双感叹号) 或 /export BTC
输出: 4 个面板的完整表格文本
"""
from __future__ import annotations

import unicodedata
from typing import Dict, List, Any, Optional

from cards.data_provider import format_symbol, get_ranking_provider
from cards.i18n import gettext as _t


# ==================== psql 表格格式化 ====================

def _disp_width(text: str) -> int:
    """计算字符串显示宽度（ASCII=1，中文=2）"""
    w = 0
    for ch in text:
        w += 2 if unicodedata.east_asian_width(ch) in {"F", "W"} else 1
    return w


def _pad(text: str, width: int, align: str = "left") -> str:
    """填充字符串到指定显示宽度"""
    pad_len = width - _disp_width(text)
    if pad_len <= 0:
        return text
    if align == "right":
        return " " * pad_len + text
    elif align == "center":
        left = pad_len // 2
        right = pad_len - left
        return " " * left + text + " " * right
    else:  # left
        return text + " " * pad_len


def format_psql_table(headers: List[str], rows: List[List[str]], title: str = None) -> str:
    """
    生成 psql 风格表格
    
    格式:
     Column | Type | Value
    --------+------+-------
     name   | text | hello
     age    | int  | 25
    """
    if not headers:
        return ""

    # 计算每列最大宽度
    col_count = len(headers)
    widths = [_disp_width(h) for h in headers]

    for row in rows:
        for i, cell in enumerate(row[:col_count]):
            widths[i] = max(widths[i], _disp_width(str(cell)))

    # 构建表格
    lines = []

    # 标题
    if title:
        lines.append(f"=== {title} ===")
        lines.append("")

    # 表头
    header_parts = []
    for i, h in enumerate(headers):
        header_parts.append(_pad(h, widths[i], "center" if i == 0 else "center"))
    lines.append(" " + " | ".join(header_parts))

    # 分隔线
    sep_parts = []
    for w in widths:
        sep_parts.append("-" * w)
    lines.append("-" + "-+-".join(sep_parts) + "-")

    # 数据行
    for row in rows:
        row_parts = []
        for i, cell in enumerate(row[:col_count]):
            # 第一列左对齐，其他右对齐
            align = "left" if i == 0 else "right"
            row_parts.append(_pad(str(cell), widths[i], align))
        lines.append(" " + " | ".join(row_parts))

    return "\n".join(lines)


# ==================== 数据格式化 ====================

def fmt_num(val: Any, precision: int = 2) -> str:
    """格式化数值"""
    if val is None or val == "":
        return "-"
    try:
        v = float(val)
        if abs(v) >= 1e9:
            return f"{v/1e9:.{precision}f}B"
        elif abs(v) >= 1e6:
            return f"{v/1e6:.{precision}f}M"
        elif abs(v) >= 1e3:
            return f"{v/1e3:.{precision}f}K"
        elif abs(v) < 0.0001 and v != 0:
            return f"{v:.6f}"
        else:
            return f"{v:.{precision}f}"
    except (ValueError, TypeError):
        return str(val)[:12] if val else "-"


def fmt_pct(val: Any) -> str:
    """格式化百分比"""
    if val is None or val == "":
        return "-"
    try:
        v = float(val)
        return f"{v:.2f}%"
    except (ValueError, TypeError):
        return str(val)[:12] if val else "-"


def fmt_str(val: Any, max_len: int = 10) -> str:
    """格式化字符串，限制长度"""
    if val is None or val == "":
        return "-"
    s = str(val)
    if len(s) > max_len:
        return s[:max_len-2] + ".."
    return s


# ==================== 面板配置 ====================

# 周期列表
ALL_PERIODS = ("1m", "5m", "15m", "1h", "4h", "1d", "1w")
FUTURES_PERIODS = ("5m", "15m", "1h", "4h", "1d", "1w")

# 面板字段配置: 表名 -> [(字段ID, 显示名, 格式化函数)]
PANEL_CONFIG = {
    "basic": {
        "title": "📊 基础指标",
        "tables": {
            "布林带扫描器": [
                ("带宽", "带宽", fmt_num),
                ("百分比b", "%B", fmt_num),
                ("中轨斜率", "中轨斜率", fmt_num),
            ],
            "KDJ随机指标扫描器": [
                ("J值", "J", fmt_num),
                ("K值", "K", fmt_num),
                ("D值", "D", fmt_num),
                ("信号概述", "信号", str),
            ],
            "MACD柱状扫描器": [
                ("MACD", "MACD", fmt_num),
                ("DIF", "DIF", fmt_num),
                ("DEA", "DEA", fmt_num),
                ("信号概述", "信号", str),
            ],
            "智能RSI扫描器": [
                ("RSI均值", "RSI", fmt_num),
                ("信号", "信号", str),
                ("强度", "强度", fmt_num),
            ],
            "OBV能量潮扫描器": [
                ("OBV值", "OBV", fmt_num),
                ("OBV变化率", "变化率", fmt_pct),
            ],
            "成交量比率扫描器": [
                ("量比", "量比", fmt_num),
                ("信号概述", "信号", str),
            ],
        },
    },
    "futures": {
        "title": "📈 期货情绪",
        "periods": FUTURES_PERIODS,
        "tables": {
            "期货情绪聚合表": [
                ("持仓金额", "持仓金额", fmt_num),
                ("持仓变动%", "持仓变动%", fmt_pct),
                ("大户多空比", "大户多空比", fmt_num),
                ("全体多空比", "全体多空比", fmt_num),
                ("主动成交多空比", "主动多空比", fmt_num),
                ("情绪差值", "情绪差值", fmt_num),
                ("信号", "信号", str),
            ],
        },
    },
    "advanced": {
        "title": "🔬 高级指标",
        "tables": {
            "全量支撑阻力扫描器": [
                ("支撑位", "支撑位", fmt_num),
                ("阻力位", "阻力位", fmt_num),
                ("距支撑百分比", "距支撑%", fmt_pct),
                ("距阻力百分比", "距阻力%", fmt_pct),
            ],
            "ATR波幅扫描器": [
                ("ATR百分比", "ATR%", fmt_pct),
                ("波动分类", "波动", str),
            ],
            "流动性扫描器": [
                ("流动性得分", "流动性", fmt_num),
                ("流动性等级", "等级", str),
            ],
            "超级精准趋势扫描器": [
                ("趋势方向", "方向", str),
                ("趋势强度", "强度", fmt_num),
                ("趋势持续根数", "持续", fmt_num),
            ],
            "VWAP离线信号扫描": [
                ("偏离百分比", "VWAP偏离%", fmt_pct),
            ],
        },
    },
    "pattern": {
        "title": "🕯️ K线形态",
        "tables": {
            "K线形态扫描器": [
                ("形态类型", "形态", str),
                ("检测数量", "数量", fmt_num),
                ("强度", "强度", fmt_num),
            ],
        },
    },
}


# ==================== 导出器 ====================

class SingleTokenTxtExporter:
    """单币种完整 TXT 导出器"""

    def __init__(self):
        self.provider = get_ranking_provider()

    def _get_data(self, table: str, symbol: str, period: str) -> Optional[Dict]:
        """获取指定表/币种/周期的数据"""
        try:
            return self.provider.fetch_row(table, period, symbol)
        except Exception:
            return None

    def _render_panel(self, panel_name: str, symbol: str) -> str:
        """渲染单个面板"""
        config = PANEL_CONFIG.get(panel_name)
        if not config:
            return ""

        periods = config.get("periods", ALL_PERIODS)

        # K线形态用竖表（周期作为行）
        if panel_name == "pattern":
            return self._render_pattern_vertical(symbol, periods, config)

        headers = ["指标\\周期"] + list(periods)
        rows = []

        for table_name, fields in config["tables"].items():
            for field_id, display_name, formatter in fields:
                row = [display_name]
                for period in periods:
                    data = self._get_data(table_name, symbol, period)
                    if data:
                        val = data.get(field_id)
                        row.append(formatter(val))
                    else:
                        row.append("-")
                rows.append(row)

        return format_psql_table(headers, rows, config["title"])

    def _render_pattern_vertical(self, symbol: str, periods: tuple, config: dict) -> str:
        """渲染 K线形态竖表（周期作为行）"""
        headers = ["周期", "形态", "数量", "强度"]
        rows = []

        for period in periods:
            data = self._get_data("K线形态扫描器", symbol, period)
            if data:
                pattern = data.get("形态类型", "-")
                # 形态可能很长，截断显示
                if pattern and len(str(pattern)) > 30:
                    pattern = str(pattern)[:28] + ".."
                count = fmt_num(data.get("检测数量"))
                strength = fmt_num(data.get("强度"))
                rows.append([period, str(pattern) if pattern else "-", count, strength])
            else:
                rows.append([period, "-", "-", "-"])

        return format_psql_table(headers, rows, config["title"])

    def export_full(self, symbol: str, lang: str = "zh_CN") -> str:
        """导出完整的 4 面板 TXT"""
        sym = format_symbol(symbol)
        if not sym:
            return _t("snapshot.error.no_symbol", lang=lang)

        sections = [
            f"{'='*50}",
            f"  {_t('export.title', lang=lang, symbol=sym)}",
            f"{'='*50}",
            "",
        ]

        # 4 个面板
        for panel in ["basic", "futures", "advanced", "pattern"]:
            panel_text = self._render_panel(panel, sym)
            if panel_text:
                sections.append(panel_text)
                sections.append("")

        return "\n".join(sections)


# ==================== 便捷函数 ====================

_exporter: Optional[SingleTokenTxtExporter] = None

def get_exporter() -> SingleTokenTxtExporter:
    global _exporter
    if _exporter is None:
        _exporter = SingleTokenTxtExporter()
    return _exporter


def export_single_token_txt(symbol: str) -> str:
    """导出单币种完整 TXT"""
    return get_exporter().export_full(symbol)


__all__ = ["export_single_token_txt", "format_psql_table", "SingleTokenTxtExporter"]
