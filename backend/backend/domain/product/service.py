"""
상품(Product) 도메인 서비스 레이어.

크롤링 데이터 기반 상품 생성, 가격/재고 변동 감지, 상품 목록 조회 등
상품 도메인 핵심 비즈니스 로직을 담당합니다.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, TypedDict, Union

if TYPE_CHECKING:
    from backend.dtos.extension import ExtensionProductData


class CrawledProductData(TypedDict, total=False):
    """크롤링된 상품 데이터 계약"""

    source_product_id: str
    name: str
    original_price: int
    source_url: str
    thumbnail_url: Optional[str]
    image_urls: Optional[List[str]]
    source_category: Optional[str]
    mapped_category: Optional[str]

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.product.model import (
    Product,
    ProductStatusEnum,
    StockStatusEnum,
)
from backend.domain.product.repository import ProductRepository
from backend.domain.brand.repository import BrandRepository


class ProductService:
    """상품 도메인 서비스"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ProductRepository(session)

    async def create_from_crawled(
        self,
        crawled_data: CrawledProductData,
        source_id: int,
        brand_id: int,
    ) -> Product:
        """
        크롤링 데이터에서 상품 생성 (중복 체크 포함).

        source_product_id로 중복 체크하여, 이미 존재하면 기존 상품을 반환하고
        없으면 새로운 상품을 생성하여 반환합니다.

        Args:
            crawled_data: 크롤러에서 수집한 상품 데이터 딕셔너리
            source_id: 소싱처 ID
            brand_id: 브랜드 ID

        Returns:
            생성되거나 기존에 존재하는 Product 객체
        """
        source_product_id: str = str(crawled_data.get("source_product_id", ""))

        # 중복 체크: 이미 수집된 상품이면 기존 것 반환
        existing = await self.repo.find_by_source_product_id(
            source_id=source_id,
            source_product_id=source_product_id,
        )
        if existing is not None:
            return existing

        # 새 상품 생성
        product = Product(
            source_id=source_id,
            brand_id=brand_id,
            name=str(crawled_data.get("name", "")),
            original_price=int(crawled_data.get("original_price", 0)),
            source_url=str(crawled_data.get("source_url", "")),
            source_product_id=source_product_id,
            thumbnail_url=crawled_data.get("thumbnail_url"),
            image_urls=crawled_data.get("image_urls"),
            source_category=crawled_data.get("source_category"),
            mapped_category=crawled_data.get("mapped_category"),
            last_crawled_at=datetime.now(tz=timezone.utc),
        )
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def update_price_and_stock(
        self,
        product_id: int,
        new_price: int,
        new_stock_status: StockStatusEnum,
    ) -> List[Tuple[str, Union[int, str], Union[int, str]]]:
        """
        가격/재고 변동 업데이트.

        변동 사항을 감지하고 product를 업데이트한 후,
        변동 사항 리스트를 반환합니다.

        Args:
            product_id: 상품 ID
            new_price: 새로운 가격
            new_stock_status: 새로운 재고 상태

        Returns:
            변동 사항 리스트 [(change_type, old_value, new_value), ...]
            예: [("price_change", 100000, 120000), ("stock_change", "in_stock", "out_of_stock")]
        """
        product = await self.repo.get_async(product_id)
        if product is None:
            return []

        changes: List[Tuple[str, Union[int, str], Union[int, str]]] = []

        # 가격 변동 감지
        if product.original_price != new_price:
            changes.append(("price_change", product.original_price, new_price))
            product.original_price = new_price

        # 재고 변동 감지
        if product.stock_status != new_stock_status:
            changes.append(("stock_change", product.stock_status, new_stock_status))
            product.stock_status = new_stock_status

        # 변동이 있는 경우에만 DB 업데이트
        if changes:
            product.last_crawled_at = datetime.now(tz=timezone.utc)
            self.session.add(product)
            await self.session.commit()
            await self.session.refresh(product)

        return changes

    async def create_from_extension(
        self,
        source: str,
        data: "ExtensionProductData",
        source_id: int,
    ) -> Product:
        """
        익스텐션 수집 데이터에서 상품 생성 (중복 체크 + 브랜드 조회 포함).

        Args:
            source: 소싱처 식별자 (예: "musinsa")
            data: 익스텐션에서 전송한 상품 데이터
            source_id: 소싱처 ID

        Returns:
            생성되거나 기존에 존재하는 Product 객체
        """
        # 중복 체크
        existing = await self.repo.find_by_source_product_id(
            source_id=source_id,
            source_product_id=data.source_product_id,
        )
        if existing is not None:
            return existing

        # 브랜드 조회 (brand_name → brand_id)
        brand_repo = BrandRepository(self.session)
        brand = await brand_repo.find_by_name(data.brand_name)
        brand_id = brand.id if brand else None  # 미등록 브랜드는 NULL (나중에 매핑)

        # 상품 생성 (Product 모델에 있는 필드만 설정, repo.create_async 패턴 사용)
        return await self.repo.create_async(
            source_id=source_id,
            brand_id=brand_id,
            name=data.name,
            original_price=data.original_price,
            source_url=data.source_url,
            source_product_id=data.source_product_id,
            thumbnail_url=data.thumbnail_url,
            image_urls=data.image_urls if data.image_urls else None,
            grade_discount_available=data.grade_discount_available,
            point_usable=data.point_usable,
            point_earnable=data.point_earnable,
            last_crawled_at=datetime.now(tz=timezone.utc),
        )

    async def list_products(
        self,
        source_id: Optional[int] = None,
        brand_id: Optional[int] = None,
        status: Optional[ProductStatusEnum] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Product]:
        """
        필터 기반 상품 목록 조회.

        Args:
            source_id: 소싱처 ID 필터 (None이면 전체)
            brand_id: 브랜드 ID 필터 (None이면 전체)
            status: 상품 상태 필터 (None이면 전체)
            skip: 건너뛸 레코드 수
            limit: 최대 반환 수

        Returns:
            필터 조건에 맞는 상품 목록
        """
        return await self.repo.find_by_filters(
            source_id=source_id,
            brand_id=brand_id,
            status=status,
            skip=skip,
            limit=limit,
        )
