"""네이버 SEO 데이터 모델."""
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, JSON
from sqlalchemy import Column, String, DateTime, UniqueConstraint


class ProductSeo(SQLModel, table=True):
    """상품별 네이버 SEO 데이터 테이블"""
    __tablename__ = "product_seo"
    __table_args__ = (
        UniqueConstraint("product_id", "market_type", name="uq_product_market_seo"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    market_type: str = Field(
        default="naver",
        sa_column=Column(String(50), nullable=False),
    )

    # 검색 노출
    optimized_name: str = Field(sa_column=Column(String(200), nullable=False))
    tags: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))  # 최대 10개, 항상 리스트
    naver_category_id: Optional[str] = Field(
        default=None, sa_column=Column(String(100))
    )

    # 상품 속성
    brand: str = Field(sa_column=Column(String(200), nullable=False))
    material: Optional[str] = Field(default=None, sa_column=Column(String(500)))
    color: Optional[str] = Field(default=None, sa_column=Column(String(200)))
    gender: Optional[str] = Field(default=None, sa_column=Column(String(50)))
    age_group: str = Field(default="성인", sa_column=Column(String(50), nullable=False))
    origin: str = Field(default="해외", sa_column=Column(String(100), nullable=False))

    # 메타
    status: str = Field(
        default="generated",
        sa_column=Column(String(20), nullable=False),
    )  # "generated" | "edited" | "fallback" | "failed"
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    edited_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
