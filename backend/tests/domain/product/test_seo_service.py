"""SeoGeneratorService 테스트 (Claude API mock 사용)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def make_product_data(
    name="나이키 에어맥스 97 화이트 / BQ1234-100",
    brand_name="NIKE",
    source_category="스니커즈",
    original_price=139000,
):
    """테스트용 ExtensionProductData mock"""
    data = MagicMock()
    data.name = name
    data.brand_name = brand_name
    data.source_category = source_category
    data.original_price = original_price
    return data


@pytest.mark.asyncio
async def test_generate_uses_rules_for_color():
    """색상 추출은 규칙 기반"""
    from backend.domain.product.seo_service import SeoGeneratorService

    service = SeoGeneratorService(api_key=None)  # fallback 모드
    result = await service.generate(
        product_data=make_product_data(name="나이키 에어맥스 화이트"),
        product_id=1,
    )
    assert result["color"] == "화이트"


@pytest.mark.asyncio
async def test_generate_fallback_when_no_api_key():
    """API 키 없으면 규칙 기반 fallback"""
    from backend.domain.product.seo_service import SeoGeneratorService

    service = SeoGeneratorService(api_key=None)
    result = await service.generate(
        product_data=make_product_data(),
        product_id=1,
    )
    # fallback이어도 모든 필드가 채워져야 함
    assert result["optimized_name"]
    assert len(result["tags"]) > 0
    assert result["brand"] == "NIKE"
    assert result["status"] == "fallback"


@pytest.mark.asyncio
async def test_generate_fallback_on_api_error():
    """Claude API 에러 시 fallback"""
    from backend.domain.product.seo_service import SeoGeneratorService

    service = SeoGeneratorService(api_key="fake-key")

    with patch.object(service, "_call_claude_api", new_callable=AsyncMock) as mock_api:
        mock_api.side_effect = Exception("API Error")
        result = await service.generate(
            product_data=make_product_data(),
            product_id=1,
        )

    assert result["status"] == "fallback"
    assert result["optimized_name"]  # 빈 칸 없음


@pytest.mark.asyncio
async def test_generate_with_claude_success():
    """Claude API 성공 시 generated 상태"""
    from backend.domain.product.seo_service import SeoGeneratorService

    service = SeoGeneratorService(api_key="fake-key")

    claude_result = {
        "optimized_name": "나이키 에어맥스 97 화이트 운동화",
        "tags": ["나이키", "에어맥스", "화이트스니커즈"],
        "material": "메쉬/합성피혁",
    }

    with patch.object(service, "_call_claude_api", new_callable=AsyncMock) as mock_api:
        mock_api.return_value = claude_result
        result = await service.generate(
            product_data=make_product_data(),
            product_id=1,
        )

    assert result["optimized_name"] == "나이키 에어맥스 97 화이트 운동화"
    assert result["material"] == "메쉬/합성피혁"
    assert result["status"] == "generated"


@pytest.mark.asyncio
async def test_generate_category_mapped():
    """스니커즈 카테고리가 네이버 ID로 매핑됨"""
    from backend.domain.product.seo_service import SeoGeneratorService

    service = SeoGeneratorService(api_key=None)
    result = await service.generate(
        product_data=make_product_data(source_category="스니커즈"),
        product_id=1,
    )
    assert result["naver_category_id"] == "50000803"


@pytest.mark.asyncio
async def test_generate_no_empty_fields():
    """모든 필드가 채워져 있어야 함 (빈 칸 없음)"""
    from backend.domain.product.seo_service import SeoGeneratorService

    service = SeoGeneratorService(api_key=None)
    result = await service.generate(
        product_data=make_product_data(),
        product_id=1,
    )
    assert result["optimized_name"]
    assert result["brand"]
    assert result["age_group"]
    assert result["origin"]
    assert result["gender"]
