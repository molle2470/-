"""
마켓(Market) 도메인 SQLModel 모델.

Table Structure:
- BusinessGroup: 사업자 그룹
- Market: 마켓 종류
- MarketAccount: 마켓 계정 (사업자 × 마켓)
- CommonTemplate: 공통 기본값 템플릿 (1단계)
- MarketTemplate: 마켓별 템플릿 (2단계)
- SeoRule: 마켓별 SEO 규칙
- CoupangBrandClearance: 쿠팡 브랜드 소명
- MarketListing: 마켓 등록 내역
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field, JSON
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, func


class ClearanceTypeEnum(str, Enum):
    IP_RIGHT = "ip_right"          # 지재권
    COUNTERFEIT = "counterfeit"    # 가품의심 유통경로


class ClearanceStatusEnum(str, Enum):
    COMPLETED = "completed"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"


class ListingStatusEnum(str, Enum):
    PENDING = "pending"
    REGISTERED = "registered"
    FAILED = "failed"
    DEACTIVATED = "deactivated"


class BusinessGroup(SQLModel, table=True):
    """사업자 그룹"""
    __tablename__ = "business_groups"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String(100), nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class Market(SQLModel, table=True):
    """마켓 종류 (쿠팡, 스마트스토어 등)"""
    __tablename__ = "markets"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String(100), nullable=False, unique=True))
    header_image_url: Optional[str] = Field(default=None, sa_column=Column(String(1000)))
    footer_image_url: Optional[str] = Field(default=None, sa_column=Column(String(1000)))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class MarketAccount(SQLModel, table=True):
    """마켓 계정 (사업자 × 마켓)"""
    __tablename__ = "market_accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    business_group_id: int = Field(foreign_key="business_groups.id", nullable=False)
    market_id: int = Field(foreign_key="markets.id", nullable=False)
    account_id: str = Field(sa_column=Column(String(200), nullable=False))
    api_credentials: Optional[dict] = Field(default=None, sa_column=Column(JSON))  # 암호화 저장 필요
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default="true"),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=func.now()),
    )


class CommonTemplate(SQLModel, table=True):
    """공통 기본값 템플릿 (3단계 구조의 1단계)"""
    __tablename__ = "common_templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    shipping_origin: Optional[str] = Field(default=None, sa_column=Column(String(500)))       # 출고지
    return_address: Optional[str] = Field(default=None, sa_column=Column(String(500)))        # 반품/교환지
    courier: Optional[str] = Field(default=None, sa_column=Column(String(100)))               # 택배사
    as_phone: Optional[str] = Field(default=None, sa_column=Column(String(20)))               # A/S 전화번호
    as_description: Optional[str] = Field(default=None, sa_column=Column(Text))               # A/S 안내문구
    origin_country: str = Field(default="기타", sa_column=Column(String(50), nullable=False))  # 원산지 (server_default 제거 - 한글 인코딩 위험)
    kc_cert_info: Optional[str] = Field(default=None, sa_column=Column(String(200)))          # KC인증 정보
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=func.now()),
    )


class MarketTemplate(SQLModel, table=True):
    """마켓별 템플릿 (3단계 구조의 2단계 - 공통값 상속)"""
    __tablename__ = "market_templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    market_id: int = Field(foreign_key="markets.id", nullable=False)
    common_template_id: int = Field(foreign_key="common_templates.id", nullable=False)
    commission_rate: float = Field(
        default=0.0,
        sa_column=Column(Float, nullable=False, server_default="0.0"),
    )  # 마켓수수료 (예: 0.08 = 8%)
    margin_rate: float = Field(
        default=0.0,
        sa_column=Column(Float, nullable=False, server_default="0.0"),
    )  # 마진율 (예: 0.20 = 20%)
    shipping_fee: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default="0"),
    )  # 배송비
    jeju_extra_fee: int = Field(
        default=5000,
        sa_column=Column(Integer, nullable=False, server_default="5000"),
    )  # 제주 추가 배송비
    island_extra_fee: int = Field(
        default=5000,
        sa_column=Column(Integer, nullable=False, server_default="5000"),
    )  # 도서산간 추가 배송비
    return_fee: int = Field(
        default=5000,
        sa_column=Column(Integer, nullable=False, server_default="5000"),
    )  # 반품 배송비
    product_name_max_length: int = Field(
        default=100,
        sa_column=Column(Integer, nullable=False, server_default="100"),
    )  # 상품명 길이 제한
    discount_rate: float = Field(
        default=0.0,
        sa_column=Column(Float, nullable=False, server_default="0.0"),
    )  # 할인율
    market_specific_config: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    product_info_notice_template: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    # 공통 템플릿 오버라이드 필드 (NULL이면 공통값 사용)
    shipping_origin_override: Optional[str] = Field(default=None, sa_column=Column(String(500)))
    return_address_override: Optional[str] = Field(default=None, sa_column=Column(String(500)))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=func.now()),
    )


class SeoRule(SQLModel, table=True):
    """마켓별 SEO 규칙"""
    __tablename__ = "seo_rules"

    id: Optional[int] = Field(default=None, primary_key=True)
    market_id: int = Field(foreign_key="markets.id", nullable=False)
    tag_pattern: Optional[str] = Field(default=None, sa_column=Column(Text))
    title_pattern: Optional[str] = Field(default=None, sa_column=Column(Text))
    meta_description_pattern: Optional[str] = Field(default=None, sa_column=Column(Text))
    keyword_rules: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=func.now()),
    )


class CoupangBrandClearance(SQLModel, table=True):
    """쿠팡 브랜드 소명 (계정별 × 브랜드별)

    주의: 쿠팡은 카탈로그 매칭 절대 금지. 소명 완료된 브랜드만 쿠팡에 등록 가능.
    """
    __tablename__ = "coupang_brand_clearances"

    id: Optional[int] = Field(default=None, primary_key=True)
    brand_id: int = Field(foreign_key="brands.id", nullable=False)
    market_account_id: int = Field(foreign_key="market_accounts.id", nullable=False)
    clearance_type: ClearanceTypeEnum = Field(
        ...,  # 필수 필드 (지재권 또는 가품의심 - 반드시 명시해야 함)
        sa_column=Column(Text, nullable=False),
    )
    clearance_status: ClearanceStatusEnum = Field(
        default=ClearanceStatusEnum.PENDING,
        sa_column=Column(Text, nullable=False),
    )
    cleared_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=func.now()),
    )


class MarketListing(SQLModel, table=True):
    """마켓 등록 내역 (상품 × 마켓 계정)"""
    __tablename__ = "market_listings"

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", nullable=False)
    market_account_id: int = Field(foreign_key="market_accounts.id", nullable=False)
    selling_price: int = Field(sa_column=Column(Integer, nullable=False))   # 판매가 (자동 계산)
    listing_status: ListingStatusEnum = Field(
        default=ListingStatusEnum.PENDING,
        sa_column=Column(Text, nullable=False),
    )
    market_product_id: Optional[str] = Field(default=None, sa_column=Column(String(200)))
    seo_data: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    registered_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=func.now()),
    )
