"""익스텐션 통신 API 라우터 테스트."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


def test_extension_router_imports():
    """라우터 import 확인"""
    from backend.api.v1.routers.extension import router
    assert router is not None


def test_verify_extension_key_valid():
    """유효한 API 키 검증"""
    from backend.api.v1.routers.extension import verify_extension_key, EXTENSION_API_KEY
    result = verify_extension_key(EXTENSION_API_KEY)
    assert result == EXTENSION_API_KEY


def test_verify_extension_key_invalid():
    """잘못된 API 키 검증"""
    from fastapi import HTTPException
    from backend.api.v1.routers.extension import verify_extension_key
    with pytest.raises(HTTPException) as exc_info:
        verify_extension_key("wrong-key")
    assert exc_info.value.status_code == 401
