"""ProductSeo 리포지토리."""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.domain.product.seo_model import ProductSeo
from backend.domain.shared.base_repository import BaseRepository


class ProductSeoRepository(BaseRepository[ProductSeo]):
    """ProductSeo CRUD"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ProductSeo)

    async def find_by_product_id(
        self,
        product_id: int,
        market_type: str = "naver",
    ) -> Optional[ProductSeo]:
        """product_id + market_type으로 SEO 데이터 조회"""
        stmt = select(ProductSeo).where(
            ProductSeo.product_id == product_id,
            ProductSeo.market_type == market_type,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
