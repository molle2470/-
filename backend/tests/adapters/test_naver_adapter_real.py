"""NaverAdapter 실제 구현 테스트 (httpx mock 사용)."""
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

# BCrypt salt 형식의 테스트 시크릿 (실제 API와 동일한 형식)
TEST_BCRYPT_SALT = "$2b$04$PncV.R1TfZ1J5ZEZzyt8iO"


@pytest.fixture
def adapter():
    from backend.adapters.naver_adapter import NaverAdapter
    return NaverAdapter("test_client_id", TEST_BCRYPT_SALT, "test_channel_id")


def make_mock_response(json_data: dict) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = json_data
    return resp


@pytest.mark.asyncio
async def test_get_access_token_bcrypt_signature(adapter):
    """BCrypt 서명이 올바르게 생성되는지 검증"""
    import base64
    import bcrypt

    captured: dict = {}

    async def fake_post(url, **kwargs):
        captured.update(kwargs.get("data", {}))
        return make_mock_response({"access_token": "tok", "expires_in": 3600})

    with patch.object(adapter.http_client, "post", side_effect=fake_post):
        token = await adapter._get_access_token()

    assert token == "tok"
    ts = captured["timestamp"]
    password = f"test_client_id_{ts}"
    # client_secret(BCrypt salt)로 서명 생성
    expected_hash = bcrypt.hashpw(password.encode("utf-8"), TEST_BCRYPT_SALT.encode("utf-8"))
    expected_sign = base64.b64encode(expected_hash).decode("utf-8")
    assert captured["client_secret_sign"] == expected_sign
    assert captured["grant_type"] == "client_credentials"


@pytest.mark.asyncio
async def test_get_access_token_cached(adapter):
    """두 번 호출해도 토큰이 유효하면 POST 1회만 발생"""
    call_count = 0

    async def fake_post(url, **kwargs):
        nonlocal call_count
        call_count += 1
        return make_mock_response({"access_token": "cached_tok", "expires_in": 3600})

    with patch.object(adapter.http_client, "post", side_effect=fake_post):
        t1 = await adapter._get_access_token()
        t2 = await adapter._get_access_token()

    assert t1 == t2 == "cached_tok"
    assert call_count == 1


@pytest.mark.asyncio
async def test_upload_image_returns_naver_url(adapter):
    """이미지 업로드 → 네이버 호스팅 URL 반환"""
    token_resp = make_mock_response({"access_token": "tok", "expires_in": 3600})
    image_resp = make_mock_response({
        "images": [{"url": "https://shop-phinf.pstatic.net/abc/img.jpg"}]
    })

    call_count = 0

    async def fake_post(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return token_resp
        return image_resp

    with patch.object(adapter.http_client, "post", side_effect=fake_post):
        result = await adapter.upload_image("https://external.com/img.jpg")

    assert result == "https://shop-phinf.pstatic.net/abc/img.jpg"


@pytest.mark.asyncio
async def test_register_product_returns_origin_product_no(adapter):
    """상품 등록 성공 시 originProductNo 문자열 반환"""
    token_resp = make_mock_response({"access_token": "tok", "expires_in": 3600})
    image_resp = make_mock_response({
        "images": [{"url": "https://shop-phinf.pstatic.net/abc/img.jpg"}]
    })
    register_resp = make_mock_response({"originProductNo": 12345678})

    call_count = 0

    async def fake_post(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return token_resp
        if call_count == 2:
            return image_resp
        return register_resp

    with patch.object(adapter.http_client, "post", side_effect=fake_post):
        result = await adapter.register_product({
            "name": "나이키 에어맥스 90",
            "selling_price": 150000,
            "thumbnail_url": "https://example.com/img.jpg",
            "source_category": "스니커즈",
            "return_fee": 5000,
            "as_phone": "02-1234-5678",
        })

    assert result == "12345678"


@pytest.mark.asyncio
async def test_update_price_uses_get_then_put(adapter):
    """가격 수정: GET으로 기존 데이터 조회 후 PUT으로 전체 업데이트"""
    token_resp = make_mock_response({"access_token": "tok", "expires_in": 3600})
    existing_product = {
        "originProduct": {
            "statusType": "SALE",
            "salePrice": 100000,
            "name": "기존상품명",
        }
    }
    get_resp = make_mock_response(existing_product)
    put_resp = make_mock_response({})

    with patch.object(adapter.http_client, "post", new=AsyncMock(return_value=token_resp)):
        with patch.object(adapter.http_client, "get", new=AsyncMock(return_value=get_resp)):
            with patch.object(adapter.http_client, "put", new=AsyncMock(return_value=put_resp)) as mock_put:
                result = await adapter.update_price("99999", 180000)

    assert result is True
    call_kwargs = mock_put.call_args.kwargs
    payload = call_kwargs.get("json", {})
    assert payload["originProduct"]["name"] == "기존상품명"
    assert payload["originProduct"]["salePrice"] == 180000


@pytest.mark.asyncio
async def test_update_stock_out_sets_suspension(adapter):
    """품절 처리: statusType=SUSPENSION 설정"""
    token_resp = make_mock_response({"access_token": "tok", "expires_in": 3600})
    existing = {"originProduct": {"statusType": "SALE", "salePrice": 100000, "name": "상품"}}
    get_resp = make_mock_response(existing)
    put_resp = make_mock_response({})

    with patch.object(adapter.http_client, "post", new=AsyncMock(return_value=token_resp)):
        with patch.object(adapter.http_client, "get", new=AsyncMock(return_value=get_resp)):
            with patch.object(adapter.http_client, "put", new=AsyncMock(return_value=put_resp)) as mock_put:
                result = await adapter.update_stock("99999", in_stock=False)

    assert result is True
    payload = mock_put.call_args.kwargs.get("json", {})
    assert payload["originProduct"]["statusType"] == "SUSPENSION"


@pytest.mark.asyncio
async def test_deactivate_product_uses_suspension(adapter):
    """비활성화: SUSPENSION 사용 (PROHIBITED는 판매자 설정 불가)"""
    token_resp = make_mock_response({"access_token": "tok", "expires_in": 3600})
    existing = {"originProduct": {"statusType": "SALE", "salePrice": 100000, "name": "상품"}}
    get_resp = make_mock_response(existing)
    put_resp = make_mock_response({})

    with patch.object(adapter.http_client, "post", new=AsyncMock(return_value=token_resp)):
        with patch.object(adapter.http_client, "get", new=AsyncMock(return_value=get_resp)):
            with patch.object(adapter.http_client, "put", new=AsyncMock(return_value=put_resp)) as mock_put:
                result = await adapter.deactivate_product("99999")

    assert result is True
    payload = mock_put.call_args.kwargs.get("json", {})
    assert payload["originProduct"]["statusType"] == "SUSPENSION"
