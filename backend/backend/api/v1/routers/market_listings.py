"""마켓 등록 관리 API 라우터.

POST   /market-listings                     — 상품 마켓 등록
GET    /market-listings                     — 등록 목록 조회
PATCH  /market-listings/{id}/deactivate    — 비활성화
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.db.orm import get_read_session_dependency, get_write_session_dependency
from backend.domain.market.model import ListingStatusEnum
from backend.domain.market.repository import MarketListingRepository
from backend.domain.market.service import MarketService
from backend.domain.product.repository import ProductRepository

router = APIRouter(prefix="/market-listings", tags=["market-listings"])


class RegisterRequest(BaseModel):
    """마켓 등록 요청"""
    product_id: int
    market_account_id: int
    market_id: int
    common_template_id: int
    margin_rate: float = 0.2


class ListingResponse(BaseModel):
    """마켓 등록 내역 응답"""
    id: int
    product_id: int
    market_account_id: int
    selling_price: int
    listing_status: str
    market_product_id: Optional[str]
    registered_at: Optional[str]
    created_at: str


def _to_listing_response(listing: object) -> ListingResponse:
    """MarketListing 객체를 ListingResponse DTO로 변환"""
    return ListingResponse(
        id=listing.id,  # type: ignore[attr-defined]
        product_id=listing.product_id,  # type: ignore[attr-defined]
        market_account_id=listing.market_account_id,  # type: ignore[attr-defined]
        selling_price=listing.selling_price,  # type: ignore[attr-defined]
        listing_status=listing.listing_status.value,  # type: ignore[attr-defined]
        market_product_id=listing.market_product_id,  # type: ignore[attr-defined]
        registered_at=listing.registered_at.isoformat() if listing.registered_at else None,  # type: ignore[attr-defined]
        created_at=listing.created_at.isoformat(),  # type: ignore[attr-defined]
    )


@router.post("", status_code=201)
async def register_to_market(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_write_session_dependency),
) -> ListingResponse:
    """상품을 마켓에 등록한다."""
    # 상품 조회 (BaseRepository.get_async 사용)
    product_repo = ProductRepository(session)
    product = await product_repo.get_async(request.product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"상품 ID {request.product_id}을 찾을 수 없습니다.")

    # 네이버 API 설정 확인
    if not all([settings.naver_client_id, settings.naver_client_secret, settings.naver_channel_id]):
        raise HTTPException(status_code=503, detail="네이버 API 설정 없음. 환경변수(NAVER_*) 확인 필요.")

    from backend.adapters.naver_adapter import NaverAdapter
    adapter = NaverAdapter(
        client_id=settings.naver_client_id,
        client_secret=settings.naver_client_secret,
        channel_id=settings.naver_channel_id,
    )

    service = MarketService(session)
    try:
        listing = await service.register_product_to_market(
            product=product,
            market_account_id=request.market_account_id,
            market_id=request.market_id,
            common_template_id=request.common_template_id,
            adapter=adapter,
            margin_rate=request.margin_rate,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    finally:
        await adapter.close()

    return _to_listing_response(listing)


@router.get("")
async def list_listings(
    product_id: Optional[int] = Query(None),
    account_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_read_session_dependency),
) -> List[ListingResponse]:
    """마켓 등록 목록 조회"""
    service = MarketService(session)
    listings = await service.list_listings(product_id=product_id, account_id=account_id)
    return [_to_listing_response(listing) for listing in listings]


@router.patch("/{listing_id}/deactivate")
async def deactivate_listing(
    listing_id: int,
    session: AsyncSession = Depends(get_write_session_dependency),
) -> dict:
    """마켓 등록 상품 비활성화 (DEACTIVATED)"""
    repo = MarketListingRepository(session)
    listing = await repo.get_async(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail=f"등록 ID {listing_id}을 찾을 수 없습니다.")

    # 네이버 API 설정 확인
    if not all([settings.naver_client_id, settings.naver_client_secret, settings.naver_channel_id]):
        raise HTTPException(status_code=503, detail="네이버 API 설정 없음")

    from backend.adapters.naver_adapter import NaverAdapter
    adapter = NaverAdapter(
        client_id=settings.naver_client_id,
        client_secret=settings.naver_client_secret,
        channel_id=settings.naver_channel_id,
    )
    try:
        # market_product_id가 있는 경우에만 네이버 API 호출
        # 예외 발생 시 finally에서 adapter 종료 후 예외가 전파되므로
        # 아래 DB 업데이트(DEACTIVATED)는 실행되지 않음 — 의도된 동작
        if listing.market_product_id:
            await adapter.deactivate_product(listing.market_product_id)
    finally:
        await adapter.close()

    listing.listing_status = ListingStatusEnum.DEACTIVATED
    session.add(listing)
    await session.commit()

    return {"success": True, "listing_id": listing_id}
