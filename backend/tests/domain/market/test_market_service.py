"""
MarketService 단위 테스트.

DB 세션과 Repository를 AsyncMock으로 모킹하여
서비스 비즈니스 로직만 검증합니다.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.domain.market.model import MarketAccount, MarketListing, MarketTemplate
from backend.domain.market.service import MarketService


@pytest.mark.asyncio
async def test_get_active_accounts():
    """마켓 활성 계정 목록 반환"""
    session = AsyncMock()

    with patch("backend.domain.market.service.MarketAccountRepository") as MockAccountRepo, \
         patch("backend.domain.market.service.MarketListingRepository"), \
         patch("backend.domain.market.service.MarketTemplateRepository"), \
         patch("backend.domain.market.service.PriceCalculator"):

        mock_repo = AsyncMock()
        MockAccountRepo.return_value = mock_repo

        expected = [
            MarketAccount(id=1, business_group_id=1, market_id=1, account_id="seller1", is_active=True),
            MarketAccount(id=2, business_group_id=2, market_id=1, account_id="seller2", is_active=True),
        ]
        mock_repo.filter_by_async.return_value = expected

        service = MarketService(session)
        result = await service.get_active_accounts(market_id=1)

        mock_repo.filter_by_async.assert_called_once_with(market_id=1, is_active=True)
        assert len(result) == 2
        assert result[0].account_id == "seller1"


@pytest.mark.asyncio
async def test_calculate_selling_price_with_template():
    """MarketTemplate commission_rate 사용하여 판매가 계산"""
    session = AsyncMock()

    with patch("backend.domain.market.service.MarketAccountRepository"), \
         patch("backend.domain.market.service.MarketListingRepository"), \
         patch("backend.domain.market.service.MarketTemplateRepository") as MockTemplateRepo, \
         patch("backend.domain.market.service.PriceCalculator") as MockCalc:

        mock_template_repo = AsyncMock()
        MockTemplateRepo.return_value = mock_template_repo

        # commission_rate = 10% 템플릿
        template = MarketTemplate(
            id=1,
            market_id=1,
            common_template_id=1,
            commission_rate=0.1,
            margin_rate=0.2,
        )
        mock_template_repo.find_by_market.return_value = template

        mock_calc_instance = MagicMock()
        MockCalc.return_value = mock_calc_instance
        mock_calc_instance.calculate.return_value = 215000

        service = MarketService(session)
        result = await service.calculate_selling_price(
            original_price=150000,
            market_id=1,
            margin_rate=0.2,
        )

        # commission_rate=0.1 (템플릿에서), margin_rate=0.2 (인자)
        mock_calc_instance.calculate.assert_called_once_with(
            original_price=150000,
            commission_rate=0.1,
            margin_rate=0.2,
        )
        assert result == 215000


@pytest.mark.asyncio
async def test_calculate_selling_price_no_template():
    """템플릿 없을 때 commission_rate=0.0으로 계산"""
    session = AsyncMock()

    with patch("backend.domain.market.service.MarketAccountRepository"), \
         patch("backend.domain.market.service.MarketListingRepository"), \
         patch("backend.domain.market.service.MarketTemplateRepository") as MockTemplateRepo, \
         patch("backend.domain.market.service.PriceCalculator") as MockCalc:

        mock_template_repo = AsyncMock()
        MockTemplateRepo.return_value = mock_template_repo
        mock_template_repo.find_by_market.return_value = None

        mock_calc_instance = MagicMock()
        MockCalc.return_value = mock_calc_instance
        mock_calc_instance.calculate.return_value = 188000

        service = MarketService(session)
        result = await service.calculate_selling_price(
            original_price=150000,
            market_id=99,
            margin_rate=0.2,
        )

        # 템플릿 없으면 commission_rate=0.0
        mock_calc_instance.calculate.assert_called_once_with(
            original_price=150000,
            commission_rate=0.0,
            margin_rate=0.2,
        )


@pytest.mark.asyncio
async def test_list_listings_by_product():
    """상품 ID 필터 마켓 등록 목록 조회"""
    session = AsyncMock()

    with patch("backend.domain.market.service.MarketAccountRepository"), \
         patch("backend.domain.market.service.MarketListingRepository") as MockListingRepo, \
         patch("backend.domain.market.service.MarketTemplateRepository"), \
         patch("backend.domain.market.service.PriceCalculator"):

        mock_listing_repo = AsyncMock()
        MockListingRepo.return_value = mock_listing_repo

        expected = [
            MarketListing(id=1, product_id=1, market_account_id=1, selling_price=200000),
        ]
        mock_listing_repo.filter_by_async.return_value = expected

        service = MarketService(session)
        result = await service.list_listings(product_id=1)

        mock_listing_repo.filter_by_async.assert_called_once_with(product_id=1)
        assert len(result) == 1


@pytest.mark.asyncio
async def test_list_listings_no_filter():
    """필터 없이 전체 목록 조회"""
    session = AsyncMock()

    with patch("backend.domain.market.service.MarketAccountRepository"), \
         patch("backend.domain.market.service.MarketListingRepository") as MockListingRepo, \
         patch("backend.domain.market.service.MarketTemplateRepository"), \
         patch("backend.domain.market.service.PriceCalculator"):

        mock_listing_repo = AsyncMock()
        MockListingRepo.return_value = mock_listing_repo
        mock_listing_repo.filter_by_async.return_value = []

        service = MarketService(session)
        result = await service.list_listings()

        # 필터 없이 호출
        mock_listing_repo.filter_by_async.assert_called_once_with()
        assert result == []
