"""
소싱처 도메인 SQLModel 모델.

Table Structure:
- Source: 소싱처 마스터 테이블 (무신사, SSG 등)
- SourceBrand: 소싱처별 브랜드 표기명 매핑 테이블
- SourceAccount: 소싱처 계정 테이블 (등급별 할인/적립 관리)
"""
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, Text, func


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
        sa_column=Column(Boolean, nullable=False, server_default="true")
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=func.now()),
    )


class AccountRoleEnum(str):
    """소싱처 계정 역할"""
    PRICE_BASE = "price_base"          # 가격 기준 계정 (중간 등급)
    PRIMARY_BUYER = "primary_buyer"    # 주결제 계정 (높은 등급)
    BACKUP = "backup"                  # 백업 결제 계정
    MONITOR = "monitor"                # 모니터링 전용 계정


class SourceAccount(SQLModel, table=True):
    """소싱처 계정 - 등급별 할인/적립 관리

    무신사 등 소싱처 아이디별로 등급이 다르며,
    등급에 따라 할인율, 적립률, 적립금 사용 한도가 달라집니다.
    가격 기준은 중간 등급(price_base) 계정을 사용하고,
    실결제는 높은 등급(primary_buyer) 계정을 사용합니다.
    """
    __tablename__ = "source_accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    # 소싱처 참조
    source_id: int = Field(foreign_key="sources.id", nullable=False)
    # 계정 식별 이름 (예: 무신사 아이디 닉네임)
    account_name: str = Field(sa_column=Column(String(100), nullable=False))
    # 등급명 (예: 화이트, 블루, 레드, VIP, VVIP)
    grade: str = Field(sa_column=Column(String(50), nullable=False))
    # 등급 기본 할인율 (예: 0.03 = 3%)
    base_discount_rate: float = Field(
        default=0.0,
        sa_column=Column(Float, nullable=False, server_default="0.0"),
    )
    # 적립률 (예: 0.01 = 1%)
    point_rate: float = Field(
        default=0.0,
        sa_column=Column(Float, nullable=False, server_default="0.0"),
    )
    # 적립금 사용 한도 비율 (예: 0.05 = 결제금액의 5%까지 사용 가능)
    point_use_limit: float = Field(
        default=0.0,
        sa_column=Column(Float, nullable=False, server_default="0.0"),
    )
    # 현재 보유 적립금
    available_points: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default="0"),
    )
    # 계정 역할
    role: str = Field(
        default=AccountRoleEnum.MONITOR,
        sa_column=Column(Text, nullable=False),
    )
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

    def calculate_effective_cost(
        self,
        original_price: int,
        grade_discount_available: bool = True,
        point_usable: bool = True,
    ) -> int:
        """등급 할인 적용한 실구매가 계산 (확정 혜택만 반영)

        상품마다 등급 할인, 적립금 사용 가능 여부가 다르므로
        상품별 혜택 플래그를 반드시 전달해야 합니다.

        Args:
            original_price: 상품 정가
            grade_discount_available: 등급 할인 가능 여부 (상품별로 다름)
            point_usable: 적립금 사용 가능 여부 (상품별로 다름)

        Returns:
            실구매가 (적용 가능한 혜택만 반영)
        """
        discount = 0
        if grade_discount_available:
            discount = int(original_price * self.base_discount_rate)

        point_use = 0
        if point_usable:
            max_point_use = int(original_price * self.point_use_limit)
            point_use = min(self.available_points, max_point_use)

        return original_price - discount - point_use


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
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=func.now()),
    )
