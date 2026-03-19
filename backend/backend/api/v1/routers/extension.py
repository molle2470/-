"""익스텐션 통신 API 라우터.

익스텐션이 폴링하는 명령 큐, 수집 데이터 수신, heartbeat 처리.
인증: X-Extension-Key 헤더 (Phase 1은 간단한 API 키)
"""
from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.orm import get_write_session_dependency
from backend.domain.collection.service import (
    CollectionService,
    ExtensionCommandService,
)
from backend.dtos.extension import (
    ExtensionProductRequest,
    ProductChangeRequest,
    CommandAckRequest,
    HeartbeatRequest,
)

router = APIRouter(prefix="/extension", tags=["extension"])

# Phase 1: 간단한 API 키 검증 (TODO: settings에서 읽기)
EXTENSION_API_KEY = "sourcing-extension-phase1-key"


def verify_extension_key(x_extension_key: str = Header(...)) -> str:
    """익스텐션 API 키 검증"""
    if x_extension_key != EXTENSION_API_KEY:
        raise HTTPException(status_code=401, detail="유효하지 않은 익스텐션 키")
    return x_extension_key


@router.get("/commands")
async def get_pending_commands(
    _key: str = Depends(verify_extension_key),
    session: AsyncSession = Depends(get_write_session_dependency),
) -> List[dict]:
    """대기 중인 명령 조회 (익스텐션 폴링)"""
    service = ExtensionCommandService(session)
    commands = await service.get_pending_commands()
    return [
        {
            "id": cmd.id,
            "command_type": cmd.command_type,
            "payload": cmd.payload,
        }
        for cmd in commands
    ]


@router.post("/commands/{command_id}/ack")
async def ack_command(
    command_id: int,
    data: CommandAckRequest,
    _key: str = Depends(verify_extension_key),
    session: AsyncSession = Depends(get_write_session_dependency),
) -> dict:
    """명령 처리 완료 보고"""
    service = ExtensionCommandService(session)
    result = await service.ack_command(
        command_id=command_id,
        status=data.status,
        message=data.message,
    )
    if not result:
        raise HTTPException(status_code=404, detail="명령을 찾을 수 없습니다")
    return {"status": "ok"}


@router.post("/products")
async def receive_collected_product(
    data: ExtensionProductRequest,
    _key: str = Depends(verify_extension_key),
    session: AsyncSession = Depends(get_write_session_dependency),
) -> dict:
    """수집된 상품 데이터 수신"""
    service = CollectionService(session)
    # TODO: source_id를 source 문자열로부터 조회하는 로직 추가
    result = await service.process_collected_product(
        source=data.source,
        product_data=data.product,
        source_id=1,  # Phase 1: 무신사 고정. Phase 2에서 소싱처 조회
    )
    product = result["product"]
    response: dict = {"status": "ok", "product_id": product.id}
    if result.get("ip_warning"):
        response["warning"] = result["ip_warning"]
    return response


@router.post("/products/{product_id}/changes")
async def receive_product_changes(
    product_id: int,
    data: ProductChangeRequest,
    _key: str = Depends(verify_extension_key),
    session: AsyncSession = Depends(get_write_session_dependency),
) -> dict:
    """모니터링 변동 데이터 수신"""
    from backend.services.market_sync import MarketSyncService
    from backend.adapters.naver_adapter import NaverAdapter

    adapter = NaverAdapter()
    sync = MarketSyncService(session, adapter)

    updated: List[dict] = []
    if data.change_type in ("price", "both") and data.new_price:
        # TODO: MarketTemplate에서 commission_rate, margin_rate 조회
        result = await sync.sync_price_change(
            product_id=product_id,
            new_price=data.new_price,
            commission_rate=0.05,
            margin_rate=0.20,
        )
        updated.extend(result)

    if data.change_type in ("stock", "both") and data.stock_status:
        in_stock = data.stock_status == "in_stock"
        result = await sync.sync_stock_change(
            product_id=product_id,
            in_stock=in_stock,
        )
        updated.extend(result)

    return {"status": "ok", "updated_listings": updated}


@router.post("/heartbeat")
async def receive_heartbeat(
    data: HeartbeatRequest,
    _key: str = Depends(verify_extension_key),
) -> dict:
    """익스텐션 생존 신호"""
    # Phase 1: 로그만 기록, Phase 2에서 offline 감지 추가
    return {"status": "ok"}
