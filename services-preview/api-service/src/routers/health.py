"""健康检查路由"""

from datetime import datetime

from fastapi import APIRouter

from src import __version__
from src.utils.errors import api_response

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """健康检查"""
    return api_response({
        "status": "healthy",
        "service": "api-service",
        "version": __version__,
        "timestamp": int(datetime.now().timestamp() * 1000)
    })
