"""SEO 관련 DTO."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SeoResponse(BaseModel):
    """SEO 데이터 응답"""
    id: int
    product_id: int
    market_type: str
    optimized_name: str
    tags: Optional[List[str]] = None
    naver_category_id: Optional[str] = None
    brand: str
    material: Optional[str] = None
    color: Optional[str] = None
    gender: Optional[str] = None
    age_group: str
    origin: str
    status: str
    generated_at: datetime
    edited_at: Optional[datetime] = None


class SeoUpdateRequest(BaseModel):
    """SEO 데이터 수정 요청"""
    optimized_name: Optional[str] = None
    tags: Optional[List[str]] = None
    naver_category_id: Optional[str] = None
    material: Optional[str] = None
    color: Optional[str] = None
    gender: Optional[str] = None
    age_group: Optional[str] = None
    origin: Optional[str] = None
