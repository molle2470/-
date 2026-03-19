"""
마켓(Market) 도메인 서비스 레이어.

마켓 활성 계정 조회, 판매가 자동 계산, 마켓 등록 목록 조회 등
마켓 도메인 핵심 비즈니스 로직을 담당합니다.
"""
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.market.model import MarketAccount, MarketListing
from backend.domain.market.repository import (
    MarketAccountRepository,
    MarketListingRepository,
    MarketTemplateRepository,
)
from backend.services.price_calculator import PriceCalculator


class MarketService:
    """마켓 도메인 서비스"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.account_repo = MarketAccountRepository(session)
        self.listing_repo = MarketListingRepository(session)
        self.template_repo = MarketTemplateRepository(session)
        self.price_calculator = PriceCalculator()

    async def get_active_accounts(self, market_id: int) -> List[MarketAccount]:
        """
        마켓 활성 계정 목록 조회.

        Args:
            market_id: 마켓 ID

        Returns:
            해당 마켓의 활성(is_active=True) 계정 목록
        """
        return await self.account_repo.filter_by_async(
            market_id=market_id,
            is_active=True,
        )

    async def calculate_selling_price(
        self,
        original_price: int,
        market_id: int,
        margin_rate: float = 0.2,
    ) -> int:
        """
        판매가 자동 계산 (마켓 수수료 + 마진율 기반).

        MarketTemplate에서 commission_rate를 조회하고,
        PriceCalculator를 이용해 판매가를 계산합니다.

        Args:
            original_price: 원가 (원)
            market_id: 마켓 ID (commission_rate 조회용)
            margin_rate: 마진율 (기본값: 0.2 = 20%)

        Returns:
            계산된 판매가 (원, 올림 처리)
        """
        # MarketTemplate에서 수수료율 조회
        template = await self.template_repo.find_by_market(market_id=market_id)
        commission_rate = template.commission_rate if template is not None else 0.0

        return self.price_calculator.calculate(
            original_price=original_price,
            commission_rate=commission_rate,
            margin_rate=margin_rate,
        )

    async def list_listings(
        self,
        product_id: Optional[int] = None,
        account_id: Optional[int] = None,
    ) -> List[MarketListing]:
        """
        마켓 등록 목록 조회.

        Args:
            product_id: 상품 ID 필터 (None이면 전체)
            account_id: 마켓 계정 ID 필터 (None이면 전체)

        Returns:
            필터 조건에 맞는 MarketListing 목록
        """
        filters: dict = {}
        if product_id is not None:
            filters["product_id"] = product_id
        if account_id is not None:
            filters["market_account_id"] = account_id

        return await self.listing_repo.filter_by_async(**filters)
