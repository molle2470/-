"""
네이버 스마트스토어 어댑터 테스트.

NaverAdapter 초기화, 스텁 구현(NotImplementedError) 확인 테스트.
"""
import pytest

from backend.adapters.naver_adapter import NaverAdapter


def test_naver_adapter_init():
    """NaverAdapter 초기화 파라미터 확인"""
    adapter = NaverAdapter("client_id", "client_secret", "channel_id")
    assert adapter.client_id == "client_id"
    assert adapter.client_secret == "client_secret"
    assert adapter.channel_id == "channel_id"


def test_naver_adapter_has_http_client():
    """httpx 클라이언트 속성 존재 확인"""
    adapter = NaverAdapter("id", "secret", "channel")
    assert hasattr(adapter, "http_client")


@pytest.mark.asyncio
async def test_register_product_raises_not_implemented():
    """스텁 구현이므로 NotImplementedError 발생"""
    adapter = NaverAdapter("id", "secret", "channel")
    with pytest.raises(NotImplementedError):
        await adapter.register_product({"name": "테스트 상품"})


@pytest.mark.asyncio
async def test_update_price_raises_not_implemented():
    """가격 수정 스텁 - NotImplementedError 발생"""
    adapter = NaverAdapter("id", "secret", "channel")
    with pytest.raises(NotImplementedError):
        await adapter.update_price("NAVER_123", 99000)


@pytest.mark.asyncio
async def test_update_stock_raises_not_implemented():
    """재고 처리 스텁 - NotImplementedError 발생"""
    adapter = NaverAdapter("id", "secret", "channel")
    with pytest.raises(NotImplementedError):
        await adapter.update_stock("NAVER_123", False)


@pytest.mark.asyncio
async def test_deactivate_product_raises_not_implemented():
    """상품 비활성화 스텁 - NotImplementedError 발생"""
    adapter = NaverAdapter("id", "secret", "channel")
    with pytest.raises(NotImplementedError):
        await adapter.deactivate_product("NAVER_123")


def test_get_headers_returns_dict():
    """_get_headers()가 Authorization 헤더 포함 딕셔너리 반환"""
    adapter = NaverAdapter("id", "secret", "channel")
    # 토큰 없이는 빈 Authorization 반환 가능 (스텁)
    headers = adapter._get_headers(access_token="test_token")
    assert isinstance(headers, dict)
    assert "Authorization" in headers
    assert "test_token" in headers["Authorization"]
