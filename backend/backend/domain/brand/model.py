"""
브랜드 도메인 SQLModel 모델.

Table Structure:
- Brand: 브랜드 마스터 테이블 (지재권 승인 여부 포함)
"""
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, Boolean, DateTime, func


class Brand(SQLModel, table=True):
    """브랜드 마스터 테이블"""
    __tablename__ = "brands"

    id: Optional[int] = Field(default=None, primary_key=True)
    # 브랜드명 (유니크 제약)
    name: str = Field(sa_column=Column(String(200), nullable=False, unique=True))
    # 지재권 승인 여부 (False: 취급 불가 브랜드)
    is_ip_approved: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default="false")
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=func.now()),
    )
