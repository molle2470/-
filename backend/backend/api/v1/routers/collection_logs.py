"""수집 로그 조회 + SSE 실시간 스트림.

GET 엔드포인트는 대시보드 읽기 허용 (인증 불필요).
"""
import json
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.orm import get_read_session_dependency
from backend.domain.collection.service import CollectionService
from backend.domain.user.auth_service import get_user_id

router = APIRouter(prefix="/collection-logs", tags=["collection-logs"])


@router.get("")
async def list_logs(
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_read_session_dependency),
):
    """수집 로그 목록"""
    service = CollectionService(session)
    logs = await service.list_logs(limit=limit, skip=skip)
    return [
        {
            "id": log.id,
            "setting_id": log.setting_id,
            "product_name": log.product_name,
            "status": log.status,
            "message": log.message,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


# sse-starlette 설치 여부에 따라 분기
try:
    import asyncio

    from sse_starlette.sse import EventSourceResponse

    @router.get("/stream")
    async def stream_logs():
        """SSE 실시간 로그 스트림 (Phase 1: heartbeat만)"""
        async def event_generator():
            while True:
                yield {"event": "heartbeat", "data": json.dumps({"status": "alive"})}
                await asyncio.sleep(5)
        return EventSourceResponse(event_generator())

except ImportError:
    @router.get("/stream")
    async def stream_logs():  # type: ignore[misc]
        """SSE 실시간 로그 스트림 — Phase 2에서 sse-starlette 설치 후 구현"""
        return {"status": "ok", "message": "SSE not available in Phase 1"}
