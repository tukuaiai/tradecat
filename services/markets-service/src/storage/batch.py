"""质量血缘批次管理"""
from __future__ import annotations

from typing import Optional

from psycopg_pool import ConnectionPool

from config import settings

_pool = ConnectionPool(settings.database_url, min_size=1, max_size=3, timeout=10.0)


def start_batch(source: str, data_type: str, market: Optional[str] = None,
                symbol: Optional[str] = None, t_start=None, t_end=None) -> int:
    """
    调用 quality.start_batch() 获取批次 ID。
    若函数不存在则回退为 0。
    """
    sql = f"SELECT {settings.quality_schema}.start_batch(%s,%s,%s,%s,%s,%s)"
    try:
        with _pool.connection() as conn, conn.cursor() as cur:
            cur.execute(sql, (source, data_type, market, symbol, t_start, t_end))
            bid = cur.fetchone()[0]
            conn.commit()
            return int(bid)
    except Exception:
        return 0
