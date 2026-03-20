"""상품 관리 API 라우터.

GET 엔드포인트는 대시보드 읽기 허용 (인증 불필요).
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.orm import get_read_session_dependency, get_write_session_dependency
from backend.domain.product.model import ProductStatusEnum
from backend.domain.product.seo_repository import ProductSeoRepository
from backend.domain.product.service import ProductService
from backend.dtos.seo import SeoUpdateRequest

router = APIRouter(prefix="/products", tags=["products"])


@router.get("")
async def list_products(
    source_id: Optional[int] = Query(None),
    brand_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_read_session_dependency),
):
    """수집된 상품 목록 (대시보드 읽기 허용)"""
    service = ProductService(session)
    # 잘못된 status 값은 500이 아닌 400으로 처리
    try:
        status_enum = ProductStatusEnum(status) if status else None
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"유효하지 않은 status 값: {status}",
        )
    products = await service.list_products(
        source_id=source_id,
        brand_id=brand_id,
        status=status_enum,
        skip=skip,
        limit=limit,
    )
    return [
        {
            "id": p.id,
            "name": p.name,
            "original_price": p.original_price,
            "brand_id": p.brand_id,
            "source_url": p.source_url,
            "stock_status": p.stock_status,
            "thumbnail_url": p.thumbnail_url,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in products
    ]


@router.get("/{product_id}")
async def get_product(
    product_id: int,
    session: AsyncSession = Depends(get_read_session_dependency),
):
    """상품 상세"""
    service = ProductService(session)
    product = await service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
    return {
        "id": product.id,
        "name": product.name,
        "original_price": product.original_price,
        "brand_id": product.brand_id,
        "source_id": product.source_id,
        "source_url": product.source_url,
        "source_product_id": product.source_product_id,
        "stock_status": product.stock_status,
        "thumbnail_url": product.thumbnail_url,
        "image_urls": product.image_urls,
        "status": product.status,
        "created_at": product.created_at.isoformat() if product.created_at else None,
    }


@router.get("/{product_id}/seo")
async def get_product_seo(
    product_id: int,
    market_type: str = Query(default="naver"),
    session: AsyncSession = Depends(get_read_session_dependency),
):
    """상품 SEO 데이터 조회"""
    repo = ProductSeoRepository(session)
    seo = await repo.find_by_product_id(product_id, market_type)
    if not seo:
        raise HTTPException(status_code=404, detail="SEO 데이터가 없습니다")
    return {
        "id": seo.id,
        "product_id": seo.product_id,
        "market_type": seo.market_type,
        "optimized_name": seo.optimized_name,
        "tags": seo.tags,
        "naver_category_id": seo.naver_category_id,
        "brand": seo.brand,
        "material": seo.material,
        "color": seo.color,
        "gender": seo.gender,
        "age_group": seo.age_group,
        "origin": seo.origin,
        "status": seo.status,
        "generated_at": seo.generated_at.isoformat() if seo.generated_at else None,
        "edited_at": seo.edited_at.isoformat() if seo.edited_at else None,
    }


@router.patch("/{product_id}/seo")
async def update_product_seo(
    product_id: int,
    data: SeoUpdateRequest,
    market_type: str = Query(default="naver"),
    session: AsyncSession = Depends(get_write_session_dependency),
):
    """상품 SEO 데이터 수정 (대시보드에서 편집 시)"""
    repo = ProductSeoRepository(session)
    seo = await repo.find_by_product_id(product_id, market_type)
    if not seo:
        raise HTTPException(status_code=404, detail="SEO 데이터가 없습니다")

    update_fields = data.model_dump(exclude_unset=True)
    update_fields["status"] = "edited"
    update_fields["edited_at"] = datetime.now(tz=timezone.utc)

    updated = await repo.update_async(seo.id, **update_fields)
    return {"status": "ok", "seo_id": updated.id}
