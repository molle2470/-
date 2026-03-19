"""
상품(Product) 도메인 Repository.
"""
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.shared.base_repository import BaseRepository
from backend.domain.product.model import (
    Product,
    ProductOptionGroup,
    ProductOptionValue,
    ProductVariant,
    ProductStatusEnum,
    StockStatusEnum,
)


class ProductRepository(BaseRepository[Product]):
    """상품 마스터 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Product)

    async def find_by_source_product_id(
        self, source_id: int, source_product_id: str
    ) -> Optional[Product]:
        """소싱처 고유 ID로 상품 조회 (중복 수집 체크)"""
        return await self.find_by_async(
            source_id=source_id, source_product_id=source_product_id
        )

    async def find_registered_products(self) -> List[Product]:
        """마켓에 등록된 상품 목록 (모니터링 대상)"""
        return await self.filter_by_async(status=ProductStatusEnum.REGISTERED)

    async def find_by_filters(
        self,
        source_id: Optional[int] = None,
        brand_id: Optional[int] = None,
        status: Optional[ProductStatusEnum] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Product]:
        """필터 기반 상품 목록 조회"""
        filters: Dict[str, Any] = {}
        if source_id is not None:
            filters["source_id"] = source_id
        if brand_id is not None:
            filters["brand_id"] = brand_id
        if status is not None:
            filters["status"] = status
        return await self.filter_by_async(skip=skip, limit=limit, **filters)


class ProductOptionGroupRepository(BaseRepository[ProductOptionGroup]):
    """상품 옵션 그룹 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ProductOptionGroup)

    async def find_by_product(self, product_id: int) -> List[ProductOptionGroup]:
        """상품별 옵션 그룹 목록"""
        return await self.filter_by_async(product_id=product_id)


class ProductOptionValueRepository(BaseRepository[ProductOptionValue]):
    """옵션 값 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ProductOptionValue)

    async def find_by_group(self, group_id: int) -> List[ProductOptionValue]:
        """그룹별 옵션 값 목록"""
        return await self.filter_by_async(group_id=group_id)


class ProductVariantRepository(BaseRepository[ProductVariant]):
    """상품 옵션 조합 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ProductVariant)

    async def find_by_product(self, product_id: int) -> List[ProductVariant]:
        """상품별 옵션 조합 목록"""
        return await self.filter_by_async(product_id=product_id)

    async def find_in_stock_variants(self, product_id: int) -> List[ProductVariant]:
        """재고 있는 옵션 조합 목록"""
        return await self.filter_by_async(
            product_id=product_id, stock_status=StockStatusEnum.IN_STOCK
        )
