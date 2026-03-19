"""
모니터링(Monitoring) 도메인 SQLModel 모델.

Table Structure:
- PriceStockHistory: 가격/재고 변동 이력
- CrawlJob: 크롤링 작업 관리
- Notification: 사용자 알림
- CategoryMapping: 소싱처-마켓 카테고리 매핑
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Float, func, Index


class ChangeTypeEnum(str, Enum):
    PRICE_CHANGE = "price_change"
    OUT_OF_STOCK = "out_of_stock"
    RESTOCKED = "restocked"


class CrawlJobStatusEnum(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class NotificationTypeEnum(str, Enum):
    PRICE_CHANGE = "price_change"
    OUT_OF_STOCK = "out_of_stock"
    RESTOCKED = "restocked"
    CRAWL_ERROR = "crawl_error"
    MARKET_SYNC_ERROR = "market_sync_error"


class PriceStockHistory(SQLModel, table=True):
    """가격/재고 변동 이력"""
    __tablename__ = "price_stock_history"
    __table_args__ = (
        Index("idx_psh_product_created", "product_id", "created_at"),
        Index("idx_psh_type_created", "change_type", "created_at"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", nullable=False)
    change_type: ChangeTypeEnum = Field(
        ...,
        sa_column=Column(Text, nullable=False),
    )
    previous_value: Optional[str] = Field(default=None, sa_column=Column(String(200)))
    new_value: Optional[str] = Field(default=None, sa_column=Column(String(200)))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class CrawlJob(SQLModel, table=True):
    """크롤링 작업"""
    __tablename__ = "crawl_jobs"

    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="sources.id", nullable=False)
    brand_id: Optional[int] = Field(default=None, foreign_key="brands.id")
    source_url: str = Field(sa_column=Column(String(1000), nullable=False))
    target_count: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default="0"),
    )
    collected_count: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default="0"),
    )
    status: CrawlJobStatusEnum = Field(
        default=CrawlJobStatusEnum.PENDING,
        sa_column=Column(Text, nullable=False),
    )
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))
    started_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    completed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=func.now()),
    )


class Notification(SQLModel, table=True):
    """사용자 알림"""
    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    notification_type: NotificationTypeEnum = Field(
        ...,
        sa_column=Column(Text, nullable=False),
    )
    product_id: Optional[int] = Field(default=None, foreign_key="products.id")
    message: str = Field(sa_column=Column(Text, nullable=False))
    is_read: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default="false"),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class CategoryMapping(SQLModel, table=True):
    """소싱처-마켓 카테고리 매핑"""
    __tablename__ = "category_mappings"

    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="sources.id", nullable=False)
    source_category: str = Field(sa_column=Column(String(500), nullable=False))
    market_id: int = Field(foreign_key="markets.id", nullable=False)
    market_category_id: str = Field(sa_column=Column(String(200), nullable=False))
    market_category_name: Optional[str] = Field(default=None, sa_column=Column(String(500)))
    confidence: float = Field(
        default=0.0,
        sa_column=Column(Float, nullable=False, server_default="0.0"),
    )
    is_confirmed: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default="false"),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=func.now()),
    )
