#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""排行榜数据访问层

数据源：market_data.db（每个指标一张表）
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional


LOGGER = logging.getLogger(__name__)

# 新旧表名映射
TABLE_NAME_MAP = {
    "基础数据": "基础数据同步器.py",
    "ATR波幅榜单": "ATR波幅扫描器.py",
    "ATR波幅扫描器.py": "ATR波幅扫描器.py",
    "BB榜单": "布林带扫描器.py",
    "布林带榜单": "布林带扫描器.py",
    "布林带扫描器.py": "布林带扫描器.py",
    "CVD榜单": "CVD信号排行榜.py",
    "CVD信号排行榜.py": "CVD信号排行榜.py",
    "KDJ随机指标榜单": "KDJ随机指标扫描器.py",
    "KDJ随机指标扫描器.py": "KDJ随机指标扫描器.py",
    "K线形态榜单": "K线形态扫描器.py",
    "K线形态扫描器.py": "K线形态扫描器.py",
    "MACD柱状榜单": "MACD柱状扫描器.py",
    "MACD柱状扫描器.py": "MACD柱状扫描器.py",
    "MFI资金流量榜单": "MFI资金流量扫描器.py",
    "MFI资金流量扫描器.py": "MFI资金流量扫描器.py",
    "OBV能量潮榜单": "OBV能量潮扫描器.py",
    "OBV能量潮扫描器.py": "OBV能量潮扫描器.py",
    "VPVR榜单": "VPVR排行生成器.py",
    "VPVR排行生成器.py": "VPVR排行生成器.py",
    "VWAP榜单": "VWAP离线信号扫描.py",
    "VWAP离线信号扫描.py": "VWAP离线信号扫描.py",
    "主动买卖比榜单": "主动买卖比扫描器.py",
    "主动买卖比扫描器.py": "主动买卖比扫描器.py",
    "成交量比率榜单": "成交量比率扫描器.py",
    "成交量比率扫描器.py": "成交量比率扫描器.py",
    "支撑阻力榜单": "全量支撑阻力扫描器.py",
    "全量支撑阻力扫描器.py": "全量支撑阻力扫描器.py",
    "收敛发散榜单": "G，C点扫描器.py",
    "G，C点扫描器.py": "G，C点扫描器.py",
    "流动性榜单": "流动性扫描器.py",
    "流动性扫描器.py": "流动性扫描器.py",
    "谐波信号榜单": "谐波信号扫描器.py",
    "谐波信号扫描器.py": "谐波信号扫描器.py",
    "趋势线榜单": "趋势线榜单",
    "布林带扫描器": "布林带扫描器.py",
    "成交量比率扫描器": "成交量比率扫描器.py",
    "主动买卖比扫描器": "主动买卖比扫描器.py",
    "全量支撑阻力扫描器": "全量支撑阻力扫描器.py",
    "KDJ随机指标扫描器": "KDJ随机指标扫描器.py",
    "MACD柱状扫描器": "MACD柱状扫描器.py",
    "OBV能量潮扫描器": "OBV能量潮扫描器.py",
    "谐波信号扫描器": "谐波信号扫描器.py",
    "基础数据同步器": "基础数据同步器.py",
    "G，C点扫描器": "G，C点扫描器.py",
    "流动性扫描器": "流动性扫描器.py",
    "MFI资金流量扫描器": "MFI资金流量扫描器.py",
    "CVD信号排行榜": "CVD信号排行榜.py",
    "VWAP离线信号扫描": "VWAP离线信号扫描.py",
    "VPVR排行生成器": "VPVR排行生成器.py",
    "K线形态扫描器": "K线形态扫描器.py",
    "ATR波幅扫描器": "ATR波幅扫描器.py",
    "大资金操盘扫描器": "大资金操盘扫描器.py",
    "智能RSI扫描器": "智能RSI扫描器.py",
    "超级精准趋势扫描器": "超级精准趋势扫描器.py",
    "趋势线榜单.py": "趋势线榜单.py",
    "期货情绪聚合表": "期货情绪聚合表.py",
    "期货情绪聚合榜单": "期货情绪聚合榜单",
    "期货情绪元数据": "期货情绪元数据",
}


def format_symbol(sym: str) -> str:
    """将交易对显示为基础币种（去除 USDT 后缀），保持大写."""
    s = (sym or "").strip().upper()
    for suffix in ("USDT",):
        if s.endswith(suffix):
            return s[: -len(suffix)] or s
    return s


def _normalize_period_value(period: str) -> str:
    """统一周期表达"""
    p = (period or "").strip().lower()
    alias = {"1d": "24h", "24h": "1d", "1day": "1d", "1w": "1w"}
    return alias.get(p, p)


def _period_to_db(period: str) -> str:
    """将业务周期转为数据库存储格式"""
    p = (period or "").strip().lower()
    return {"24h": "1d", "1day": "1d"}.get(p, p)


# ============================================================
# RankingDataProvider（market_data.db）
# ============================================================
class RankingDataProvider:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        _project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        _default_db = _project_root / "libs" / "database" / "services" / "telegram-service" / "market_data.db"
        self.db_path = db_path or _default_db

    def _connect(self) -> Optional[sqlite3.Connection]:
        if not self.db_path.exists():
            LOGGER.error("market_data.db 不存在: %s", self.db_path)
            return None
        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            for pragma in ("synchronous=OFF", "temp_store=MEMORY", "mmap_size=134217728"):
                try:
                    conn.execute(f"PRAGMA {pragma};")
                except Exception:
                    pass
            return conn
        except Exception as exc:
            LOGGER.error("打开 SQLite 失败: %s", exc)
            return None

    def _resolve_table(self, name: str) -> str:
        return TABLE_NAME_MAP.get(name, name)

    def _load_table(self, table: str) -> List[sqlite3.Row]:
        table = self._resolve_table(table)
        conn = self._connect()
        if conn is None:
            return []
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT * FROM '{table}'")
            return cur.fetchall()
        except Exception as exc:
            LOGGER.warning("读取表 %s 失败: %s", table, exc)
            return []
        finally:
            conn.close()

    def _load_table_period(self, table: str, period: str) -> List[sqlite3.Row]:
        """按周期读取表"""
        table = self._resolve_table(table)
        conn = self._connect()
        if conn is None:
            return []
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            cur.execute(f"PRAGMA table_info('{table}')")
            cols = [row[1] for row in cur.fetchall()]
            period_cols = [c for c in cols if c in ("周期", "period", "PERIOD")]
            if not period_cols:
                cur.execute(f"SELECT * FROM '{table}'")
                return cur.fetchall()

            target = _normalize_period_value(period)
            cand = list({target, target.upper(), period, period.lower(), period.upper()})
            placeholders = ",".join("?" for _ in cand)
            where = " OR ".join([f"{col} IN ({placeholders})" for col in period_cols])
            cur.execute(f"SELECT * FROM '{table}' WHERE {where}", cand * len(period_cols))
            return cur.fetchall()
        except Exception as exc:
            LOGGER.warning("读取表 %s 失败: %s", table, exc)
            return []
        finally:
            conn.close()

    def _fetch_single_row(self, table: str, period: str, symbol: str) -> Dict:
        """按周期+交易对取一行"""
        table = self._resolve_table(table)
        conn = self._connect()
        if conn is None:
            return {}
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        norm_p = _normalize_period_value(period)
        sym_full = symbol.upper()
        sym_with_usdt = sym_full + "USDT"
        try:
            cur.execute(f"PRAGMA table_info('{table}')")
            cols = [row[1] for row in cur.fetchall()]
            period_cols = [c for c in cols if c.lower() in ("周期", "period", "interval")]

            sym_where = """
                (upper(交易对)=? OR replace(upper(交易对),'USDT','')=?
                 OR upper(币种)=? OR upper(symbol)=?)
            """
            sym_params = (sym_with_usdt, sym_full, sym_full, sym_full)

            if period_cols:
                period_vals = (norm_p, period.lower(), period.upper(), period)
                placeholders = ",".join("?" for _ in period_vals)
                period_cond = " OR ".join([f"{col} IN ({placeholders})" for col in period_cols])
                params = period_vals * len(period_cols) + sym_params
                cur.execute(f"""
                    SELECT * FROM '{table}'
                    WHERE ({period_cond}) AND {sym_where}
                    ORDER BY 数据时间 DESC, 时间 DESC, timestamp DESC, rowid DESC
                    LIMIT 1
                """, params)
            else:
                cur.execute(f"""
                    SELECT * FROM '{table}'
                    WHERE {sym_where}
                    ORDER BY 数据时间 DESC, 时间 DESC, timestamp DESC, rowid DESC
                    LIMIT 1
                """, sym_params)
            row = cur.fetchone()
            return dict(row) if row else {}
        except Exception as exc:
            LOGGER.warning("读取表 %s 失败: %s", table, exc)
            return {}
        finally:
            conn.close()

    # ---------------- 公共读取 ----------------
    def fetch_base(self, period: str) -> Dict[str, Dict]:
        """按周期取基础数据"""
        rows = self._load_table_period("基础数据", period)
        target_period = _normalize_period_value(period)
        latest: Dict[str, Dict] = {}
        for row in rows:
            r = dict(row)
            r_period = _normalize_period_value(str(r.get("周期")))
            if r_period != target_period:
                continue
            sym = str(r.get("交易对", "")).upper()
            ts = str(r.get("数据时间", ""))
            if not sym:
                continue
            if sym not in latest or ts > latest[sym].get("数据时间", ""):
                latest[sym] = r
        return latest

    def fetch_metric(self, table: str, period: str) -> List[Dict]:
        """通用指标表读取 - 只取最新一批数据（同一时间戳），每个币种只保留一条"""
        rows = self._load_table_period(table, period)
        target_period = _normalize_period_value(period)
        
        # 第一遍：找出最新时间戳
        max_ts = ""
        for row in rows:
            r = dict(row)
            r_period = _normalize_period_value(str(r.get("周期", "")))
            if r_period != target_period:
                continue
            ts = str(r.get("数据时间", ""))
            if ts > max_ts:
                max_ts = ts
        
        if not max_ts:
            return []
        
        # 第二遍：只取最新时间戳的数据，每个币种只保留一条
        seen = set()
        result = []
        for row in rows:
            r = dict(row)
            r_period = _normalize_period_value(str(r.get("周期", "")))
            if r_period != target_period:
                continue
            ts = str(r.get("数据时间", ""))
            sym = str(r.get("交易对", "")).upper()
            if ts == max_ts and sym not in seen:
                seen.add(sym)
                result.append(r)
        
        return result

    def fetch_base_row(self, period: str, symbol: str) -> Dict:
        return self._fetch_single_row("基础数据", period, symbol)

    def fetch_row(self, table: str, period: str, symbol: str, *,
                  symbol_keys: tuple = ("交易对", "币种", "symbol"),
                  base_fields: Optional[List[str]] = None) -> Dict:
        row = self._fetch_single_row(table, period, symbol)
        if not row:
            return {}
        base = self.fetch_base_row(period, symbol) or {}
        sym = symbol.upper()
        merged = dict(row)
        merged["symbol"] = sym
        merged["price"] = float(base.get("当前价格", row.get("当前价格", 0)) or 0)
        merged["quote_volume"] = float(base.get("成交额", row.get("成交额", 0)) or 0)
        merged["change_percent"] = float(base.get("变化率", 0) or 0)
        merged["updated_at"] = base.get("数据时间") or row.get("数据时间")
        for k in ["振幅", "交易次数", "成交笔数", "主动买入量", "主动卖出量", "主动买额", "主动卖额", "主动买卖比"]:
            if k in base:
                merged[k] = base.get(k)
        if base_fields:
            for bf in base_fields:
                if bf in base:
                    merged[bf] = base.get(bf)
        return merged

    def merge_with_base(self, table: str, period: str,
                        symbol_keys: tuple = ("交易对", "币种", "symbol"),
                        base_fields: Optional[List[str]] = None) -> List[Dict]:
        """合并指标表与基础数据"""
        metrics = self.fetch_metric(table, period)
        if not metrics:
            return []
        base_map = self.fetch_base(period)
        merged: List[Dict] = []
        for r in metrics:
            sym = ""
            for key in symbol_keys:
                val = r.get(key)
                if val:
                    sym = str(val).upper()
                    break
            if not sym:
                continue
            base = base_map.get(sym, {})
            row = dict(r)
            row["symbol"] = sym
            row["price"] = float(base.get("当前价格", r.get("当前价格", 0)) or 0)
            row["quote_volume"] = float(base.get("成交额", r.get("成交额", 0)) or 0)
            row["change_percent"] = float(base.get("变化率", 0) or 0)
            row["updated_at"] = base.get("数据时间") or r.get("数据时间")
            for k in ["振幅", "交易次数", "成交笔数", "主动买入量", "主动卖出量", "主动买额", "主动卖额", "主动买卖比"]:
                if k in base:
                    row[k] = base.get(k)
            if base_fields:
                for bf in base_fields:
                    if bf in base:
                        row[bf] = base.get(bf)
            merged.append(row)
        return merged

    def get_volume_rows(self, period: str) -> List[Dict]:
        metric_rows = self.fetch_metric("Volume", period)
        if not metric_rows:
            return []
        base_map = self.fetch_base(period)
        merged: List[Dict] = []
        for r in metric_rows:
            sym = str(r.get("交易对", "")).upper()
            if not sym:
                continue
            base = base_map.get(sym, {})
            merged.append({
                "symbol": sym,
                "quote_volume": float(base.get("成交额", 0) or 0),
                "base_volume": float(r.get("成交量", 0) or base.get("成交量", 0) or 0),
                "last_close": float(base.get("当前价格", 0) or 0),
                "first_close": float(base.get("开盘价", 0) or 0),
                "change_percent": float(base.get("变化率", 0) or 0) * 100 if abs(float(base.get("变化率", 0) or 0)) < 1 else float(base.get("变化率", 0) or 0),
                "ma5_volume": float(r.get("MA5成交量", 0) or 0),
                "ma20_volume": float(r.get("MA20成交量", 0) or 0),
                "updated_at": base.get("数据时间") or r.get("数据时间"),
            })
        return merged

    def get_atr_rows(self, period: str) -> List[Dict]:
        metrics = self.fetch_metric("ATR波幅榜单", period)
        if not metrics:
            return []
        base_map = self.fetch_base(period)
        out: List[Dict] = []
        for r in metrics:
            sym = str(r.get("交易对", r.get("币种", ""))).upper()
            if not sym:
                continue
            base = base_map.get(sym, {})
            out.append({
                "symbol": sym,
                "strength": float(r.get("强度", 0) or 0),
                "atr_pct": float(r.get("ATR百分比", 0) or 0),
                "price": float(base.get("当前价格", r.get("当前价格", 0)) or 0),
                "category": r.get("波动分类") or "-",
                "quote_volume": float(base.get("成交额", 0) or 0),
                "updated_at": (base.get("数据时间") or r.get("数据时间")),
            })
        return out


_PROVIDER: Optional[RankingDataProvider] = None


def get_ranking_provider() -> RankingDataProvider:
    global _PROVIDER
    if _PROVIDER is None:
        _PROVIDER = RankingDataProvider()
    return _PROVIDER


__all__ = ["RankingDataProvider", "get_ranking_provider", "format_symbol"]
