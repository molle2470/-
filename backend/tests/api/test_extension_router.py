"""익스텐션 통신 API 라우터 테스트."""
import sys
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

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
    """유효한 API 키 검증 — settings.extension_api_key와 일치하는 경우 통과"""
    from backend.api.v1.routers.extension import verify_extension_key

    mock_settings = MagicMock()
    mock_settings.extension_api_key = "sourcing-extension-phase1-key"

    # 다른 테스트가 먼저 실행되어 settings가 다른 mock으로 주입됐을 수 있으므로 patch로 고정
    with patch("backend.api.v1.routers.extension.settings", mock_settings):
        result = verify_extension_key("sourcing-extension-phase1-key")
    assert result == "sourcing-extension-phase1-key"


def test_verify_extension_key_invalid():
    """잘못된 API 키 검증"""
    from fastapi import HTTPException
    from backend.api.v1.routers.extension import verify_extension_key

    mock_settings = MagicMock()
    mock_settings.extension_api_key = "sourcing-extension-phase1-key"

    with patch("backend.api.v1.routers.extension.settings", mock_settings):
        with pytest.raises(HTTPException) as exc_info:
            verify_extension_key("wrong-key")
    assert exc_info.value.status_code == 401
