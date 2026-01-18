"""指标数据路由"""

import sqlite3

from fastapi import APIRouter, Query

from src.config import get_settings
from src.utils.errors import ErrorCode, api_response, error_response
from src.utils.symbol import normalize_symbol

router = APIRouter(tags=["indicator"])


@router.get("/indicator/list")
async def get_indicator_list() -> dict:
    """获取可用的指标表列表"""
    settings = get_settings()
    db_path = settings.SQLITE_INDICATORS_PATH

    if not db_path.exists():
        return error_response(ErrorCode.SERVICE_UNAVAILABLE, "指标数据库不可用")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        rows = cursor.fetchall()
        conn.close()

        tables = [row[0] for row in rows]
        return api_response(tables)
    except Exception as e:
        return error_response(ErrorCode.INTERNAL_ERROR, f"查询失败: {e}")


@router.get("/indicator/data")
async def get_indicator_data(
    table: str = Query(..., description="指标表名"),
    symbol: str | None = Query(default=None, description="交易对"),
    interval: str | None = Query(default=None, description="周期"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回数量"),
) -> dict:
    """获取指标数据"""
    settings = get_settings()
    db_path = settings.SQLITE_INDICATORS_PATH

    if not db_path.exists():
        return error_response(ErrorCode.SERVICE_UNAVAILABLE, "指标数据库不可用")

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if not cursor.fetchone():
            conn.close()
            return error_response(ErrorCode.TABLE_NOT_FOUND, f"表 '{table}' 不存在")

        # 构建查询
        query = f'SELECT * FROM "{table}"'
        params: list = []
        conditions = []

        if symbol:
            conditions.append('"交易对" = ?')
            params.append(normalize_symbol(symbol))

        if interval:
            conditions.append('"周期" = ?')
            params.append(interval)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += f" LIMIT {limit}"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        data = [dict(row) for row in rows]
        return api_response(data)
    except Exception as e:
        return error_response(ErrorCode.INTERNAL_ERROR, f"查询失败: {e}")
