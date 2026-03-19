"""수집 설정 API 라우터 테스트."""
import sys
import pytest
from unittest.mock import MagicMock, AsyncMock


# 테스트 환경에서 DB/settings 없이 라우터 모듈 import를 허용하기 위한 mock 주입
_mock_settings = MagicMock()

_mock_config_module = MagicMock()
_mock_config_module.settings = _mock_settings

_mock_orm_module = MagicMock()
_mock_orm_module.get_read_session_dependency = MagicMock(return_value=AsyncMock())
_mock_orm_module.get_write_session_dependency = MagicMock(return_value=AsyncMock())

# config/orm 모듈이 아직 로드되지 않은 경우에만 mock 주입
if "backend.core.config" not in sys.modules:
    sys.modules["backend.core.config"] = _mock_config_module
if "backend.db.orm" not in sys.modules:
    sys.modules["backend.db.orm"] = _mock_orm_module


def test_collection_settings_router_imports():
    """라우터 import 확인"""
    from backend.api.v1.routers.collection_settings import router
    assert router is not None


def test_collection_logs_router_imports():
    """수집 로그 라우터 import 확인"""
    from backend.api.v1.routers.collection_logs import router
    assert router is not None


def test_products_router_imports():
    """상품 라우터 import 확인"""
    from backend.api.v1.routers.products import router
    assert router is not None
