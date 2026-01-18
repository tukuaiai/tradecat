"""支持币种路由 (对齐 CoinGlass /api/futures/supported-coins)"""

import sqlite3
import sys
from pathlib import Path

from fastapi import APIRouter

from src.config import get_settings
from src.utils.errors import ErrorCode, api_response, error_response
from src.utils.symbol import to_base_symbol

# 添加 libs/common 到路径以使用全局币种管理
libs_path = Path(__file__).parent.parent.parent.parent.parent / "libs" / "common"
if str(libs_path) not in sys.path:
    sys.path.insert(0, str(libs_path))

from symbols import get_configured_symbols

router = APIRouter(tags=["futures"])


@router.get("/supported-coins")
async def get_supported_coins() -> dict:
    """获取支持的币种列表 (继承全局 SYMBOLS_GROUPS 配置)"""
    
    # 优先使用全局配置的币种
    configured = get_configured_symbols()
    if configured:
        # 转换为 CoinGlass 格式 (BTC 而非 BTCUSDT)
        symbols = sorted(set(to_base_symbol(s) for s in configured))
        return api_response(symbols)
    
    # auto/all 模式: 从数据库获取实际可用币种
    settings = get_settings()
    db_path = settings.SQLITE_INDICATORS_PATH

    if not db_path.exists():
        return error_response(ErrorCode.SERVICE_UNAVAILABLE, "指标数据库不可用")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT "交易对" FROM "基础数据同步器.py" ORDER BY "交易对"')
        rows = cursor.fetchall()
        conn.close()

        # 转换为 CoinGlass 格式 (BTC 而非 BTCUSDT)
        symbols = [to_base_symbol(row[0]) for row in rows if row[0]]
        # 去重并排序
        symbols = sorted(set(symbols))
        
        return api_response(symbols)
    except Exception as e:
        return error_response(ErrorCode.INTERNAL_ERROR, f"查询失败: {e}")
