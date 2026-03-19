"""익스텐션 통신 API 라우터 테스트."""
import sys
import pytest
from unittest.mock import MagicMock, AsyncMock


# 테스트 환경에서 DB/settings 없이 라우터 모듈 import를 허용하기 위한 mock 주입
_mock_settings = MagicMock()
_mock_settings.extension_api_key = "sourcing-extension-phase1-key"

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


def test_extension_router_imports():
    """라우터 import 확인"""
    from backend.api.v1.routers.extension import router
    assert router is not None


def test_verify_extension_key_valid():
    """유효한 API 키 검증"""
    from backend.api.v1.routers.extension import verify_extension_key
    result = verify_extension_key("sourcing-extension-phase1-key")
    assert result == "sourcing-extension-phase1-key"


def test_verify_extension_key_invalid():
    """잘못된 API 키 검증"""
    from fastapi import HTTPException
    from backend.api.v1.routers.extension import verify_extension_key
    with pytest.raises(HTTPException) as exc_info:
        verify_extension_key("wrong-key")
    assert exc_info.value.status_code == 401
