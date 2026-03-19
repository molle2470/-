"""수집 설정 CRUD API 라우터.

대시보드에서 사용하는 API — 기존 JWT 인증 적용.
쓰기(POST/PUT/DELETE) 엔드포인트는 인증 필수, GET은 대시보드 읽기 허용.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.orm import get_read_session_dependency, get_write_session_dependency
from backend.domain.collection.service import CollectionService
from backend.domain.user.auth_service import get_user_id
from backend.dtos.collection import (
    CollectionSettingCreateRequest,
    CollectionSettingResponse,
    CollectionSettingUpdateRequest,
)

router = APIRouter(prefix="/collection-settings", tags=["collection-settings"])


@router.post("", response_model=CollectionSettingResponse)
async def create_setting(
    data: CollectionSettingCreateRequest,
    user_id: str = Depends(get_user_id),
    session: AsyncSession = Depends(get_write_session_dependency),
):
    """수집 설정 생성 (인증 필수)"""
    service = CollectionService(session)
    setting = await service.create_setting(data)
    return setting


@router.get("", response_model=List[CollectionSettingResponse])
async def list_settings(
    session: AsyncSession = Depends(get_read_session_dependency),
):
    """수집 설정 목록 (대시보드 읽기 허용)"""
    service = CollectionService(session)
    return await service.list_settings()


@router.get("/{setting_id}", response_model=CollectionSettingResponse)
async def get_setting(
    setting_id: int,
    session: AsyncSession = Depends(get_read_session_dependency),
):
    """수집 설정 상세 (대시보드 읽기 허용)"""
    service = CollectionService(session)
    setting = await service.get_setting(setting_id)
    if not setting:
        raise HTTPException(status_code=404, detail="수집 설정을 찾을 수 없습니다")
    return setting


@router.put("/{setting_id}", response_model=CollectionSettingResponse)
async def update_setting(
    setting_id: int,
    data: CollectionSettingUpdateRequest,
    user_id: str = Depends(get_user_id),
    session: AsyncSession = Depends(get_write_session_dependency),
):
    """수집 설정 수정 (인증 필수)"""
    service = CollectionService(session)
    result = await service.update_setting(setting_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="수집 설정을 찾을 수 없습니다")
    return result


@router.delete("/{setting_id}")
async def delete_setting(
    setting_id: int,
    user_id: str = Depends(get_user_id),
    session: AsyncSession = Depends(get_write_session_dependency),
):
    """수집 설정 삭제 (인증 필수)"""
    service = CollectionService(session)
    success = await service.delete_setting(setting_id)
    if not success:
        raise HTTPException(status_code=404, detail="수집 설정을 찾을 수 없습니다")
    return {"status": "ok"}
