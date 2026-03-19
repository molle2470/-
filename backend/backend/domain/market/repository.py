"""
마켓(Market) 도메인 Repository.
"""
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.shared.base_repository import BaseRepository
from backend.domain.market.model import (
    BusinessGroup,
    ClearanceStatusEnum,
    CoupangBrandClearance,
    CommonTemplate,
    ListingStatusEnum,
    Market,
    MarketAccount,
    MarketListing,
    MarketTemplate,
    SeoRule,
)


class BusinessGroupRepository(BaseRepository[BusinessGroup]):
    """사업자 그룹 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, BusinessGroup)


class MarketRepository(BaseRepository[Market]):
    """마켓 종류 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Market)

    async def find_by_name(self, name: str) -> Optional[Market]:
        """마켓 이름으로 조회"""
        return await self.find_by_async(name=name)


class MarketAccountRepository(BaseRepository[MarketAccount]):
    """마켓 계정 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, MarketAccount)

    async def find_by_business_and_market(
        self, business_group_id: int, market_id: int
    ) -> List[MarketAccount]:
        """사업자 그룹 + 마켓별 계정 목록"""
        return await self.filter_by_async(
            business_group_id=business_group_id, market_id=market_id
        )

    async def find_active_accounts(self) -> List[MarketAccount]:
        """활성 마켓 계정 목록"""
        return await self.filter_by_async(is_active=True)


class CommonTemplateRepository(BaseRepository[CommonTemplate]):
    """공통 기본값 템플릿 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, CommonTemplate)


class MarketTemplateRepository(BaseRepository[MarketTemplate]):
    """마켓별 템플릿 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, MarketTemplate)

    async def find_by_market(self, market_id: int) -> Optional[MarketTemplate]:
        """마켓 ID로 템플릿 조회"""
        return await self.find_by_async(market_id=market_id)


class SeoRuleRepository(BaseRepository[SeoRule]):
    """마켓별 SEO 규칙 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, SeoRule)

    async def find_by_market(self, market_id: int) -> Optional[SeoRule]:
        """마켓 ID로 SEO 규칙 조회"""
        return await self.find_by_async(market_id=market_id)


class CoupangBrandClearanceRepository(BaseRepository[CoupangBrandClearance]):
    """쿠팡 브랜드 소명 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, CoupangBrandClearance)

    async def find_by_account_and_brand(
        self, market_account_id: int, brand_id: int
    ) -> Optional[CoupangBrandClearance]:
        """계정 + 브랜드 조합으로 소명 이력 조회"""
        return await self.find_by_async(
            market_account_id=market_account_id, brand_id=brand_id
        )

    async def find_completed_clearances(
        self, market_account_id: int
    ) -> List[CoupangBrandClearance]:
        """소명 완료된 브랜드 목록 (쿠팡 등록 가능 여부 확인용)"""
        return await self.filter_by_async(
            market_account_id=market_account_id,
            clearance_status=ClearanceStatusEnum.COMPLETED,
        )


class MarketListingRepository(BaseRepository[MarketListing]):
    """마켓 등록 내역 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, MarketListing)

    async def find_by_product(self, product_id: int) -> List[MarketListing]:
        """상품별 마켓 등록 내역 목록"""
        return await self.filter_by_async(product_id=product_id)

    async def find_registered_listings(self) -> List[MarketListing]:
        """등록 완료된 마켓 리스팅 목록"""
        return await self.filter_by_async(listing_status=ListingStatusEnum.REGISTERED)
