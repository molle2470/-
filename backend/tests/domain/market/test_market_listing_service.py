"""MarketService 마켓 등록 로직 테스트."""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_register_product_to_market_success(mock_session):
    """register_product_to_market 성공 시 REGISTERED 상태의 MarketListing 반환"""
    from backend.domain.market.service import MarketService
    from backend.domain.market.model import ListingStatusEnum

    service = MarketService(mock_session)

    mock_listing_repo = AsyncMock()
    mock_listing_repo.filter_by_async = AsyncMock(return_value=[])
    service.listing_repo = mock_listing_repo

    mock_template_repo = AsyncMock()
    mock_template = MagicMock()
    mock_template.commission_rate = 0.08
    mock_template.return_fee = 5000
    mock_template_repo.find_by_market = AsyncMock(return_value=mock_template)
    service.template_repo = mock_template_repo

    mock_common_template_repo = AsyncMock()
    mock_common = MagicMock()
    mock_common.as_phone = "02-1234-5678"
    # BaseRepository의 실제 메서드명에 맞게 설정 (get_async)
    mock_common_template_repo.get_async = AsyncMock(return_value=mock_common)
    service.common_template_repo = mock_common_template_repo

    mock_adapter = AsyncMock()
    mock_adapter.register_product = AsyncMock(return_value="NAVER_123456")

    product = MagicMock()
    product.id = 1
    product.name = "나이키 에어맥스"
    product.original_price = 100000
    product.thumbnail_url = "https://example.com/img.jpg"
    product.source_category = "스니커즈"

    result = await service.register_product_to_market(
        product=product,
        market_account_id=1,
        market_id=1,
        common_template_id=1,
        adapter=mock_adapter,
        margin_rate=0.2,
    )

    assert result.market_product_id == "NAVER_123456"
    assert result.listing_status == ListingStatusEnum.REGISTERED
    mock_adapter.register_product.assert_called_once()


@pytest.mark.asyncio
async def test_register_product_to_market_duplicate_blocked(mock_session):
    """이미 REGISTERED 상태 상품 재등록 시도 → ValueError"""
    from backend.domain.market.service import MarketService
    from backend.domain.market.model import ListingStatusEnum, MarketListing

    service = MarketService(mock_session)

    existing = MagicMock(spec=MarketListing)
    existing.listing_status = ListingStatusEnum.REGISTERED

    mock_listing_repo = AsyncMock()
    mock_listing_repo.filter_by_async = AsyncMock(return_value=[existing])
    service.listing_repo = mock_listing_repo

    product = MagicMock()
    product.id = 1

    with pytest.raises(ValueError, match="이미 등록된 상품"):
        await service.register_product_to_market(
            product=product,
            market_account_id=1,
            market_id=1,
            common_template_id=1,
            adapter=AsyncMock(),
            margin_rate=0.2,
        )


@pytest.mark.asyncio
async def test_register_product_to_market_api_failure_records_failed(mock_session):
    """NaverAdapter API 실패 시 FAILED 상태 MarketListing 저장 후 예외 전파"""
    from backend.domain.market.service import MarketService
    from backend.domain.market.model import ListingStatusEnum

    service = MarketService(mock_session)

    mock_listing_repo = AsyncMock()
    mock_listing_repo.filter_by_async = AsyncMock(return_value=[])
    service.listing_repo = mock_listing_repo

    mock_template_repo = AsyncMock()
    mock_template = MagicMock()
    mock_template.commission_rate = 0.08
    mock_template.return_fee = 5000
    mock_template_repo.find_by_market = AsyncMock(return_value=mock_template)
    service.template_repo = mock_template_repo

    mock_common_template_repo = AsyncMock()
    mock_common = MagicMock()
    mock_common.as_phone = "02-0000-0000"
    mock_common_template_repo.get_async = AsyncMock(return_value=mock_common)
    service.common_template_repo = mock_common_template_repo

    mock_adapter = AsyncMock()
    mock_adapter.register_product = AsyncMock(side_effect=Exception("API 오류"))

    product = MagicMock()
    product.id = 1
    product.name = "상품명"
    product.original_price = 100000
    product.thumbnail_url = "https://example.com/img.jpg"
    product.source_category = "스니커즈"

    with pytest.raises(Exception, match="API 오류"):
        await service.register_product_to_market(
            product=product,
            market_account_id=1,
            market_id=1,
            common_template_id=1,
            adapter=mock_adapter,
            margin_rate=0.2,
        )

    # FAILED 상태 리스팅이 저장되었는지 확인
    assert mock_session.add.called
    added_listing = mock_session.add.call_args[0][0]
    assert added_listing.listing_status == ListingStatusEnum.FAILED
