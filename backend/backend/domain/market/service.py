"""
마켓(Market) 도메인 서비스 레이어.

마켓 활성 계정 조회, 판매가 자동 계산, 마켓 등록 목록 조회 등
마켓 도메인 핵심 비즈니스 로직을 담당합니다.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.adapters.base_adapter import BaseMarketAdapter
from backend.domain.market.model import (
    ListingStatusEnum,
    MarketAccount,
    MarketListing,
)
from backend.domain.market.repository import (
    CommonTemplateRepository,
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
        self.common_template_repo = CommonTemplateRepository(session)

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
        kwargs: Dict[str, Any] = {}
        if product_id is not None:
            kwargs["product_id"] = product_id
        if account_id is not None:
            kwargs["market_account_id"] = account_id

        return await self.listing_repo.filter_by_async(**kwargs)

    async def register_product_to_market(
        self,
        product: Any,
        market_account_id: int,
        market_id: int,
        common_template_id: int,
        adapter: BaseMarketAdapter,
        margin_rate: float = 0.2,
    ) -> MarketListing:
        """상품을 마켓에 등록하고 MarketListing 저장.

        1. 중복 등록 차단 (REGISTERED 상태 이미 있으면 ValueError)
        2. 판매가 계산 (수수료 + 마진율)
        3. CommonTemplate에서 A/S 전화번호 조회 (필수)
        4. Adapter로 이미지 업로드 + API 등록
        5. 성공: REGISTERED, 실패: FAILED 상태로 MarketListing 저장

        Raises:
            ValueError: 이미 REGISTERED 상태 등록 내역이 있을 때
        """
        # 중복 등록 차단
        existing = await self.listing_repo.filter_by_async(
            product_id=product.id,
            market_account_id=market_account_id,
        )
        for e in existing:
            if e.listing_status == ListingStatusEnum.REGISTERED:
                raise ValueError(
                    f"이미 등록된 상품 (product_id={product.id}, account_id={market_account_id})"
                )

        # 판매가 계산
        selling_price = await self.calculate_selling_price(
            original_price=product.original_price,
            market_id=market_id,
            margin_rate=margin_rate,
        )

        # 마켓 템플릿에서 반품배송비 조회
        template = await self.template_repo.find_by_market(market_id=market_id)
        return_fee = template.return_fee if template else 5000

        # 공통 템플릿에서 A/S 전화번호 조회
        common_template = await self.common_template_repo.get_async(common_template_id)
        as_phone = common_template.as_phone if common_template else ""

        # MarketListing 초기 레코드 (PENDING 상태)
        listing = MarketListing(
            product_id=product.id,
            market_account_id=market_account_id,
            selling_price=selling_price,
            listing_status=ListingStatusEnum.PENDING,
        )

        try:
            market_product_id = await adapter.register_product({
                "name": product.name,
                "selling_price": selling_price,
                "thumbnail_url": product.thumbnail_url,
                "source_category": getattr(product, "source_category", None),
                "return_fee": return_fee,
                "as_phone": as_phone,
            })
            listing.listing_status = ListingStatusEnum.REGISTERED
            listing.market_product_id = market_product_id
            listing.registered_at = datetime.now(tz=timezone.utc)
        except Exception:
            # API 실패 시 FAILED 상태로 기록 후 예외 전파
            listing.listing_status = ListingStatusEnum.FAILED
            self.session.add(listing)
            await self.session.flush()
            await self.session.commit()
            raise

        self.session.add(listing)
        await self.session.flush()
        await self.session.commit()
        return listing
