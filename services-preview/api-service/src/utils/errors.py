"""错误码和统一响应"""

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """错误码定义 (对齐 CoinGlass V4)"""
    SUCCESS = "0"
    PARAM_ERROR = "40001"
    INVALID_SYMBOL = "40002"
    INVALID_INTERVAL = "40003"
    TABLE_NOT_FOUND = "40004"
    SERVICE_UNAVAILABLE = "50001"
    INTERNAL_ERROR = "50002"


def api_response(data: Any, code: str = "0", msg: str = "success") -> dict:
    """统一成功响应格式"""
    return {
        "code": code,
        "msg": msg,
        "data": data,
        "success": code == "0"
    }


def error_response(code: ErrorCode, msg: str) -> dict:
    """统一错误响应格式"""
    return {
        "code": code.value,
        "msg": msg,
        "data": None,
        "success": False
    }
