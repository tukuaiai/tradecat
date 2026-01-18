"""pytest 配置"""

import pytest
from fastapi.testclient import TestClient

from src.app import app


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)
