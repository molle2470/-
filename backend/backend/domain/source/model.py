"""
소싱처 도메인 SQLModel 모델.

Table Structure:
- Source: 소싱처 마스터 테이블 (무신사, SSG 등)
- SourceBrand: 소싱처별 브랜드 표기명 매핑 테이블
"""
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, Boolean, DateTime, func


class Source(SQLModel, table=True):
    """소싱처 테이블"""
    __tablename__ = "sources"

    id: Optional[int] = Field(default=None, primary_key=True)
    # 소싱처 이름 (예: 무신사, SSG)
    name: str = Field(sa_column=Column(String(100), nullable=False))
    # 소싱처 기본 URL
    base_url: str = Field(sa_column=Column(String(500), nullable=False))
    # 크롤러 타입 식별자 (예: musinsa, ssg)
    crawler_type: str = Field(sa_column=Column(String(50), nullable=False))
    # 소싱처 활성화 여부
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, default=True)
    )
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )


class SourceBrand(SQLModel, table=True):
    """소싱처별 브랜드 매핑 - 소싱처마다 브랜드 표기명이 다름"""
    __tablename__ = "source_brands"

    id: Optional[int] = Field(default=None, primary_key=True)
    # 브랜드 마스터 참조
    brand_id: int = Field(foreign_key="brands.id", nullable=False)
    # 소싱처 참조
    source_id: int = Field(foreign_key="sources.id", nullable=False)
    # 해당 소싱처 내에서의 브랜드 표기명 (예: NIKE, 나이키)
    display_name: str = Field(sa_column=Column(String(200), nullable=False))
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
