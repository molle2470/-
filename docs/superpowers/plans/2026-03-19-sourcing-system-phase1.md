# 소싱 통합 시스템 Phase 1 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 무신사에서 상품을 크롤링하고, 가격을 자동 계산하여 네이버 스마트스토어에 등록하며, 등록된 상품의 가격/재고 변동을 모니터링하여 자동 반영하는 Phase 1 테스트 시스템 구축 (10-20개 상품)

**Architecture:** FastAPI 백엔드에 도메인별 서비스 레이어(크롤링/상품/가격/마켓)를 구성하고, Next.js 15 프론트엔드로 대시보드를 구현. APScheduler로 주기적 모니터링 실행. 기존 monorepo의 DDD 패턴(model→repository→service)과 읽기/쓰기 세션 분리를 따름.

**Tech Stack:** FastAPI + SQLModel + PostgreSQL + httpx/Playwright (크롤링) + APScheduler + Next.js 15 + React 19 + TypeScript + Tailwind CSS + shadcn/ui

**설계서:** `docs/superpowers/specs/2026-03-19-sourcing-system-design.md`

---

## 파일 구조

### Backend 신규 파일

```
backend/backend/
├── domain/
│   ├── source/                        # 소싱처 도메인
│   │   ├── model.py                   # Source, SourceBrand 테이블
│   │   ├── repository.py             # CRUD
│   │   └── service.py                # 소싱처 관리 로직
│   │
│   ├── brand/                         # 브랜드 도메인
│   │   ├── model.py                   # Brand 마스터 테이블
│   │   ├── repository.py
│   │   └── service.py
│   │
│   ├── product/                       # 상품 도메인
│   │   ├── model.py                   # Product, ProductOptionGroup, ProductOptionValue, ProductVariant
│   │   ├── repository.py
│   │   └── service.py
│   │
│   ├── market/                        # 마켓 도메인
│   │   ├── model.py                   # Market, BusinessGroup, MarketAccount, MarketListing
│   │   │                              # CommonTemplate, MarketTemplate, SeoRule
│   │   │                              # CoupangBrandClearance
│   │   ├── repository.py
│   │   └── service.py
│   │
│   ├── monitoring/                    # 모니터링 도메인
│   │   ├── model.py                   # PriceStockHistory, CrawlJob, Notification
│   │   ├── repository.py
│   │   └── service.py
│   │
│   └── crawling/                      # 크롤링 엔진
│       ├── base_crawler.py            # BaseCrawler 추상 클래스
│       ├── musinsa_crawler.py         # 무신사 전용 크롤러
│       └── crawler_manager.py         # 크롤러 매니저
│
├── services/                          # 크로스 도메인 서비스
│   ├── price_calculator.py            # 가격 계산 서비스
│   ├── seo_generator.py               # SEO 자동 생성 서비스
│   ├── market_sync.py                 # 마켓 동기화 서비스
│   └── scheduler.py                   # APScheduler 모니터링 스케줄러
│
├── adapters/                          # 마켓 API 어댑터
│   ├── base_adapter.py                # BaseMarketAdapter 추상 클래스
│   └── naver_adapter.py               # 네이버 스마트스토어 Commerce API
│
├── api/v1/routers/
│   ├── sources.py                     # 소싱처 관리 API
│   ├── brands.py                      # 브랜드 관리 API
│   ├── products.py                    # 상품 관리 API
│   ├── markets.py                     # 마켓/계정/템플릿 API
│   ├── crawling.py                    # 크롤링 작업 API
│   └── monitoring.py                  # 모니터링/알림 API
│
└── dtos/
    ├── source.py                      # 소싱처 DTO
    ├── brand.py                       # 브랜드 DTO
    ├── product.py                     # 상품 DTO
    ├── market.py                      # 마켓/템플릿 DTO
    ├── crawling.py                    # 크롤링 DTO
    └── monitoring.py                  # 모니터링/알림 DTO
```

### Frontend 신규 파일

```
frontend/src/
├── app/
│   └── sourcing/                      # 소싱 대시보드 앱
│       ├── layout.tsx                 # 사이드바 레이아웃
│       ├── page.tsx                   # 대시보드 홈
│       ├── sources/page.tsx           # 소싱처 관리
│       ├── brands/page.tsx            # 브랜드 관리
│       ├── products/page.tsx          # 상품 목록
│       ├── products/[id]/page.tsx     # 상품 상세
│       ├── crawl/page.tsx             # 새 소싱 작업
│       ├── markets/page.tsx           # 마켓/계정 관리
│       ├── markets/templates/page.tsx # 마켓 템플릿 설정
│       ├── markets/coupang/page.tsx   # 쿠팡 소명 관리
│       ├── monitoring/page.tsx        # 크롤링 현황
│       └── notifications/page.tsx     # 알림 센터
│
├── components/
│   └── sourcing/                      # 소싱 전용 컴포넌트
│       ├── layout/
│       │   └── Sidebar.tsx            # 사이드바 네비게이션
│       ├── dashboard/
│       │   ├── StatsCards.tsx          # 통계 카드
│       │   └── RecentAlerts.tsx       # 최근 알림
│       ├── products/
│       │   ├── ProductTable.tsx        # 상품 테이블
│       │   ├── ProductFilters.tsx      # 필터 UI
│       │   └── UploadModal.tsx         # 마켓 업로드 모달
│       ├── crawl/
│       │   ├── SourceSelector.tsx      # 소싱처 선택
│       │   ├── BrandSelector.tsx       # 브랜드 체크박스 (갯수 표시)
│       │   ├── CategorySelector.tsx    # 카테고리 체크박스 (갯수 표시)
│       │   └── CrawlProgress.tsx       # 수집 진행률
│       ├── markets/
│       │   ├── TemplateForm.tsx        # 마켓 템플릿 폼
│       │   ├── BusinessGroupSelector.tsx
│       │   └── CoupangClearanceMatrix.tsx  # 쿠팡 소명 매트릭스
│       └── monitoring/
│           ├── CrawlStatusTable.tsx    # 크롤링 현황 테이블
│           └── NotificationList.tsx    # 알림 목록
│
├── lib/
│   └── sourcing-api.ts                # 소싱 전용 API 클라이언트
│
└── types/
    └── sourcing.ts                    # 소싱 타입 정의
```

### 테스트 파일

```
backend/tests/
├── domain/
│   ├── source/test_source_service.py
│   ├── brand/test_brand_service.py
│   ├── product/test_product_service.py
│   ├── market/test_market_service.py
│   └── monitoring/test_monitoring_service.py
├── crawling/
│   ├── test_base_crawler.py
│   └── test_musinsa_crawler.py
├── services/
│   ├── test_price_calculator.py
│   ├── test_seo_generator.py
│   └── test_market_sync.py
└── adapters/
    └── test_naver_adapter.py
```

---

## Task 1: 데이터베이스 모델 (소싱처/브랜드)

**Files:**
- Create: `backend/backend/domain/source/model.py`
- Create: `backend/backend/domain/brand/model.py`
- Create: `backend/backend/domain/source/__init__.py`
- Create: `backend/backend/domain/brand/__init__.py`
- Test: `backend/tests/domain/source/test_source_model.py`

- [ ] **Step 1: Source, Brand, SourceBrand 모델 작성**

```python
# backend/backend/domain/source/model.py
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, Boolean, DateTime, func

class Source(SQLModel, table=True):
    """소싱처 테이블"""
    __tablename__ = "sources"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String(100), nullable=False))
    base_url: str = Field(sa_column=Column(String(500), nullable=False))
    crawler_type: str = Field(sa_column=Column(String(50), nullable=False))  # musinsa, ssg, etc.
    is_active: bool = Field(default=True, sa_column=Column(Boolean, default=True))
    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )


class SourceBrand(SQLModel, table=True):
    """소싱처별 브랜드 매핑 - 소싱처마다 브랜드 표기명이 다름"""
    __tablename__ = "source_brands"

    id: Optional[int] = Field(default=None, primary_key=True)
    brand_id: int = Field(foreign_key="brands.id", nullable=False)
    source_id: int = Field(foreign_key="sources.id", nullable=False)
    display_name: str = Field(sa_column=Column(String(200), nullable=False))  # 소싱처 내 표기명
    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
```

```python
# backend/backend/domain/brand/model.py
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, Boolean, DateTime, func

class Brand(SQLModel, table=True):
    """브랜드 마스터 테이블"""
    __tablename__ = "brands"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String(200), nullable=False, unique=True))
    is_ip_approved: bool = Field(default=False, sa_column=Column(Boolean, default=False))  # 지재권 승인 여부
    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )
```

- [ ] **Step 2: 모델 임포트 테스트 작성 및 실행**

```python
# backend/tests/domain/source/test_source_model.py
from backend.domain.source.model import Source, SourceBrand
from backend.domain.brand.model import Brand

def test_source_model_exists():
    source = Source(name="무신사", base_url="https://www.musinsa.com", crawler_type="musinsa")
    assert source.name == "무신사"
    assert source.crawler_type == "musinsa"

def test_brand_model_exists():
    brand = Brand(name="나이키")
    assert brand.name == "나이키"

def test_source_brand_model_exists():
    sb = SourceBrand(brand_id=1, source_id=1, display_name="NIKE")
    assert sb.display_name == "NIKE"
```

Run: `cd backend && python -m pytest tests/domain/source/test_source_model.py -v`
Expected: PASS

- [ ] **Step 3: 커밋**

```bash
git add backend/backend/domain/source/ backend/backend/domain/brand/ backend/tests/domain/source/
git commit -m "feat: 소싱처(Source) 및 브랜드(Brand) 데이터 모델 추가"
```

---

## Task 2: 데이터베이스 모델 (상품/옵션)

**Files:**
- Create: `backend/backend/domain/product/model.py`
- Create: `backend/backend/domain/product/__init__.py`
- Test: `backend/tests/domain/product/test_product_model.py`

- [ ] **Step 1: Product, ProductOptionGroup, ProductOptionValue, ProductVariant 모델 작성**

```python
# backend/backend/domain/product/model.py
from datetime import datetime
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
    thumbnail_url: Optional[str] = Field(sa_column=Column(String(1000)))
    image_urls: Optional[list] = Field(default=None, sa_column=Column(JSON))  # 대표사진 URLs
    source_url: str = Field(sa_column=Column(String(1000), nullable=False))
    source_product_id: str = Field(sa_column=Column(String(200), nullable=False))  # 소싱처 고유 ID
    source_category: Optional[str] = Field(sa_column=Column(String(500)))  # 소싱처 원본 카테고리
    mapped_category: Optional[str] = Field(sa_column=Column(String(500)))  # 매핑된 마켓 카테고리
    stock_status: StockStatusEnum = Field(default=StockStatusEnum.IN_STOCK)
    monitoring_grade: MonitoringGradeEnum = Field(default=MonitoringGradeEnum.NORMAL)
    status: ProductStatusEnum = Field(default=ProductStatusEnum.COLLECTED)
    last_crawled_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )


class ProductOptionGroup(SQLModel, table=True):
    """상품 옵션 그룹 (색상, 사이즈 등)"""
    __tablename__ = "product_option_groups"

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", nullable=False)
    group_name: str = Field(sa_column=Column(String(100), nullable=False))  # "색상", "사이즈"


class ProductOptionValue(SQLModel, table=True):
    """옵션 그룹의 값 (블랙, M 등)"""
    __tablename__ = "product_option_values"

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="product_option_groups.id", nullable=False)
    value: str = Field(sa_column=Column(String(200), nullable=False))


class ProductVariant(SQLModel, table=True):
    """옵션 조합별 재고/가격 (블랙/M, 블랙/L 등)"""
    __tablename__ = "product_variants"

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", nullable=False)
    option_combination: Optional[dict] = Field(default=None, sa_column=Column(JSON))  # {"색상": "블랙", "사이즈": "M"}
    stock_status: StockStatusEnum = Field(default=StockStatusEnum.IN_STOCK)
    additional_price: int = Field(default=0)  # 추가 가격
```

- [ ] **Step 2: 모델 테스트 작성 및 실행**

```python
# backend/tests/domain/product/test_product_model.py
from backend.domain.product.model import (
    Product, ProductOptionGroup, ProductOptionValue, ProductVariant,
    ProductStatusEnum, MonitoringGradeEnum, StockStatusEnum,
)

def test_product_model():
    p = Product(
        source_id=1, brand_id=1, name="나이키 에어맥스 90",
        original_price=139000, source_url="https://musinsa.com/123",
        source_product_id="musinsa_123",
    )
    assert p.status == ProductStatusEnum.COLLECTED
    assert p.monitoring_grade == MonitoringGradeEnum.NORMAL

def test_product_variant():
    v = ProductVariant(
        product_id=1,
        option_combination={"색상": "블랙", "사이즈": "M"},
        stock_status=StockStatusEnum.IN_STOCK,
    )
    assert v.option_combination["색상"] == "블랙"
```

Run: `cd backend && python -m pytest tests/domain/product/test_product_model.py -v`
Expected: PASS

- [ ] **Step 3: 커밋**

```bash
git add backend/backend/domain/product/ backend/tests/domain/product/
git commit -m "feat: 상품(Product) 및 옵션 데이터 모델 추가"
```

---

## Task 3: 데이터베이스 모델 (마켓/계정/템플릿/소명)

**Files:**
- Create: `backend/backend/domain/market/model.py`
- Create: `backend/backend/domain/market/__init__.py`
- Test: `backend/tests/domain/market/test_market_model.py`

- [ ] **Step 1: Market, BusinessGroup, MarketAccount, CommonTemplate, MarketTemplate, SeoRule, CoupangBrandClearance, MarketListing 모델 작성**

```python
# backend/backend/domain/market/model.py
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field, JSON
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Numeric, func

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
    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )


class Market(SQLModel, table=True):
    """마켓 (쿠팡, 스마트스토어 등)"""
    __tablename__ = "markets"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String(100), nullable=False, unique=True))
    header_image_url: Optional[str] = Field(sa_column=Column(String(1000)))
    footer_image_url: Optional[str] = Field(sa_column=Column(String(1000)))
    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )


class MarketAccount(SQLModel, table=True):
    """마켓 계정 (사업자 × 마켓)"""
    __tablename__ = "market_accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    business_group_id: int = Field(foreign_key="business_groups.id", nullable=False)
    market_id: int = Field(foreign_key="markets.id", nullable=False)
    account_id: str = Field(sa_column=Column(String(200), nullable=False))
    api_credentials: Optional[dict] = Field(default=None, sa_column=Column(JSON))  # API 인증 정보 (암호화 필요)
    is_active: bool = Field(default=True, sa_column=Column(Boolean, default=True))
    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )


class CommonTemplate(SQLModel, table=True):
    """공통 기본값 템플릿 (1단계)"""
    __tablename__ = "common_templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    shipping_origin: Optional[str] = Field(sa_column=Column(String(500)))       # 출고지
    return_address: Optional[str] = Field(sa_column=Column(String(500)))        # 반품/교환지
    courier: Optional[str] = Field(sa_column=Column(String(100)))               # 택배사
    as_phone: Optional[str] = Field(sa_column=Column(String(20)))               # A/S 전화번호
    as_description: Optional[str] = Field(sa_column=Column(Text))               # A/S 안내문구
    origin_country: str = Field(default="기타", sa_column=Column(String(50)))    # 원산지
    kc_cert_info: Optional[str] = Field(sa_column=Column(String(200)))          # KC인증 정보
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )


class MarketTemplate(SQLModel, table=True):
    """마켓별 템플릿 (2단계 - 공통값 상속)"""
    __tablename__ = "market_templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    market_id: int = Field(foreign_key="markets.id", nullable=False)
    common_template_id: int = Field(foreign_key="common_templates.id", nullable=False)
    commission_rate: float = Field(default=0.0)   # 마켓수수료 (예: 0.08 = 8%)
    margin_rate: float = Field(default=0.0)       # 마진율 (예: 0.20 = 20%)
    shipping_fee: int = Field(default=0)          # 배송비
    jeju_extra_fee: int = Field(default=5000)     # 제주 추가 배송비
    island_extra_fee: int = Field(default=5000)   # 도서산간 추가 배송비
    return_fee: int = Field(default=5000)         # 반품 배송비
    product_name_max_length: int = Field(default=100)  # 상품명 길이 제한
    discount_rate: float = Field(default=0.0)     # 할인율
    market_specific_config: Optional[dict] = Field(default=None, sa_column=Column(JSON))  # 마켓 고유 설정
    product_info_notice_template: Optional[dict] = Field(default=None, sa_column=Column(JSON))  # 상품정보제공고시
    # 오버라이드 필드 (NULL이면 공통값 사용)
    shipping_origin_override: Optional[str] = Field(sa_column=Column(String(500)))
    return_address_override: Optional[str] = Field(sa_column=Column(String(500)))
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )


class SeoRule(SQLModel, table=True):
    """마켓별 SEO 규칙"""
    __tablename__ = "seo_rules"

    id: Optional[int] = Field(default=None, primary_key=True)
    market_id: int = Field(foreign_key="markets.id", nullable=False)
    tag_pattern: Optional[str] = Field(sa_column=Column(Text))           # 태그 생성 규칙
    title_pattern: Optional[str] = Field(sa_column=Column(Text))         # Page Title 패턴
    meta_description_pattern: Optional[str] = Field(sa_column=Column(Text))  # Meta Description 패턴
    keyword_rules: Optional[dict] = Field(default=None, sa_column=Column(JSON))  # 키워드 생성 규칙
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )


class CoupangBrandClearance(SQLModel, table=True):
    """쿠팡 브랜드 소명 (쿠팡 계정별 × 브랜드별)"""
    __tablename__ = "coupang_brand_clearances"

    id: Optional[int] = Field(default=None, primary_key=True)
    brand_id: int = Field(foreign_key="brands.id", nullable=False)
    market_account_id: int = Field(foreign_key="market_accounts.id", nullable=False)
    clearance_type: ClearanceTypeEnum
    clearance_status: ClearanceStatusEnum = Field(default=ClearanceStatusEnum.PENDING)
    cleared_at: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True)))
    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )


class MarketListing(SQLModel, table=True):
    """마켓 등록 내역"""
    __tablename__ = "market_listings"

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", nullable=False)
    market_account_id: int = Field(foreign_key="market_accounts.id", nullable=False)
    selling_price: int = Field(sa_column=Column(Integer, nullable=False))   # 판매가 (자동 계산)
    listing_status: ListingStatusEnum = Field(default=ListingStatusEnum.PENDING)
    market_product_id: Optional[str] = Field(sa_column=Column(String(200)))  # 마켓 내 상품 ID
    seo_data: Optional[dict] = Field(default=None, sa_column=Column(JSON))   # 태그, 타이틀, 메타설명
    registered_at: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True)))
    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
```

- [ ] **Step 2: 모델 테스트 작성 및 실행**

Run: `cd backend && python -m pytest tests/domain/market/test_market_model.py -v`
Expected: PASS

- [ ] **Step 3: 커밋**

```bash
git add backend/backend/domain/market/ backend/tests/domain/market/
git commit -m "feat: 마켓/계정/템플릿/소명 데이터 모델 추가"
```

---

## Task 4: 데이터베이스 모델 (모니터링/크롤링 작업/알림)

**Files:**
- Create: `backend/backend/domain/monitoring/model.py`
- Create: `backend/backend/domain/monitoring/__init__.py`
- Test: `backend/tests/domain/monitoring/test_monitoring_model.py`

- [ ] **Step 1: PriceStockHistory, CrawlJob, Notification, CategoryMapping 모델 작성**

```python
# backend/backend/domain/monitoring/model.py
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field, JSON
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, func, Index

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
    change_type: ChangeTypeEnum
    previous_value: Optional[str] = Field(sa_column=Column(String(200)))
    new_value: Optional[str] = Field(sa_column=Column(String(200)))
    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )


class CrawlJob(SQLModel, table=True):
    """크롤링 작업"""
    __tablename__ = "crawl_jobs"

    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="sources.id", nullable=False)
    brand_id: Optional[int] = Field(foreign_key="brands.id")
    source_url: str = Field(sa_column=Column(String(1000), nullable=False))
    target_count: int = Field(default=0)          # 수집 목표 갯수
    collected_count: int = Field(default=0)        # 수집된 갯수
    status: CrawlJobStatusEnum = Field(default=CrawlJobStatusEnum.PENDING)
    error_message: Optional[str] = Field(sa_column=Column(Text))
    started_at: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True)))
    completed_at: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True)))
    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )


class Notification(SQLModel, table=True):
    """알림"""
    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    notification_type: NotificationTypeEnum
    product_id: Optional[int] = Field(foreign_key="products.id")
    message: str = Field(sa_column=Column(Text, nullable=False))
    is_read: bool = Field(default=False, sa_column=Column(Boolean, default=False))
    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )


class CategoryMapping(SQLModel, table=True):
    """카테고리 매핑"""
    __tablename__ = "category_mappings"

    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="sources.id", nullable=False)
    source_category: str = Field(sa_column=Column(String(500), nullable=False))
    market_id: int = Field(foreign_key="markets.id", nullable=False)
    market_category_id: str = Field(sa_column=Column(String(200), nullable=False))
    market_category_name: Optional[str] = Field(sa_column=Column(String(500)))
    confidence: float = Field(default=0.0)        # 매핑 신뢰도
    is_confirmed: bool = Field(default=False)      # 수동 확인 여부
    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
```

- [ ] **Step 2: 테스트 작성 및 실행**
- [ ] **Step 3: 커밋**

```bash
git commit -m "feat: 모니터링/크롤링/알림/카테고리매핑 데이터 모델 추가"
```

---

## Task 5: Repository 레이어 (전체 도메인)

**Files:**
- Create: `backend/backend/domain/source/repository.py`
- Create: `backend/backend/domain/brand/repository.py`
- Create: `backend/backend/domain/product/repository.py`
- Create: `backend/backend/domain/market/repository.py`
- Create: `backend/backend/domain/monitoring/repository.py`

- [ ] **Step 1: 기존 BaseRepository 패턴을 따라 각 도메인 Repository 작성**

```python
# backend/backend/domain/product/repository.py (예시)
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.domain.shared.base_repository import BaseRepository
from backend.domain.product.model import Product, ProductStatusEnum, StockStatusEnum

class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: AsyncSession):
        super().__init__(Product, session)

    async def find_by_source_product_id(self, source_id: int, source_product_id: str) -> Optional[Product]:
        """소싱처 고유 ID로 상품 조회 (중복 체크용)"""
        stmt = select(Product).where(
            Product.source_id == source_id,
            Product.source_product_id == source_product_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_registered_products(self) -> List[Product]:
        """마켓에 등록된 상품만 조회 (모니터링 대상)"""
        stmt = select(Product).where(Product.status == ProductStatusEnum.REGISTERED)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_filters(
        self,
        source_id: Optional[int] = None,
        brand_id: Optional[int] = None,
        status: Optional[ProductStatusEnum] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Product]:
        """필터 기반 상품 목록 조회"""
        stmt = select(Product)
        if source_id:
            stmt = stmt.where(Product.source_id == source_id)
        if brand_id:
            stmt = stmt.where(Product.brand_id == brand_id)
        if status:
            stmt = stmt.where(Product.status == status)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
```

- [ ] **Step 2: 각 Repository 테스트 (단위 테스트)**
- [ ] **Step 3: 커밋**

```bash
git commit -m "feat: 전체 도메인 Repository 레이어 추가"
```

---

## Task 6: 가격 계산 서비스

**Files:**
- Create: `backend/backend/services/price_calculator.py`
- Test: `backend/tests/services/test_price_calculator.py`

- [ ] **Step 1: 가격 계산 테스트 작성**

```python
# backend/tests/services/test_price_calculator.py
from backend.services.price_calculator import PriceCalculator

def test_calculate_selling_price():
    """판매가 = 원가 ÷ (1 - 마켓수수료 - 마진율)"""
    calc = PriceCalculator()
    # 원가 50,000, 수수료 8%, 마진율 20%
    price = calc.calculate(original_price=50000, commission_rate=0.08, margin_rate=0.20)
    assert price == 69445  # 50000 / (1 - 0.08 - 0.20) = 69444.4 → 올림

def test_calculate_coupang_price():
    """쿠팡 수수료 15%"""
    calc = PriceCalculator()
    price = calc.calculate(original_price=50000, commission_rate=0.15, margin_rate=0.20)
    assert price == 76924  # 50000 / (1 - 0.15 - 0.20) = 76923.1 → 올림

def test_price_change_recalculation():
    """원가 변동 시 재계산"""
    calc = PriceCalculator()
    old = calc.calculate(original_price=50000, commission_rate=0.08, margin_rate=0.20)
    new = calc.calculate(original_price=45000, commission_rate=0.08, margin_rate=0.20)
    assert new < old
    assert new == 62500  # 45000 / 0.72

def test_margin_change_recalculation():
    """마진율 변경 시 재계산"""
    calc = PriceCalculator()
    old = calc.calculate(original_price=50000, commission_rate=0.08, margin_rate=0.20)
    new = calc.calculate(original_price=50000, commission_rate=0.08, margin_rate=0.25)
    assert new > old
```

- [ ] **Step 2: 테스트 실행하여 실패 확인**

Run: `cd backend && python -m pytest tests/services/test_price_calculator.py -v`
Expected: FAIL

- [ ] **Step 3: PriceCalculator 구현**

```python
# backend/backend/services/price_calculator.py
import math

class PriceCalculator:
    """마켓 판매가 계산 서비스"""

    def calculate(self, original_price: int, commission_rate: float, margin_rate: float) -> int:
        """
        판매가 = 원가 ÷ (1 - 마켓수수료 - 마진율)
        결과는 올림 처리 (원 단위)
        """
        denominator = 1 - commission_rate - margin_rate
        if denominator <= 0:
            raise ValueError("수수료 + 마진율이 100% 이상입니다")
        return math.ceil(original_price / denominator)

    def calculate_margin_amount(self, original_price: int, selling_price: int, commission_rate: float) -> int:
        """실제 마진 금액 계산"""
        commission = math.ceil(selling_price * commission_rate)
        return selling_price - original_price - commission
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd backend && python -m pytest tests/services/test_price_calculator.py -v`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git commit -m "feat: 마켓 판매가 자동 계산 서비스 (PriceCalculator) 추가"
```

---

## Task 7: SEO 자동 생성 서비스

**Files:**
- Create: `backend/backend/services/seo_generator.py`
- Test: `backend/tests/services/test_seo_generator.py`

- [ ] **Step 1: SEO 생성 테스트 작성**

```python
# backend/tests/services/test_seo_generator.py
from backend.services.seo_generator import SeoGenerator

def test_generate_tags():
    """브랜드 + 카테고리 + 상품명에서 태그 자동 생성"""
    gen = SeoGenerator()
    tags = gen.generate_tags(
        brand="나이키",
        category="운동화",
        product_name="나이키 에어맥스 90 블랙",
        max_tags=10,
    )
    assert "나이키" in tags
    assert "운동화" in tags
    assert "에어맥스" in tags
    assert len(tags) <= 10

def test_generate_title():
    """Page Title 패턴 적용"""
    gen = SeoGenerator()
    title = gen.generate_title(
        pattern="{brand} {product_name}",
        brand="나이키",
        product_name="에어맥스 90 블랙",
    )
    assert title == "나이키 에어맥스 90 블랙"

def test_title_max_length():
    """상품명 길이 제한"""
    gen = SeoGenerator()
    title = gen.generate_title(
        pattern="{brand} {product_name}",
        brand="나이키",
        product_name="에어맥스 90 블랙 화이트 레드 블루 " * 5,
        max_length=100,
    )
    assert len(title) <= 100
```

- [ ] **Step 2: SeoGenerator 구현**

```python
# backend/backend/services/seo_generator.py
import re
from typing import List, Optional

class SeoGenerator:
    """마켓별 SEO 자동 생성 서비스"""

    def generate_tags(
        self,
        brand: str,
        category: str,
        product_name: str,
        max_tags: int = 10,
    ) -> List[str]:
        """태그 자동 생성: 브랜드 + 카테고리 키워드 + 상품명 키워드"""
        tags = set()
        tags.add(brand)
        tags.add(category)
        # 상품명에서 키워드 추출 (2글자 이상, 브랜드/카테고리 제외)
        words = re.split(r'\s+', product_name)
        for word in words:
            if len(word) >= 2 and word not in tags:
                tags.add(word)
        # 조합 태그 (브랜드+카테고리)
        combo = f"{brand}{category}"
        if len(combo) <= 20:
            tags.add(combo)
        return list(tags)[:max_tags]

    def generate_title(
        self,
        pattern: str,
        brand: str,
        product_name: str,
        max_length: int = 100,
    ) -> str:
        """패턴 기반 타이틀 생성"""
        title = pattern.replace("{brand}", brand).replace("{product_name}", product_name)
        if len(title) > max_length:
            title = title[:max_length]
        return title

    def generate_meta_description(
        self,
        pattern: str,
        brand: str,
        product_name: str,
        category: str,
    ) -> str:
        """Meta Description 생성"""
        return pattern.replace("{brand}", brand).replace("{product_name}", product_name).replace("{category}", category)
```

- [ ] **Step 3: 테스트 통과 확인 및 커밋**

```bash
git commit -m "feat: SEO 자동 생성 서비스 (SeoGenerator) 추가"
```

---

## Task 8: 무신사 크롤러 (BaseCrawler + MusinsaCrawler)

**Files:**
- Create: `backend/backend/domain/crawling/base_crawler.py`
- Create: `backend/backend/domain/crawling/musinsa_crawler.py`
- Create: `backend/backend/domain/crawling/__init__.py`
- Test: `backend/tests/crawling/test_base_crawler.py`
- Test: `backend/tests/crawling/test_musinsa_crawler.py`

- [ ] **Step 1: BaseCrawler 추상 클래스 작성**

```python
# backend/backend/domain/crawling/base_crawler.py
import asyncio
import random
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from dataclasses import dataclass

@dataclass
class CrawledProduct:
    """크롤링된 상품 데이터"""
    name: str
    original_price: int
    thumbnail_url: Optional[str]
    image_urls: List[str]
    source_url: str
    source_product_id: str
    brand_name: str
    category: Optional[str]
    options: List[Dict]  # [{"group": "색상", "values": ["블랙", "화이트"]}, ...]
    stock_status: str  # "in_stock" | "out_of_stock"

@dataclass
class BrandInfo:
    """소싱처 브랜드 정보"""
    name: str
    product_count: int

@dataclass
class CategoryInfo:
    """소싱처 카테고리 정보"""
    name: str
    product_count: int

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

class BaseCrawler(ABC):
    """크롤러 공통 인터페이스"""

    def __init__(self):
        self.max_retries = 3
        self.min_delay = 1.0   # 최소 딜레이 (초)
        self.max_delay = 3.0   # 최대 딜레이 (초)

    async def _random_delay(self):
        """랜덤 딜레이 (봇 감지 회피)"""
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)

    def _get_random_user_agent(self) -> str:
        """랜덤 User-Agent"""
        return random.choice(USER_AGENTS)

    async def _request_with_retry(self, fetch_func, *args, **kwargs):
        """자동 재시도 (3회)"""
        for attempt in range(self.max_retries):
            try:
                await self._random_delay()
                return await fetch_func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # 지수 백오프

    @abstractmethod
    async def scan_brands(self, category_url: str) -> List[BrandInfo]:
        """카테고리 페이지에서 브랜드 목록 + 상품 갯수 스캔"""
        ...

    @abstractmethod
    async def scan_categories(self, category_url: str, brand_name: str) -> List[CategoryInfo]:
        """브랜드 선택 후 카테고리 목록 스캔"""
        ...

    @abstractmethod
    async def crawl_products(
        self,
        category_url: str,
        brand_name: str,
        categories: Optional[List[str]] = None,
        max_count: int = 20,
    ) -> List[CrawledProduct]:
        """상품 수집"""
        ...

    @abstractmethod
    async def check_product(self, source_url: str) -> Optional[CrawledProduct]:
        """단일 상품 가격/재고 체크 (모니터링용)"""
        ...
```

- [ ] **Step 2: BaseCrawler 테스트 작성 및 실행**
- [ ] **Step 3: MusinsaCrawler 구현 (무신사 전용)**

```python
# backend/backend/domain/crawling/musinsa_crawler.py
# 무신사 카테고리 페이지 크롤링, 상품 상세 크롤링 구현
# httpx 또는 Playwright 사용 (무신사 CSR 대응)
```

**참고:** 무신사는 CSR(Client-Side Rendering) 기반이므로 내부 API 엔드포인트(`api.musinsa.com`)를 먼저 분석하여 직접 호출 시도. 불가능할 경우 Playwright 사용.

- [ ] **Step 4: MusinsaCrawler 테스트 (목업 데이터)**
- [ ] **Step 5: 커밋**

```bash
git commit -m "feat: BaseCrawler + MusinsaCrawler (무신사 전용 크롤러) 추가"
```

---

## Task 9: 서비스 레이어 (상품/소싱/마켓)

**Files:**
- Create: `backend/backend/domain/source/service.py`
- Create: `backend/backend/domain/brand/service.py`
- Create: `backend/backend/domain/product/service.py`
- Create: `backend/backend/domain/market/service.py`
- Create: `backend/backend/domain/monitoring/service.py`

- [ ] **Step 1: ProductService 작성 (핵심)**

```python
# backend/backend/domain/product/service.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.domain.product.model import Product, ProductStatusEnum, StockStatusEnum
from backend.domain.product.repository import ProductRepository
from backend.domain.monitoring.repository import PriceStockHistoryRepository, NotificationRepository
from backend.domain.monitoring.model import ChangeTypeEnum

class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ProductRepository(session)

    async def create_from_crawled(self, crawled_data: dict, source_id: int, brand_id: int) -> Product:
        """크롤링 데이터에서 상품 생성 (중복 체크 포함)"""
        existing = await self.repo.find_by_source_product_id(
            source_id, crawled_data["source_product_id"]
        )
        if existing:
            return existing  # 이미 수집된 상품

        product = Product(
            source_id=source_id,
            brand_id=brand_id,
            name=crawled_data["name"],
            original_price=crawled_data["original_price"],
            thumbnail_url=crawled_data.get("thumbnail_url"),
            image_urls=crawled_data.get("image_urls"),
            source_url=crawled_data["source_url"],
            source_product_id=crawled_data["source_product_id"],
            source_category=crawled_data.get("category"),
        )
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def update_price_and_stock(self, product_id: int, new_price: int, new_stock_status: StockStatusEnum):
        """가격/재고 변동 업데이트 + 이력 저장 + 알림 생성"""
        product = await self.repo.find_by_id(product_id)
        if not product:
            return

        changes = []
        # 가격 변동 체크
        if product.original_price != new_price:
            changes.append(("price_change", str(product.original_price), str(new_price)))
            product.original_price = new_price

        # 재고 변동 체크
        if product.stock_status != new_stock_status:
            change_type = "out_of_stock" if new_stock_status == StockStatusEnum.OUT_OF_STOCK else "restocked"
            changes.append((change_type, product.stock_status.value, new_stock_status.value))
            product.stock_status = new_stock_status

        if changes:
            # 이력 저장 + 알림 생성은 monitoring service에서 처리
            await self.session.commit()

        return changes
```

- [ ] **Step 2: MarketService 작성 (템플릿/등록)**
- [ ] **Step 3: MonitoringService 작성 (변동 이력/알림)**
- [ ] **Step 4: 각 서비스 테스트**
- [ ] **Step 5: 커밋**

```bash
git commit -m "feat: 도메인 서비스 레이어 전체 추가 (Product/Market/Monitoring)"
```

---

## Task 10: 마켓 동기화 서비스 + 네이버 어댑터

**Files:**
- Create: `backend/backend/adapters/base_adapter.py`
- Create: `backend/backend/adapters/naver_adapter.py`
- Create: `backend/backend/services/market_sync.py`
- Test: `backend/tests/adapters/test_naver_adapter.py`
- Test: `backend/tests/services/test_market_sync.py`

- [ ] **Step 1: BaseMarketAdapter 작성**

```python
# backend/backend/adapters/base_adapter.py
from abc import ABC, abstractmethod
from typing import Optional, Dict

class BaseMarketAdapter(ABC):
    """마켓 API 어댑터 공통 인터페이스"""

    @abstractmethod
    async def register_product(self, product_data: Dict) -> Optional[str]:
        """상품 등록, 마켓 상품 ID 반환"""
        ...

    @abstractmethod
    async def update_price(self, market_product_id: str, new_price: int) -> bool:
        """가격 수정"""
        ...

    @abstractmethod
    async def update_stock(self, market_product_id: str, in_stock: bool) -> bool:
        """재고/품절 처리"""
        ...

    @abstractmethod
    async def deactivate_product(self, market_product_id: str) -> bool:
        """상품 비활성화"""
        ...
```

- [ ] **Step 2: NaverAdapter 구현 (스마트스토어 Commerce API)**
- [ ] **Step 3: MarketSync 서비스 구현 (변동 감지 → 마켓 자동 반영)**

```python
# backend/backend/services/market_sync.py
# 트리거 3가지:
# 1. 원가 변동 → 판매가 재계산 → 마켓 가격 수정
# 2. 재고 변동 → 마켓 품절/재활성화
# 3. 마진율 변경 → 전체 재계산 → 마켓 일괄 수정
```

- [ ] **Step 4: 테스트 (모킹)**
- [ ] **Step 5: 커밋**

```bash
git commit -m "feat: 마켓 동기화 서비스 + 네이버 스마트스토어 어댑터 추가"
```

---

## Task 11: 모니터링 스케줄러

**Files:**
- Create: `backend/backend/services/scheduler.py`
- Test: `backend/tests/services/test_scheduler.py`

- [ ] **Step 1: APScheduler 기반 스마트 주기 모니터링 구현**

```python
# backend/backend/services/scheduler.py
# - 등록된 상품만 모니터링
# - 인기 상품: 10-15분 (±2분 랜덤)
# - 일반 상품: 30분-1시간 (±5분 랜덤)
# - 변동 감지 시 → MarketSync 호출
# - 크롤링 실패 시 → 자동 재시도 3회 → 품절 처리
```

- [ ] **Step 2: main.py에 스케줄러 연동**
- [ ] **Step 3: 테스트**
- [ ] **Step 4: 커밋**

```bash
git commit -m "feat: APScheduler 기반 스마트 주기 모니터링 스케줄러 추가"
```

---

## Task 12: Backend API 엔드포인트

**Files:**
- Create: `backend/backend/api/v1/routers/sources.py`
- Create: `backend/backend/api/v1/routers/brands.py`
- Create: `backend/backend/api/v1/routers/products.py`
- Create: `backend/backend/api/v1/routers/markets.py`
- Create: `backend/backend/api/v1/routers/crawling.py`
- Create: `backend/backend/api/v1/routers/monitoring.py`
- Create: `backend/backend/dtos/source.py`
- Create: `backend/backend/dtos/brand.py`
- Create: `backend/backend/dtos/product.py`
- Create: `backend/backend/dtos/market.py`
- Create: `backend/backend/dtos/crawling.py`
- Create: `backend/backend/dtos/monitoring.py`
- Modify: `backend/backend/main.py` (라우터 등록)

- [ ] **Step 1: DTO 작성 (Request/Response)**
- [ ] **Step 2: 라우터 작성**

주요 엔드포인트:
```
# 소싱처
GET    /api/v1/sources                    # 소싱처 목록
POST   /api/v1/sources                    # 소싱처 추가

# 브랜드
GET    /api/v1/brands                     # 브랜드 목록
POST   /api/v1/brands                     # 브랜드 추가

# 상품
GET    /api/v1/products                   # 상품 목록 (필터/검색/페이징)
GET    /api/v1/products/{id}              # 상품 상세
PATCH  /api/v1/products/{id}              # 상품 수정 (모니터링 등급 등)
DELETE /api/v1/products/{id}              # 상품 삭제
POST   /api/v1/products/bulk-action       # 일괄 작업

# 마켓
GET    /api/v1/markets                    # 마켓 목록
GET    /api/v1/markets/accounts           # 마켓 계정 목록
POST   /api/v1/markets/accounts           # 마켓 계정 추가
GET    /api/v1/markets/templates/common   # 공통 템플릿 조회
PUT    /api/v1/markets/templates/common   # 공통 템플릿 수정
GET    /api/v1/markets/templates/{market_id}  # 마켓별 템플릿 조회
PUT    /api/v1/markets/templates/{market_id}  # 마켓별 템플릿 수정
GET    /api/v1/markets/seo-rules/{market_id}  # SEO 규칙 조회
PUT    /api/v1/markets/seo-rules/{market_id}  # SEO 규칙 수정
GET    /api/v1/markets/coupang/clearances     # 쿠팡 소명 목록
PUT    /api/v1/markets/coupang/clearances/{id}  # 소명 상태 변경

# 크롤링
POST   /api/v1/crawling/scan-brands       # 브랜드 스캔 (체크박스용)
POST   /api/v1/crawling/scan-categories   # 카테고리 스캔 (체크박스용)
POST   /api/v1/crawling/start             # 크롤링 시작
GET    /api/v1/crawling/jobs              # 크롤링 작업 목록
GET    /api/v1/crawling/jobs/{id}         # 작업 상태 조회
GET    /api/v1/crawling/jobs/{id}/progress  # SSE 진행률

# 마켓 등록
POST   /api/v1/products/upload            # 마켓 업로드
GET    /api/v1/products/listings          # 마켓 등록 현황

# 모니터링
GET    /api/v1/monitoring/history          # 변동 이력
GET    /api/v1/monitoring/notifications    # 알림 목록
PATCH  /api/v1/monitoring/notifications/{id}  # 알림 읽음 처리
GET    /api/v1/monitoring/dashboard        # 대시보드 통계
```

- [ ] **Step 3: main.py에 라우터 등록**
- [ ] **Step 4: 커밋**

```bash
git commit -m "feat: Backend API 엔드포인트 전체 추가 (소싱/상품/마켓/크롤링/모니터링)"
```

---

## Task 13: Frontend - 타입 정의 + API 클라이언트

**Files:**
- Create: `frontend/src/types/sourcing.ts`
- Create: `frontend/src/lib/sourcing-api.ts`

- [ ] **Step 1: TypeScript 타입 정의**

```typescript
// frontend/src/types/sourcing.ts
export interface Source {
  id: number;
  name: string;
  base_url: string;
  crawler_type: string;
  is_active: boolean;
}

export interface Brand {
  id: number;
  name: string;
  is_ip_approved: boolean;
}

export interface Product {
  id: number;
  source_id: number;
  brand_id: number;
  name: string;
  original_price: number;
  thumbnail_url: string | null;
  image_urls: string[];
  stock_status: "in_stock" | "out_of_stock";
  monitoring_grade: "high" | "normal";
  status: "collected" | "registered" | "inactive";
  last_crawled_at: string | null;
}

// ... 전체 타입 정의
```

- [ ] **Step 2: API 클라이언트 작성**

```typescript
// frontend/src/lib/sourcing-api.ts
// 기존 api.ts 패턴을 따라 소싱 전용 API 함수 작성
```

- [ ] **Step 3: 커밋**

```bash
git commit -m "feat: Frontend 타입 정의 + 소싱 API 클라이언트 추가"
```

---

## Task 14: Frontend - 레이아웃 + 대시보드 홈

**Files:**
- Create: `frontend/src/app/sourcing/layout.tsx`
- Create: `frontend/src/app/sourcing/page.tsx`
- Create: `frontend/src/components/sourcing/layout/Sidebar.tsx`
- Create: `frontend/src/components/sourcing/dashboard/StatsCards.tsx`
- Create: `frontend/src/components/sourcing/dashboard/RecentAlerts.tsx`

- [ ] **Step 1: 사이드바 레이아웃 구현**
- [ ] **Step 2: 대시보드 홈 (통계 카드 + 최근 알림)**
- [ ] **Step 3: 커밋**

```bash
git commit -m "feat: 소싱 대시보드 레이아웃 + 홈 화면 추가"
```

---

## Task 15: Frontend - 새 소싱 작업 화면

**Files:**
- Create: `frontend/src/app/sourcing/crawl/page.tsx`
- Create: `frontend/src/components/sourcing/crawl/SourceSelector.tsx`
- Create: `frontend/src/components/sourcing/crawl/BrandSelector.tsx`
- Create: `frontend/src/components/sourcing/crawl/CategorySelector.tsx`
- Create: `frontend/src/components/sourcing/crawl/CrawlProgress.tsx`

- [ ] **Step 1: 4단계 소싱 위자드 구현**

```
1단계: 소싱처 선택 + URL 입력
2단계: 브랜드 체크박스 (수집 가능 갯수 표시)
3단계: 카테고리 체크박스 (수집 가능 갯수 표시)
4단계: 수집 갯수 설정 → 수집 시작 → 진행률 표시 (SSE)
```

- [ ] **Step 2: 커밋**

```bash
git commit -m "feat: 새 소싱 작업 4단계 위자드 화면 추가"
```

---

## Task 16: Frontend - 상품 목록 + 마켓 업로드 모달

**Files:**
- Create: `frontend/src/app/sourcing/products/page.tsx`
- Create: `frontend/src/components/sourcing/products/ProductTable.tsx`
- Create: `frontend/src/components/sourcing/products/ProductFilters.tsx`
- Create: `frontend/src/components/sourcing/products/UploadModal.tsx`

- [ ] **Step 1: 상품 테이블 (필터/검색/페이징/일괄작업)**
- [ ] **Step 2: 마켓 업로드 모달 (사업자 → 마켓 → 계정 선택, 쿠팡 소명 차단)**
- [ ] **Step 3: 커밋**

```bash
git commit -m "feat: 상품 목록 + 마켓 업로드 모달 화면 추가"
```

---

## Task 17: Frontend - 마켓 템플릿 설정

**Files:**
- Create: `frontend/src/app/sourcing/markets/templates/page.tsx`
- Create: `frontend/src/components/sourcing/markets/TemplateForm.tsx`

- [ ] **Step 1: 3단계 템플릿 UI (공통 기본값 탭 + 마켓별 탭)**
- [ ] **Step 2: 커밋**

```bash
git commit -m "feat: 마켓 템플릿 설정 화면 (공통+마켓별) 추가"
```

---

## Task 18: Frontend - 나머지 화면 (브랜드/소싱처/모니터링/알림/쿠팡소명)

**Files:**
- Create: `frontend/src/app/sourcing/brands/page.tsx`
- Create: `frontend/src/app/sourcing/sources/page.tsx`
- Create: `frontend/src/app/sourcing/monitoring/page.tsx`
- Create: `frontend/src/app/sourcing/notifications/page.tsx`
- Create: `frontend/src/app/sourcing/markets/coupang/page.tsx`

- [ ] **Step 1: 브랜드 관리 화면**
- [ ] **Step 2: 소싱처 관리 화면**
- [ ] **Step 3: 크롤링 현황 + 알림 센터**
- [ ] **Step 4: 쿠팡 소명 관리 매트릭스**
- [ ] **Step 5: 커밋**

```bash
git commit -m "feat: 브랜드/소싱처/모니터링/알림/쿠팡소명 화면 추가"
```

---

## Task 19: 통합 테스트 + E2E 검증

**Files:**
- Create: `backend/tests/integration/test_full_flow.py`

- [ ] **Step 1: 전체 플로우 통합 테스트**

```
1. 소싱처(무신사) 등록
2. 브랜드(나이키) 등록
3. 무신사 크롤링 (10개 상품 수집)
4. 마켓 템플릿 설정 (스마트스토어, 수수료 8%, 마진율 20%)
5. 상품 선택 → 스마트스토어 등록
6. 가격/재고 모니터링 1회 실행
7. 가격 변동 시뮬레이션 → 마켓 자동 반영 확인
```

- [ ] **Step 2: 커밋**

```bash
git commit -m "test: 전체 플로우 통합 테스트 추가"
```

---

## Task 20: DB 마이그레이션 + 시드 데이터

**Files:**
- Create: DB 마이그레이션 스크립트
- Create: `backend/scripts/seed_data.py`

- [ ] **Step 1: Alembic 마이그레이션 생성**
- [ ] **Step 2: 시드 데이터 (무신사 소싱처, 마켓 6개, 사업자 그룹 5개)**
- [ ] **Step 3: 커밋**

```bash
git commit -m "feat: DB 마이그레이션 + 시드 데이터 추가"
```

---

## 실행 순서 요약

```
Task 1-4:  데이터 모델 (DB 테이블 정의)
Task 5:    Repository 레이어
Task 6-7:  가격 계산 + SEO 서비스
Task 8:    무신사 크롤러
Task 9:    서비스 레이어
Task 10:   마켓 동기화 + 네이버 어댑터
Task 11:   모니터링 스케줄러
Task 12:   Backend API 엔드포인트
Task 13:   Frontend 타입 + API 클라이언트
Task 14-18: Frontend UI 화면
Task 19:   통합 테스트
Task 20:   DB 마이그레이션 + 시드 데이터
```
