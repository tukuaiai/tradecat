"""TimescaleDB 适配器 - 支持双模式写入"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
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


@dataclass
class WriteResult:
    """写入结果"""
    success: bool = False
    rows_written: int = 0
    batch_id: Optional[int] = None
    error: Optional[str] = None


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
                    # 使用 sql.Identifier 避免 SQL 注入
                    query = sql.SQL("SELECT {}.start_batch(%s, %s, %s, %s, %s, %s)").format(
                        sql.Identifier(settings.quality_schema)
                    )
                    cur.execute(query, ("binance", data_type, "crypto", None, None, None))
                    result = cur.fetchone()
                    conn.commit()
                    return result[0] if result else 0
        except Exception as e:
            logger.debug("获取 batch_id 失败: %s", e)
            return 0
    
    def _get_batch_id_safe(self, data_type: str) -> Optional[int]:
        """安全获取 batch_id，失败返回 None 而非抛异常 (F-04 修复)"""
        try:
            batch_id = self._get_batch_id(data_type)
            return batch_id if batch_id > 0 else None
        except Exception as e:
            logger.warning("获取 batch_id 失败，将使用 NULL: %s", e)
            return None

    def upsert_candles(self, interval: str, rows: Sequence[dict], batch_size: int = 2000) -> int:
        """
        使用 COPY 命令批量 upsert K线，支持双模式写入。
        
        - raw 模式: 写入 raw.crypto_kline_1m，字段转换 + batch_id
        - legacy 模式: 写入 market_data.candles_1m，保持原字段
        
        Returns:
            写入的行数
        """
        if not rows:
            return 0
        
        interval = normalize_interval(interval)
        
        # 根据模式处理数据 (F-03/F-04: 使用安全的 batch_id 获取)
        if settings.is_raw_mode:
            batch_id = self._get_batch_id_safe("kline") or 0
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

        # 根据模式处理数据 (F-03/F-04: 使用安全的 batch_id 获取)
        if settings.is_raw_mode:
            batch_id = self._get_batch_id_safe("metrics") or 0
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

    def get_symbols(self, exchange: str, interval: str = "1m") -> List[str]:
        """获取交易对列表"""
        interval = normalize_interval(interval)
        table = f"{self.schema}.candles_{interval}"
        # 验证表名 (R2-01 修复)
        from ..config import validate_table_name
        validate_table_name(table)
        
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("SELECT DISTINCT symbol FROM {} WHERE exchange = %s ORDER BY symbol").format(
                        sql.Identifier(self.schema, f"candles_{interval}")
                    ),
                    (exchange,)
                )
                return [r[0] for r in cur.fetchall()]

    def get_counts(self, exchange: str, interval: str, symbols: Sequence[str]) -> Dict[str, int]:
        """获取各交易对数据量"""
        if not symbols:
            return {}
        interval = normalize_interval(interval)
        table = f"{self.schema}.candles_{interval}"
        from ..config import validate_table_name
        validate_table_name(table)
        
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("SELECT symbol, COUNT(*) FROM {} WHERE exchange = %s AND symbol = ANY(%s) GROUP BY symbol").format(
                        sql.Identifier(self.schema, f"candles_{interval}")
                    ),
                    (exchange, list(symbols))
                )
                return {r[0]: r[1] for r in cur.fetchall()}

    def detect_gaps(self, exchange: str, interval: str, symbols: Sequence[str], lookback_min: int = 10080, threshold_sec: int = 120, limit: int = 50) -> List[tuple]:
        """检测数据缺口"""
        interval = normalize_interval(interval)
        table = f"{self.schema}.candles_{interval}"
        from ..config import validate_table_name
        validate_table_name(table)
        
        # 使用参数化查询，lookback_min 和 threshold_sec 是整数，安全
        query = sql.SQL("""
            WITH o AS (
                SELECT symbol, bucket_ts, LEAD(bucket_ts) OVER (PARTITION BY symbol ORDER BY bucket_ts) AS next_ts
                FROM {table} 
                WHERE exchange = %(ex)s AND symbol = ANY(%(sym)s) 
                  AND bucket_ts >= NOW() - INTERVAL '{lookback} minutes'
            )
            SELECT symbol, bucket_ts, next_ts 
            FROM o 
            WHERE next_ts IS NOT NULL AND next_ts - bucket_ts >= INTERVAL '{threshold} seconds' 
            ORDER BY bucket_ts 
            LIMIT %(lim)s
        """).format(
            table=sql.Identifier(self.schema, f"candles_{interval}"),
            lookback=sql.Literal(lookback_min),
            threshold=sql.Literal(threshold_sec)
        )
        
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, {"ex": exchange, "sym": list(symbols), "lim": limit})
                return cur.fetchall()

    def query(self, exchange: str, symbol: str, interval: str, start: Optional[datetime] = None, end: Optional[datetime] = None, limit: int = 1000) -> List[dict]:
        """查询 K 线数据"""
        interval = normalize_interval(interval)
        table = f"{self.schema}.candles_{interval}"
        from ..config import validate_table_name
        validate_table_name(table)
        
        conds = [sql.SQL("exchange = %s"), sql.SQL("symbol = %s")]
        params: list = [exchange, symbol]
        
        if start:
            conds.append(sql.SQL("bucket_ts >= %s"))
            params.append(start)
        if end:
            conds.append(sql.SQL("bucket_ts <= %s"))
            params.append(end)
        params.append(limit)
        
        query = sql.SQL("SELECT * FROM {} WHERE {} ORDER BY bucket_ts DESC LIMIT %s").format(
            sql.Identifier(self.schema, f"candles_{interval}"),
            sql.SQL(" AND ").join(conds)
        )
        
        with self.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(query, params)
                return cur.fetchall()
