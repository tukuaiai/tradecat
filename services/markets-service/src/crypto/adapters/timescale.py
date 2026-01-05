"""TimescaleDB 适配器 - 支持双模式写入"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Iterator, List, Optional, Sequence

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from psycopg import sql

from ..config import settings, normalize_interval
from ..schema_adapter import (
    KlineAdapter, MetricsAdapter,
    get_kline_table, get_metrics_table,
    get_kline_conflict_keys, get_metrics_conflict_keys,
    get_kline_time_field, get_metrics_time_field,
)

logger = logging.getLogger(__name__)


class TimescaleAdapter:
    """TimescaleDB 操作"""

    def __init__(self, db_url: Optional[str] = None, schema: Optional[str] = None,
                 pool_min: int = 2, pool_max: int = 10, timeout: float = 30.0):
        self.db_url = db_url or settings.database_url
        self.schema = schema or settings.db_schema
        self._pool_min = pool_min
        self._pool_max = pool_max
        self._timeout = timeout
        self._pool: Optional[ConnectionPool] = None

    @property
    def pool(self) -> ConnectionPool:
        if self._pool is None:
            self._pool = ConnectionPool(
                self.db_url,
                min_size=self._pool_min,
                max_size=self._pool_max,
                timeout=self._timeout,  # 获取连接超时
                max_idle=300,           # 空闲连接最大存活 5 分钟
                max_lifetime=3600,      # 连接最大存活 1 小时
            )
        return self._pool

    def close(self) -> None:
        if self._pool:
            self._pool.close()
            self._pool = None

    @contextmanager
    def connection(self) -> Iterator:
        with self.pool.connection() as conn:
            yield conn

    def _get_batch_id(self, data_type: str) -> int:
        """获取批次 ID (仅 raw 模式需要)"""
        if not settings.is_raw_mode:
            return 0
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT {settings.quality_schema}.start_batch(%s, %s, %s, %s, %s, %s)",
                        ("binance", data_type, "crypto", None, None, None)
                    )
                    result = cur.fetchone()
                    conn.commit()
                    return result[0] if result else 0
        except Exception as e:
            logger.debug("获取 batch_id 失败: %s", e)
            return 0

    def upsert_candles(self, interval: str, rows: Sequence[dict], batch_size: int = 2000) -> int:
        """
        使用 COPY 命令批量 upsert K线，支持双模式写入。
        
        - raw 模式: 写入 raw.crypto_kline_1m，字段转换 + batch_id
        - legacy 模式: 写入 market_data.candles_1m，保持原字段
        """
        if not rows:
            return 0
        
        interval = normalize_interval(interval)
        
        # 根据模式处理数据
        if settings.is_raw_mode:
            batch_id = self._get_batch_id("kline")
            rows = KlineAdapter.to_new_schema(rows, batch_id)
            table_name = get_kline_table(interval)
            conflict_keys = get_kline_conflict_keys()
            time_field = "open_time"
        else:
            table_name = f"{self.schema}.candles_{interval}"
            conflict_keys = ("exchange", "symbol", "bucket_ts")
            time_field = "bucket_ts"
        
        cols = list(rows[0].keys())
        
        # 确保关键列存在
        if time_field not in cols or "symbol" not in cols or "exchange" not in cols:
            raise ValueError(f"Rows must contain {time_field}, symbol, and exchange")

        temp_table_name = f"temp_candles_{int(datetime.now().timestamp() * 1000)}"
        
        # 解析 schema 和 table
        if "." in table_name:
            schema_name, tbl_name = table_name.split(".", 1)
        else:
            schema_name, tbl_name = self.schema, table_name

        sql_create_temp = sql.SQL("""
            CREATE TEMP TABLE {temp_table} (LIKE {target_table} INCLUDING DEFAULTS)
            ON COMMIT DROP;
        """).format(
            temp_table=sql.Identifier(temp_table_name),
            target_table=sql.Identifier(schema_name, tbl_name)
        )

        # ON CONFLICT 更新的列（排除冲突键）
        update_cols = [col for col in cols if col not in conflict_keys]
        
        # 构建 ON CONFLICT 子句
        conflict_clause = sql.SQL("({})").format(
            sql.SQL(", ").join(map(sql.Identifier, conflict_keys))
        )
        
        sql_upsert_from_temp = sql.SQL("""
            INSERT INTO {target_table} ({cols})
            SELECT {cols} FROM {temp_table}
            ON CONFLICT {conflict} DO UPDATE SET
                {update_assignments},
                updated_at = NOW();
        """).format(
            target_table=sql.Identifier(schema_name, tbl_name),
            cols=sql.SQL(", ").join(map(sql.Identifier, cols)),
            temp_table=sql.Identifier(temp_table_name),
            conflict=conflict_clause,
            update_assignments=sql.SQL(", ").join(
                sql.SQL("{col} = EXCLUDED.{col}").format(col=sql.Identifier(col))
                for col in update_cols
            )
        )

        total_inserted = 0
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_create_temp)
                
                # 分批处理
                for i in range(0, len(rows), batch_size):
                    batch = rows[i:i + batch_size]
                    
                    # 使用 COPY 命令高效写入临时表
                    with cur.copy(sql.SQL("COPY {temp_table} ({cols}) FROM STDIN").format(
                        temp_table=sql.Identifier(temp_table_name),
                        cols=sql.SQL(", ").join(map(sql.Identifier, cols))
                    )) as copy:
                        for row in batch:
                            copy.write_row(tuple(row.get(col) for col in cols))
                
                # 从临时表一次性 upsert 到目标表
                cur.execute(sql_upsert_from_temp)
                total_inserted = cur.rowcount if cur.rowcount > 0 else len(rows)

            conn.commit()
            
        return total_inserted

    def upsert_metrics(self, rows: Sequence[dict], batch_size: int = 2000) -> int:
        """使用 COPY 命令批量 upsert 指标数据，支持双模式写入。"""
        if not rows:
            return 0

        # 根据模式处理数据
        if settings.is_raw_mode:
            batch_id = self._get_batch_id("metrics")
            rows = MetricsAdapter.to_new_schema(rows, batch_id)
            table_name = get_metrics_table()
            conflict_keys = get_metrics_conflict_keys()
        else:
            table_name = f"{self.schema}.binance_futures_metrics_5m"
            conflict_keys = ("symbol", "create_time")
        
        cols = list(rows[0].keys())
        
        # 检查时间字段 (raw 模式用 timestamp，legacy 用 create_time)
        time_field = "timestamp" if settings.is_raw_mode else "create_time"
        if time_field not in cols or "symbol" not in cols:
            raise ValueError(f"Rows must contain {time_field} and symbol")

        temp_table_name = f"temp_metrics_{int(datetime.now().timestamp() * 1000)}"
        
        # 解析 schema 和 table
        if "." in table_name:
            schema_name, tbl_name = table_name.split(".", 1)
        else:
            schema_name, tbl_name = self.schema, table_name

        sql_create_temp = sql.SQL("""
            CREATE TEMP TABLE {temp_table} (LIKE {target_table} INCLUDING DEFAULTS)
            ON COMMIT DROP;
        """).format(
            temp_table=sql.Identifier(temp_table_name),
            target_table=sql.Identifier(schema_name, tbl_name)
        )
        
        update_cols = [col for col in cols if col not in conflict_keys]
        
        # 构建 ON CONFLICT 子句
        conflict_clause = sql.SQL("({})").format(
            sql.SQL(", ").join(map(sql.Identifier, conflict_keys))
        )
        
        sql_upsert_from_temp = sql.SQL("""
            INSERT INTO {target_table} ({cols})
            SELECT {cols} FROM {temp_table}
            ON CONFLICT {conflict} DO UPDATE SET
                {update_assignments},
                updated_at = NOW();
        """).format(
            target_table=sql.Identifier(schema_name, tbl_name),
            cols=sql.SQL(", ").join(map(sql.Identifier, cols)),
            temp_table=sql.Identifier(temp_table_name),
            conflict=conflict_clause,
            update_assignments=sql.SQL(", ").join(
                sql.SQL("{col} = EXCLUDED.{col}").format(col=sql.Identifier(col))
                for col in update_cols
            )
        )

        total_inserted = 0
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_create_temp)
                
                for i in range(0, len(rows), batch_size):
                    batch = rows[i:i + batch_size]
                    with cur.copy(sql.SQL("COPY {temp_table} ({cols}) FROM STDIN").format(
                        temp_table=sql.Identifier(temp_table_name),
                        cols=sql.SQL(", ").join(map(sql.Identifier, cols))
                    )) as copy:
                        for row in batch:
                            copy.write_row(tuple(row.get(col) for col in cols))
                
                cur.execute(sql_upsert_from_temp)
                total_inserted = cur.rowcount if cur.rowcount > 0 else len(rows)

            conn.commit()
            
        return total_inserted
    
    def _quote_val(self, v) -> str:
        """SQL 值转义 (在此重构中已不再需要，保留以兼容旧代码)"""
        if v is None:
            return "NULL"
        if isinstance(v, str):
            return f"'{v.replace(chr(39), chr(39)+chr(39))}'"
        if isinstance(v, datetime):
            return f"'{v.isoformat()}'"
        if isinstance(v, bool):
            return "TRUE" if v else "FALSE"
        # Decimal, int, float 都直接转 str
        return str(v)

    def get_symbols(self, exchange: str, interval: str = "1m") -> List[str]:
        table = f"{self.schema}.candles_{normalize_interval(interval)}"
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT DISTINCT symbol FROM {table} WHERE exchange = %s ORDER BY symbol", (exchange,))
                return [r[0] for r in cur.fetchall()]

    def get_counts(self, exchange: str, interval: str, symbols: Sequence[str]) -> Dict[str, int]:
        if not symbols:
            return {}
        table = f"{self.schema}.candles_{normalize_interval(interval)}"
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT symbol, COUNT(*) FROM {table} WHERE exchange = %s AND symbol = ANY(%s) GROUP BY symbol", (exchange, list(symbols)))
                return {r[0]: r[1] for r in cur.fetchall()}

    def detect_gaps(self, exchange: str, interval: str, symbols: Sequence[str], lookback_min: int = 10080, threshold_sec: int = 120, limit: int = 50) -> List[tuple]:
        table = f"{self.schema}.candles_{normalize_interval(interval)}"
        sql = f"""
            WITH o AS (SELECT symbol, bucket_ts, LEAD(bucket_ts) OVER (PARTITION BY symbol ORDER BY bucket_ts) AS next_ts
                       FROM {table} WHERE exchange = %(ex)s AND symbol = ANY(%(sym)s) AND bucket_ts >= NOW() - INTERVAL '{lookback_min} minutes')
            SELECT symbol, bucket_ts, next_ts FROM o WHERE next_ts IS NOT NULL AND next_ts - bucket_ts >= INTERVAL '{threshold_sec} seconds' ORDER BY bucket_ts LIMIT %(lim)s
        """
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, {"ex": exchange, "sym": list(symbols), "lim": limit})
                return cur.fetchall()

    def query(self, exchange: str, symbol: str, interval: str, start: Optional[datetime] = None, end: Optional[datetime] = None, limit: int = 1000) -> List[dict]:
        table = f"{self.schema}.candles_{normalize_interval(interval)}"
        conds, params = ["exchange = %s", "symbol = %s"], [exchange, symbol]
        if start:
            conds.append("bucket_ts >= %s"); params.append(start)
        if end:
            conds.append("bucket_ts <= %s"); params.append(end)
        params.append(limit)
        with self.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(f"SELECT * FROM {table} WHERE {' AND '.join(conds)} ORDER BY bucket_ts DESC LIMIT %s", params)
                return cur.fetchall()
