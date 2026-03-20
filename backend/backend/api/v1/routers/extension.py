"""익스텐션 통신 API 라우터.

익스텐션이 폴링하는 명령 큐, 수집 데이터 수신, heartbeat 처리.
인증: X-Extension-Key 헤더 (Phase 1은 간단한 API 키)
"""
from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.db.orm import get_read_session_dependency, get_write_session_dependency
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


def _debug_log(msg: str) -> None:
    """디버그 로그를 파일에 기록 (stdout이 안 보이는 환경 대비)"""
    import datetime
    with open("debug_collect.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now()}] {msg}\n")


def verify_extension_key(x_extension_key: str = Header(...)) -> str:
    """익스텐션 API 키 검증"""
    if x_extension_key != settings.extension_api_key:
        raise HTTPException(status_code=401, detail="유효하지 않은 익스텐션 키")
    return x_extension_key


@router.get("/commands")
async def get_pending_commands(
    _key: str = Depends(verify_extension_key),
    session: AsyncSession = Depends(get_read_session_dependency),
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
    import traceback, sys
    _debug_log("요청 도착: " + data.product.name[:30])
    try:
        service = CollectionService(session)
        result = await service.process_collected_product(
            source=data.source,
            product_data=data.product,
            source_id=1,
        )
        product = result["product"]
        _debug_log(f"성공 product_id={product.id}")
        response: dict = {"status": "ok", "product_id": product.id}
        if result.get("ip_warning"):
            response["warning"] = result["ip_warning"]
        return response
    except Exception as e:
        _debug_log(f"에러: {type(e).__name__}: {e}\n{traceback.format_exc()}")
        raise


@router.post("/products/{product_id}/changes")
async def receive_product_changes(
    product_id: int,
    data: ProductChangeRequest,
    _key: str = Depends(verify_extension_key),
) -> dict:
    """모니터링 변동 데이터 수신 — Phase 2에서 구현 예정

    TODO: Phase 2에서 NaverAdapter 연동 구현
    - settings에서 naver_client_id, naver_client_secret, naver_channel_id 읽기
    - NaverAdapter(client_id=..., client_secret=..., channel_id=...) 생성
    - MarketSyncService로 가격/재고 동기화 처리
    """
    return {"status": "ok", "updated_listings": []}


@router.post("/heartbeat")
async def receive_heartbeat(
    data: HeartbeatRequest,
    _key: str = Depends(verify_extension_key),
) -> dict:
    """익스텐션 생존 신호"""
    # Phase 1: 로그만 기록, Phase 2에서 offline 감지 추가
    return {"status": "ok"}
