from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, JSON
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Numeric, func, UniqueConstraint


class ProductStatusEnum(str, Enum):
    COLLECTED = "collected"      # 수집됨
    REGISTERED = "registered"    # 마켓 등록됨
    INACTIVE = "inactive"        # 비활성


class MonitoringGradeEnum(str, Enum):
    HIGH = "high"      # 인기/재고 적음 → 10-15분 주기
    NORMAL = "normal"  # 일반 → 30분-1시간 주기


class StockStatusEnum(str, Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"


class Product(SQLModel, table=True):
    """상품 테이블"""
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("source_id", "source_product_id", name="uq_source_product"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="sources.id", nullable=False)
    brand_id: int = Field(foreign_key="brands.id", nullable=False)
    name: str = Field(sa_column=Column(String(500), nullable=False))
    original_price: int = Field(sa_column=Column(Integer, nullable=False))  # 원가 (원)
    thumbnail_url: Optional[str] = Field(default=None, sa_column=Column(String(1000)))
    image_urls: Optional[list] = Field(default=None, sa_column=Column(JSON))  # 대표사진 URLs
    source_url: str = Field(sa_column=Column(String(1000), nullable=False))
    source_product_id: str = Field(sa_column=Column(String(200), nullable=False))  # 소싱처 고유 ID
    source_category: Optional[str] = Field(default=None, sa_column=Column(String(500)))  # 소싱처 원본 카테고리
    mapped_category: Optional[str] = Field(default=None, sa_column=Column(String(500)))  # 매핑된 마켓 카테고리
    stock_status: StockStatusEnum = Field(default=StockStatusEnum.IN_STOCK)
    monitoring_grade: MonitoringGradeEnum = Field(default=MonitoringGradeEnum.NORMAL)
    status: ProductStatusEnum = Field(default=ProductStatusEnum.COLLECTED)
    last_crawled_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=func.now()),
    )


class ProductOptionGroup(SQLModel, table=True):
    """상품 옵션 그룹 (색상, 사이즈 등)"""
    __tablename__ = "product_option_groups"

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", nullable=False)
    group_name: str = Field(sa_column=Column(String(100), nullable=False))  # "색상", "사이즈"
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ProductOptionValue(SQLModel, table=True):
    """옵션 그룹의 값 (블랙, M 등)"""
    __tablename__ = "product_option_values"

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="product_option_groups.id", nullable=False)
    value: str = Field(sa_column=Column(String(200), nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ProductVariant(SQLModel, table=True):
    """옵션 조합별 재고/가격 (블랙/M, 블랙/L 등)"""
    __tablename__ = "product_variants"

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", nullable=False)
    option_combination: Optional[dict] = Field(default=None, sa_column=Column(JSON))  # {"색상": "블랙", "사이즈": "M"}
    stock_status: StockStatusEnum = Field(default=StockStatusEnum.IN_STOCK)
    additional_price: int = Field(default=0)  # 추가 가격
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=func.now()),
    )
