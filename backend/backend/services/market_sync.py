"""마켓 동기화 서비스 - 원가/재고 변동을 마켓에 자동 반영.

변동 감지 트리거:
1. 원가 변동 → 판매가 재계산 → 마켓 가격 수정
2. 재고 변동 → 마켓 품절/재활성화
"""
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from backend.adapters.base_adapter import BaseMarketAdapter
from backend.domain.market.model import ListingStatusEnum
from backend.domain.market.repository import MarketListingRepository
from backend.services.price_calculator import PriceCalculator


class MarketSyncService:
    """마켓 동기화 서비스

    원가 변동, 재고 변동을 감지하여 마켓에 자동 반영합니다.
    트리거:
    1. 원가 변동 → 판매가 재계산 → 마켓 가격 수정
    2. 재고 변동 → 마켓 품절/재활성화
    """

    def __init__(
        self,
        session: AsyncSession,
        adapter: BaseMarketAdapter,
    ) -> None:
        self.session = session
        self.adapter = adapter
        self.listing_repo = MarketListingRepository(session)
        self.price_calculator = PriceCalculator()

    async def sync_price_change(
        self,
        product_id: int,
        new_price: int,
        commission_rate: float,
        margin_rate: float,
    ) -> List[str]:
        """원가 변동 시 마켓 가격 동기화.

        새 판매가를 계산하고 해당 상품의 모든 마켓 등록 상품에 가격을 반영합니다.

        Args:
            product_id: 상품 ID
            new_price: 새로운 원가 (원)
            commission_rate: 마켓 수수료율 (예: 0.05 = 5%)
            margin_rate: 마진율 (예: 0.20 = 20%)

        Returns:
            성공적으로 업데이트된 market_product_id 목록
        """
        # 새 판매가 계산 (원가 ÷ (1 - 수수료 - 마진율))
        selling_price = self.price_calculator.calculate(new_price, commission_rate, margin_rate)

        # 해당 상품의 마켓 등록 목록 조회
        listings = await self.listing_repo.filter_by_async(product_id=product_id)

        # 각 마켓 등록 상품 가격 업데이트
        updated: List[str] = []
        for listing in listings:
            if listing.market_product_id:
                success = await self.adapter.update_price(listing.market_product_id, selling_price)
                if success:
                    listing.selling_price = selling_price
                    updated.append(listing.market_product_id)

        # 변경 사항이 있을 때만 커밋
        if updated:
            await self.session.commit()

        return updated

    async def sync_stock_change(
        self,
        product_id: int,
        in_stock: bool,
    ) -> List[str]:
        """재고 변동 시 마켓 품절/재활성화 동기화.

        Args:
            product_id: 상품 ID
            in_stock: True=재고 있음(재활성화), False=품절 처리

        Returns:
            성공적으로 업데이트된 market_product_id 목록
        """
        listings = await self.listing_repo.filter_by_async(product_id=product_id)

        # 각 마켓 등록 상품에 재고 상태 반영
        updated: List[str] = []
        for listing in listings:
            if listing.market_product_id:
                success = await self.adapter.update_stock(listing.market_product_id, in_stock)
                if success:
                    # 로컬 DB 상태 동기화
                    listing.listing_status = (
                        ListingStatusEnum.REGISTERED if in_stock
                        else ListingStatusEnum.DEACTIVATED
                    )
                    updated.append(listing.market_product_id)

        if updated:
            await self.session.commit()

        return updated
