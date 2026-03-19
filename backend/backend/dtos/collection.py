"""수집 설정 DTO."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CollectionSettingCreateRequest(BaseModel):
    """수집 설정 생성"""
    name: str = Field(..., min_length=1, max_length=200)
    source_id: int
    brand_name: str = Field(..., min_length=1, max_length=200)
    category_url: str
    max_count: int = Field(default=500, ge=1, le=5000)


class CollectionSettingUpdateRequest(BaseModel):
    """수집 설정 수정"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    brand_name: Optional[str] = Field(None, min_length=1, max_length=200)
    category_url: Optional[str] = None
    max_count: Optional[int] = Field(None, ge=1, le=5000)
    is_active: Optional[bool] = None


class CollectionSettingResponse(BaseModel):
    """수집 설정 응답"""
    id: int
    name: str
    source_id: int
    brand_name: str
    category_url: str
    max_count: int
    is_active: bool
    last_collected_at: Optional[datetime] = None  # str → Optional[datetime] (ORM 직렬화 오류 방지)
    collected_count: int
    created_at: datetime  # str → datetime
    updated_at: datetime  # str → datetime

    class Config:
        from_attributes = True
