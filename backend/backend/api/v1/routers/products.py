"""상품 관리 API 라우터."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.orm import get_read_session_dependency
from backend.domain.product.model import ProductStatusEnum
from backend.domain.product.service import ProductService

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
    """수집된 상품 목록"""
    service = ProductService(session)
    status_enum = ProductStatusEnum(status) if status else None
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
    product = await service.repo.get_async(product_id)
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
