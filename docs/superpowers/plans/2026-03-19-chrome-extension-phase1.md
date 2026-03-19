# 크롬 익스텐션 기반 소싱 시스템 Phase 1 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 무신사 상품 개별 수집 → 스마트스토어 등록 → 가격/재고 모니터링 파이프라인을 크롬 익스텐션 + FastAPI + Next.js 대시보드로 구현한다.

**Architecture:** 크롬 익스텐션(Manifest V3)이 무신사 페이지에서 fetch/XHR 오버라이드로 상품 데이터를 수집하고, REST API 폴링으로 백엔드와 통신한다. 백엔드는 가격 계산/마켓 연동/명령 큐를 관리하며, Next.js 대시보드에서 모든 설정과 관리를 수행한다.

**Tech Stack:** Vite 5 + CRXJS (익스텐션), FastAPI + SQLModel + PostgreSQL (백엔드), Next.js 15 + shadcn/ui + Tailwind CSS 4 (프론트엔드)

**Spec:** `docs/superpowers/specs/2026-03-19-chrome-extension-sourcing-design.md`

---

## 파일 구조 (Phase 1에서 생성/수정하는 전체 파일)

### 백엔드 — 삭제

```
backend/backend/domain/crawling/base_crawler.py        # 삭제
backend/backend/domain/crawling/musinsa_crawler.py     # 삭제
backend/backend/services/scheduler.py                   # 삭제
backend/tests/domain/crawling/test_base_crawler.py     # 삭제
backend/tests/domain/crawling/test_musinsa_crawler.py  # 삭제
backend/tests/services/test_scheduler.py               # 삭제
```

### 백엔드 — 신규

```
backend/backend/domain/collection/__init__.py
backend/backend/domain/collection/model.py              # CollectionSetting, CollectionLog, ExtensionCommand
backend/backend/domain/collection/repository.py         # 3개 레포지토리
backend/backend/domain/collection/service.py            # CollectionService, ExtensionCommandService
backend/backend/dtos/extension.py                       # 익스텐션 수신 DTO
backend/backend/dtos/collection.py                      # 수집 설정 DTO
backend/backend/api/v1/routers/extension.py             # 익스텐션 통신 라우터
backend/backend/api/v1/routers/collection_settings.py   # 수집 설정 CRUD 라우터
backend/backend/api/v1/routers/collection_logs.py       # 수집 로그 + SSE 라우터
backend/backend/api/v1/routers/products.py              # 상품 관리 라우터
backend/alembic/versions/xxxx_add_collection_tables.py  # DB 마이그레이션
backend/tests/domain/collection/test_collection_model.py
backend/tests/domain/collection/test_collection_service.py
backend/tests/api/test_extension_router.py
backend/tests/api/test_collection_settings_router.py
```

### 백엔드 — 수정

```
backend/backend/main.py                                 # 라우터 등록 추가
backend/backend/domain/monitoring/model.py              # CrawlJob 클래스 deprecated 주석
backend/backend/domain/product/service.py               # create_from_extension() 추가
```

### 크롬 익스텐션 — 전부 신규

```
extension/package.json
extension/vite.config.ts
extension/tsconfig.json
extension/tailwind.config.ts
extension/postcss.config.js
extension/manifest.json
extension/src/shared/types.ts
extension/src/shared/constants.ts
extension/src/background/index.ts
extension/src/background/api-client.ts
extension/src/background/command-poller.ts
extension/src/background/monitoring-manager.ts
extension/src/content/musinsa-interceptor.ts
extension/src/content/musinsa-product.tsx
extension/src/content/musinsa-product.css
extension/src/popup/index.html
extension/src/popup/index.tsx
extension/src/popup/Popup.tsx
extension/src/popup/popup.css
```

### 프론트엔드 — 신규

```
frontend/src/types/sourcing.ts
frontend/src/lib/sourcing-api.ts
frontend/src/app/sourcing/layout.tsx
frontend/src/app/sourcing/page.tsx
frontend/src/app/sourcing/collection-settings/page.tsx
frontend/src/app/sourcing/collection-settings/new/page.tsx
frontend/src/app/sourcing/products/page.tsx
frontend/src/app/sourcing/products/[id]/page.tsx
frontend/src/app/sourcing/monitoring/page.tsx
frontend/src/app/sourcing/market-listings/page.tsx
frontend/src/app/sourcing/logs/page.tsx
frontend/src/components/sourcing/CollectionSettingsTable.tsx
frontend/src/components/sourcing/ProductsTable.tsx
frontend/src/components/sourcing/MonitoringStatus.tsx
frontend/src/components/sourcing/LogsViewer.tsx
frontend/src/components/sourcing/ExtensionStatus.tsx
```

---

## Task 분해

### Task 1: 백엔드 — 삭제된 코드 정리 + 수집 도메인 모델

**Files:**
- Delete: `backend/backend/domain/crawling/base_crawler.py`
- Delete: `backend/backend/domain/crawling/musinsa_crawler.py`
- Delete: `backend/backend/services/scheduler.py`
- Delete: `backend/tests/domain/crawling/test_base_crawler.py`
- Delete: `backend/tests/domain/crawling/test_musinsa_crawler.py`
- Delete: `backend/tests/services/test_scheduler.py`
- Modify: `backend/backend/domain/monitoring/model.py` (CrawlJob deprecated 주석)
- Create: `backend/backend/domain/collection/__init__.py`
- Create: `backend/backend/domain/collection/model.py`
- Test: `backend/tests/domain/collection/test_collection_model.py`

- [ ] **Step 1: 크롤링/스케줄러 코드 삭제**

삭제할 파일:
```
backend/backend/domain/crawling/base_crawler.py
backend/backend/domain/crawling/musinsa_crawler.py
backend/backend/services/scheduler.py
backend/tests/domain/crawling/test_base_crawler.py
backend/tests/domain/crawling/test_musinsa_crawler.py
backend/tests/services/test_scheduler.py
```

`monitoring/model.py`의 `CrawlJob` 클래스 위에 deprecated 주석 추가:
```python
# DEPRECATED: ExtensionCommand로 대체됨 (2026-03-19)
# Phase 1 마이그레이션 완료 후 삭제 예정
class CrawlJob(SQLModel, table=True):
    ...
```

- [ ] **Step 2: 수집 도메인 모델 테스트 작성**

```python
# backend/tests/domain/collection/test_collection_model.py
"""수집 도메인 모델 단위 테스트."""
from backend.domain.collection.model import (
    CollectionSetting,
    CollectionLog,
    ExtensionCommand,
    CommandStatusEnum,
    CommandTypeEnum,
    LogStatusEnum,
)


def test_collection_setting_creation():
    """CollectionSetting 인스턴스 생성 및 기본값"""
    setting = CollectionSetting(
        name="나이키_신발",
        source_id=1,
        brand_name="나이키",
        category_url="https://www.musinsa.com/categories/shoes",
    )
    assert setting.name == "나이키_신발"
    assert setting.max_count == 500
    assert setting.is_active is True
    assert setting.collected_count == 0


def test_collection_log_creation():
    """CollectionLog 인스턴스 생성"""
    log = CollectionLog(
        product_name="나이키 에어맥스 90",
        status=LogStatusEnum.SUCCESS,
    )
    assert log.status == "success"
    assert log.setting_id is None  # 개별 수집 시 null


def test_extension_command_creation():
    """ExtensionCommand 인스턴스 생성 및 기본값"""
    cmd = ExtensionCommand(
        command_type=CommandTypeEnum.MONITOR_REGISTER,
        payload='{"product_id": 42, "source_url": "https://..."}',
    )
    assert cmd.status == "pending"
    assert cmd.processed_at is None


def test_command_type_enum_values():
    """CommandTypeEnum 값 확인"""
    assert CommandTypeEnum.MONITOR_REGISTER == "monitor_register"
    assert CommandTypeEnum.MONITOR_UNREGISTER == "monitor_unregister"


def test_command_status_enum_values():
    """CommandStatusEnum 값 확인"""
    assert CommandStatusEnum.PENDING == "pending"
    assert CommandStatusEnum.PROCESSING == "processing"
    assert CommandStatusEnum.DONE == "done"
    assert CommandStatusEnum.FAILED == "failed"
```

- [ ] **Step 3: 테스트 실행 — FAIL 확인**

```bash
cd backend
source .venv/Scripts/activate && python -m pytest tests/domain/collection/test_collection_model.py -v
```
Expected: FAIL (모듈 없음)

- [ ] **Step 4: 수집 도메인 모델 구현**

```python
# backend/backend/domain/collection/__init__.py
# (빈 파일)

# backend/backend/domain/collection/model.py
"""수집 도메인 SQLModel 모델.

Table Structure:
- CollectionSetting: 수집 설정 (브랜드×카테고리 매핑)
- CollectionLog: 수집 로그
- ExtensionCommand: 익스텐션 명령 큐
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, Index, func


class CommandTypeEnum(str, Enum):
    """익스텐션 명령 타입"""
    MONITOR_REGISTER = "monitor_register"
    MONITOR_UNREGISTER = "monitor_unregister"


class CommandStatusEnum(str, Enum):
    """명령 처리 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class LogStatusEnum(str, Enum):
    """수집 로그 상태"""
    SUCCESS = "success"
    FAILED = "failed"


class CollectionSetting(SQLModel, table=True):
    """수집 설정 — 브랜드×카테고리 매핑"""
    __tablename__ = "collection_settings"
    __table_args__ = (
        Index("ix_collection_settings_source_id", "source_id"),
        Index("ix_collection_settings_is_active", "is_active"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String(200), nullable=False))
    source_id: int = Field(foreign_key="sources.id", nullable=False)
    brand_name: str = Field(sa_column=Column(String(200), nullable=False))
    category_url: str = Field(sa_column=Column(Text, nullable=False))
    max_count: int = Field(
        default=500,
        sa_column=Column(Integer, nullable=False, server_default="500"),
    )
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default="true"),
    )
    last_collected_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    collected_count: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default="0"),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=func.now()),
    )


class CollectionLog(SQLModel, table=True):
    """수집 로그"""
    __tablename__ = "collection_logs"
    __table_args__ = (
        Index("ix_collection_logs_created_at", "created_at"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    setting_id: Optional[int] = Field(
        default=None, foreign_key="collection_settings.id", nullable=True,
    )
    product_name: str = Field(sa_column=Column(String(500), nullable=False))
    status: str = Field(sa_column=Column(String(20), nullable=False))
    message: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ExtensionCommand(SQLModel, table=True):
    """익스텐션 명령 큐"""
    __tablename__ = "extension_commands"
    __table_args__ = (
        Index("ix_extension_commands_status", "status"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    command_type: str = Field(sa_column=Column(String(50), nullable=False))
    payload: str = Field(sa_column=Column(Text, nullable=False))
    status: str = Field(
        default=CommandStatusEnum.PENDING,
        sa_column=Column(String(20), nullable=False, server_default="pending"),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    processed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
```

- [ ] **Step 5: 테스트 실행 — PASS 확인**

```bash
cd backend
source .venv/Scripts/activate && python -m pytest tests/domain/collection/test_collection_model.py -v
```
Expected: 5 passed

- [ ] **Step 6: 커밋**

```bash
git add -A
git commit -m "feat: 수집 도메인 모델 추가 + 크롤러/스케줄러 코드 삭제

- CollectionSetting, CollectionLog, ExtensionCommand 모델
- 기존 crawling 도메인 + scheduler 삭제 (익스텐션으로 대체)
- CrawlJob deprecated 처리"
```

---

### Task 2: 백엔드 — 수집 도메인 Repository + Service + ProductService 확장

**Files:**
- Create: `backend/backend/domain/collection/repository.py`
- Create: `backend/backend/domain/collection/service.py`
- Create: `backend/backend/dtos/extension.py`
- Create: `backend/backend/dtos/collection.py`
- Modify: `backend/backend/domain/product/service.py` (create_from_extension 추가)
- Test: `backend/tests/domain/collection/test_collection_service.py`

**참고 패턴:**
- BaseRepository: `backend/backend/domain/shared/base_repository.py` — `__init__(session, Model)` (session 먼저, Model 두번째)
- BaseRepository API: `create_async(**kwargs)`, `update_async(id, **kwargs)`, `delete_async(id)`, `list_async(skip=, limit=)`, `find_by_async(**kwargs)`, `filter_by_async(**kwargs)`
- ProductService: `backend/backend/domain/product/service.py` — `__init__(session)` 패턴
- 기존 DTO: `backend/backend/dtos/` — Pydantic BaseModel 기반

- [ ] **Step 1: DTO 정의**

```python
# backend/backend/dtos/extension.py
"""익스텐션 통신 DTO."""
from typing import List, Optional
from pydantic import BaseModel, Field


class ProductOptionData(BaseModel):
    """상품 옵션 (색상×사이즈)"""
    color: Optional[str] = None
    size: Optional[str] = None
    stock: int = 0


class ExtensionProductData(BaseModel):
    """익스텐션에서 전송하는 수집 상품 데이터"""
    name: str
    original_price: int
    source_url: str
    source_product_id: str
    brand_name: str
    stock_status: str = "in_stock"
    grade_discount_available: bool = True
    point_usable: bool = True
    point_earnable: bool = True
    thumbnail_url: Optional[str] = None
    image_urls: List[str] = Field(default_factory=list)
    options: List[ProductOptionData] = Field(default_factory=list)


class ExtensionProductRequest(BaseModel):
    """POST /api/v1/extension/products 요청"""
    source: str = "musinsa"
    product: ExtensionProductData


class ProductChangeRequest(BaseModel):
    """POST /api/v1/extension/products/{id}/changes 요청"""
    change_type: str  # "price" | "stock" | "both"
    old_price: Optional[int] = None
    new_price: Optional[int] = None
    stock_status: Optional[str] = None


class CommandAckRequest(BaseModel):
    """명령 처리 완료 보고"""
    status: str = "done"  # "done" | "failed"
    message: Optional[str] = None


class HeartbeatRequest(BaseModel):
    """익스텐션 생존 신호"""
    monitoring_count: int = 0
    extension_version: str = "1.0.0"
```

```python
# backend/backend/dtos/collection.py
"""수집 설정 DTO."""
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
    last_collected_at: Optional[str] = None
    collected_count: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
```

- [ ] **Step 2: Repository 구현**

```python
# backend/backend/domain/collection/repository.py
"""수집 도메인 Repository."""
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.shared.base_repository import BaseRepository
from backend.domain.collection.model import (
    CollectionSetting,
    CollectionLog,
    ExtensionCommand,
    CommandStatusEnum,
)


class CollectionSettingRepository(BaseRepository[CollectionSetting]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, CollectionSetting)

    async def find_active_settings(self) -> List[CollectionSetting]:
        """활성 수집 설정 목록"""
        return await self.filter_by_async(is_active=True)


class CollectionLogRepository(BaseRepository[CollectionLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, CollectionLog)


class ExtensionCommandRepository(BaseRepository[ExtensionCommand]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ExtensionCommand)

    async def find_pending_commands(self) -> List[ExtensionCommand]:
        """대기 중인 명령 조회 (익스텐션 폴링용)"""
        return await self.filter_by_async(status=CommandStatusEnum.PENDING)
```

- [ ] **Step 3: ProductService에 create_from_extension 추가**

`backend/backend/domain/product/service.py`에 다음 메서드를 `ProductService` 클래스에 추가:

```python
# backend/backend/domain/product/service.py — ProductService 클래스에 추가
# import 추가: from backend.domain.brand.repository import BrandRepository
# import 추가: from backend.services.price_calculator import PriceCalculator
# import 추가: from backend.services.seo_generator import SeoGenerator
# import 추가: from backend.dtos.extension import ExtensionProductData

async def create_from_extension(
    self,
    source: str,
    data: ExtensionProductData,
    source_id: int,
) -> Product:
    """
    익스텐션 수집 데이터에서 상품 생성 (중복 체크 + 브랜드 조회 포함).

    Args:
        source: 소싱처 식별자 (예: "musinsa")
        data: 익스텐션에서 전송한 상품 데이터
        source_id: 소싱처 ID

    Returns:
        생성되거나 기존에 존재하는 Product 객체
    """
    # 중복 체크
    existing = await self.repo.find_by_source_product_id(
        source_id=source_id,
        source_product_id=data.source_product_id,
    )
    if existing is not None:
        return existing

    # 브랜드 조회 (brand_name → brand_id)
    brand_repo = BrandRepository(self.session)
    brand = await brand_repo.find_by_name(data.brand_name)
    brand_id = brand.id if brand else 0  # 미등록 브랜드는 0 (나중에 매핑)

    # 상품 생성
    product = Product(
        source_id=source_id,
        brand_id=brand_id,
        name=data.name,
        original_price=data.original_price,
        source_url=data.source_url,
        source_product_id=data.source_product_id,
        thumbnail_url=data.thumbnail_url,
        image_urls=data.image_urls if data.image_urls else None,
        grade_discount_available=data.grade_discount_available,
        point_usable=data.point_usable,
        last_crawled_at=datetime.now(tz=timezone.utc),
    )
    self.session.add(product)
    await self.session.commit()
    await self.session.refresh(product)
    return product
```

**주의:** Product 모델에 `grade_discount_available`, `point_usable` 필드가 없으면 추가 필요 — 이미 Product 모델에 있는지 확인 후 없으면 Task 1에서 마이그레이션에 포함.

- [ ] **Step 4: Service 테스트 작성**

```python
# backend/tests/domain/collection/test_collection_service.py
"""수집 서비스 단위 테스트."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.domain.collection.service import (
    CollectionService,
    ExtensionCommandService,
)
from backend.domain.collection.model import CommandTypeEnum, CommandStatusEnum
from backend.dtos.extension import ExtensionProductData


def test_extension_command_service_init():
    """ExtensionCommandService 초기화"""
    session = AsyncMock()
    service = ExtensionCommandService(session)
    assert service.session is session


@pytest.mark.asyncio
async def test_create_monitor_register_command():
    """모니터링 등록 명령 생성"""
    session = AsyncMock()
    service = ExtensionCommandService(session)

    with patch.object(service, "repo") as mock_repo:
        mock_repo.create_async = AsyncMock()
        await service.create_monitor_command(
            product_id=42,
            source_url="https://www.musinsa.com/app/goods/12345",
            grade="high",
        )
        mock_repo.create_async.assert_called_once()
        call_kwargs = mock_repo.create_async.call_args[1]
        assert call_kwargs["command_type"] == CommandTypeEnum.MONITOR_REGISTER
        payload = json.loads(call_kwargs["payload"])
        assert payload["product_id"] == 42


@pytest.mark.asyncio
async def test_ack_command_done():
    """명령 처리 완료"""
    session = AsyncMock()
    service = ExtensionCommandService(session)

    mock_cmd = MagicMock()
    mock_cmd.id = 1
    mock_cmd.status = CommandStatusEnum.PENDING

    with patch.object(service, "repo") as mock_repo:
        mock_repo.get_async = AsyncMock(return_value=mock_cmd)
        mock_repo.update_async = AsyncMock(return_value=mock_cmd)
        result = await service.ack_command(command_id=1, status="done")
        # update_async(id, **kwargs) 패턴 검증
        mock_repo.update_async.assert_called_once()
        call_args = mock_repo.update_async.call_args
        assert call_args[0][0] == 1  # id


@pytest.mark.asyncio
async def test_collection_service_process_product():
    """수집 상품 처리 (DB 저장 + 로그 기록 + 브랜드 IP 경고)"""
    session = AsyncMock()
    service = CollectionService(session)

    product_data = ExtensionProductData(
        name="나이키 에어맥스 90",
        original_price=169000,
        source_url="https://www.musinsa.com/app/goods/12345",
        source_product_id="12345",
        brand_name="나이키",
        stock_status="in_stock",
    )

    with (
        patch.object(service, "product_service") as mock_product_svc,
        patch.object(service, "log_repo") as mock_log_repo,
        patch.object(service, "brand_repo") as mock_brand_repo,
    ):
        mock_product_svc.create_from_extension = AsyncMock(return_value=MagicMock(id=1))
        mock_log_repo.create_async = AsyncMock()
        # 브랜드 지재권 미승인 시뮬레이션
        mock_brand = MagicMock()
        mock_brand.is_ip_approved = False
        mock_brand_repo.find_by_name = AsyncMock(return_value=mock_brand)

        result = await service.process_collected_product(
            source="musinsa",
            product_data=product_data,
            source_id=1,
        )
        # 수집은 허용되되 경고 포함
        mock_product_svc.create_from_extension.assert_called_once()
        mock_log_repo.create_async.assert_called_once()
```

- [ ] **Step 5: 테스트 실행 — FAIL 확인**

```bash
cd backend
source .venv/Scripts/activate && python -m pytest tests/domain/collection/test_collection_service.py -v
```

- [ ] **Step 6: Service 구현**

```python
# backend/backend/domain/collection/service.py
"""수집 도메인 서비스."""
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.collection.model import (
    CollectionSetting,
    CollectionLog,
    ExtensionCommand,
    CommandTypeEnum,
    CommandStatusEnum,
    LogStatusEnum,
)
from backend.domain.collection.repository import (
    CollectionSettingRepository,
    CollectionLogRepository,
    ExtensionCommandRepository,
)
from backend.domain.product.service import ProductService
from backend.domain.brand.repository import BrandRepository
from backend.services.price_calculator import PriceCalculator
from backend.services.seo_generator import SeoGenerator
from backend.dtos.extension import ExtensionProductData
from backend.dtos.collection import (
    CollectionSettingCreateRequest,
    CollectionSettingUpdateRequest,
)
from backend.utils.logger import logger


class ExtensionCommandService:
    """익스텐션 명령 큐 관리"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ExtensionCommandRepository(session)

    async def get_pending_commands(self) -> List[ExtensionCommand]:
        """대기 중인 명령 조회 (익스텐션 폴링)"""
        return await self.repo.find_pending_commands()

    async def create_monitor_command(
        self,
        product_id: int,
        source_url: str,
        grade: str = "normal",
    ) -> ExtensionCommand:
        """모니터링 등록 명령 생성"""
        payload = json.dumps({
            "product_id": product_id,
            "source_url": source_url,
            "grade": grade,
        })
        return await self.repo.create_async(
            command_type=CommandTypeEnum.MONITOR_REGISTER,
            payload=payload,
        )

    async def create_unmonitor_command(self, product_id: int) -> ExtensionCommand:
        """모니터링 해제 명령 생성"""
        payload = json.dumps({"product_id": product_id})
        return await self.repo.create_async(
            command_type=CommandTypeEnum.MONITOR_UNREGISTER,
            payload=payload,
        )

    async def ack_command(
        self,
        command_id: int,
        status: str = "done",
        message: Optional[str] = None,
    ) -> Optional[ExtensionCommand]:
        """명령 처리 완료/실패 보고"""
        cmd = await self.repo.get_async(command_id)
        if not cmd:
            return None
        new_status = (
            CommandStatusEnum.DONE if status == "done"
            else CommandStatusEnum.FAILED
        )
        return await self.repo.update_async(
            command_id,
            status=new_status,
            processed_at=datetime.now(tz=timezone.utc),
        )


class CollectionService:
    """수집 비즈니스 로직"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.setting_repo = CollectionSettingRepository(session)
        self.log_repo = CollectionLogRepository(session)
        self.product_service = ProductService(session)
        self.brand_repo = BrandRepository(session)
        self.price_calculator = PriceCalculator()
        self.seo_generator = SeoGenerator()

    # --- 수집 설정 CRUD ---

    async def create_setting(
        self, data: CollectionSettingCreateRequest,
    ) -> CollectionSetting:
        """수집 설정 생성"""
        return await self.setting_repo.create_async(
            name=data.name,
            source_id=data.source_id,
            brand_name=data.brand_name,
            category_url=data.category_url,
            max_count=data.max_count,
        )

    async def list_settings(self) -> List[CollectionSetting]:
        """수집 설정 목록"""
        return await self.setting_repo.list_async()

    async def get_setting(self, setting_id: int) -> Optional[CollectionSetting]:
        """수집 설정 조회"""
        return await self.setting_repo.get_async(setting_id)

    async def update_setting(
        self, setting_id: int, data: CollectionSettingUpdateRequest,
    ) -> Optional[CollectionSetting]:
        """수집 설정 수정"""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.setting_repo.get_async(setting_id)
        return await self.setting_repo.update_async(setting_id, **update_data)

    async def delete_setting(self, setting_id: int) -> bool:
        """수집 설정 삭제"""
        return await self.setting_repo.delete_async(setting_id)

    # --- 수집 상품 처리 ---

    async def process_collected_product(
        self,
        source: str,
        product_data: ExtensionProductData,
        source_id: int,
        setting_id: Optional[int] = None,
    ) -> Dict:
        """
        수집된 상품 데이터 처리 (DB 저장 + 브랜드 IP 체크 + 가격 계산 + 로그).

        Returns:
            {"product": Product, "ip_warning": str | None}
        """
        # 1. 브랜드 지재권 확인 (경고만, 수집은 허용)
        ip_warning = None
        brand = await self.brand_repo.find_by_name(product_data.brand_name)
        if brand and not brand.is_ip_approved:
            ip_warning = f"브랜드 '{product_data.brand_name}'의 지재권이 미승인 상태입니다"
            logger.warning(ip_warning)

        # 2. 상품 저장
        product = await self.product_service.create_from_extension(
            source=source,
            data=product_data,
            source_id=source_id,
        )

        # 3. PriceCalculator로 판매가 계산 (Phase 1: 기본 계산만)
        # TODO: SourceAccount에서 등급별 할인율 조회
        # 현재는 기본 계산 (등급 할인 없이)
        try:
            selling_price = self.price_calculator.calculate(
                original_price=product_data.original_price,
                commission_rate=0.05,  # TODO: MarketTemplate에서 조회
                margin_rate=0.20,  # TODO: MarketTemplate에서 조회
            )
            logger.info(f"판매가 계산: {product_data.original_price}원 → {selling_price}원")
        except ValueError as e:
            logger.warning(f"판매가 계산 실패: {e}")

        # 4. SeoGenerator로 태그 생성 (Phase 1: 기본 태그만)
        tags = self.seo_generator.generate_tags(
            brand=product_data.brand_name,
            category="",  # Phase 2에서 카테고리 매핑 추가
            product_name=product_data.name,
        )
        logger.info(f"SEO 태그 생성: {tags[:5]}...")

        # 5. 수집 로그 기록
        log_message = ip_warning if ip_warning else None
        await self.log_repo.create_async(
            setting_id=setting_id,
            product_name=product_data.name,
            status=LogStatusEnum.SUCCESS,
            message=log_message,
        )

        return {"product": product, "ip_warning": ip_warning}

    # --- 수집 로그 ---

    async def list_logs(
        self, limit: int = 50, skip: int = 0,
    ) -> List[CollectionLog]:
        """수집 로그 목록"""
        return await self.log_repo.list_async(skip=skip, limit=limit)
```

- [ ] **Step 7: 테스트 실행 — PASS 확인**

```bash
cd backend
source .venv/Scripts/activate && python -m pytest tests/domain/collection/ -v
```

- [ ] **Step 8: 커밋**

```bash
git add -A
git commit -m "feat: 수집 도메인 Repository/Service + 익스텐션 DTO 추가

- CollectionSettingRepository, CollectionLogRepository, ExtensionCommandRepository
- CollectionService (수집 설정 CRUD + 상품 처리 + 브랜드 IP 체크 + PriceCalculator)
- ExtensionCommandService (명령 큐 관리)
- ProductService.create_from_extension() 추가
- ExtensionProductData, CollectionSettingCreateRequest 등 DTO
- BaseRepository API 준수: create_async(**kwargs), update_async(id, **kwargs), delete_async(id)"
```

---

### Task 3: 백엔드 — 익스텐션 통신 API 라우터

**Files:**
- Create: `backend/backend/api/v1/routers/extension.py`
- Modify: `backend/backend/main.py`
- Test: `backend/tests/api/test_extension_router.py`

**참고:** 기존 라우터 패턴은 `backend/backend/api/v1/routers/auth.py` 참조.
세션 주입은 `Depends(get_write_session_dependency)` 사용.

- [ ] **Step 1: 익스텐션 라우터 테스트 작성**

```python
# backend/tests/api/test_extension_router.py
"""익스텐션 통신 API 라우터 테스트."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


def test_extension_router_imports():
    """라우터 import 확인"""
    from backend.api.v1.routers.extension import router
    assert router is not None


def test_verify_extension_key_valid():
    """유효한 API 키 검증"""
    from backend.api.v1.routers.extension import verify_extension_key, EXTENSION_API_KEY
    result = verify_extension_key(EXTENSION_API_KEY)
    assert result == EXTENSION_API_KEY


def test_verify_extension_key_invalid():
    """잘못된 API 키 검증"""
    from fastapi import HTTPException
    from backend.api.v1.routers.extension import verify_extension_key
    with pytest.raises(HTTPException) as exc_info:
        verify_extension_key("wrong-key")
    assert exc_info.value.status_code == 401
```

- [ ] **Step 2: 익스텐션 라우터 구현**

```python
# backend/backend/api/v1/routers/extension.py
"""익스텐션 통신 API 라우터.

익스텐션이 폴링하는 명령 큐, 수집 데이터 수신, heartbeat 처리.
인증: X-Extension-Key 헤더 (Phase 1은 간단한 API 키)
"""
from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.db.orm import get_write_session_dependency
from backend.domain.collection.service import (
    CollectionService,
    ExtensionCommandService,
)
from backend.dtos.extension import (
    ExtensionProductRequest,
    ProductChangeRequest,
    CommandAckRequest,
    HeartbeatRequest,
)

router = APIRouter(prefix="/extension", tags=["extension"])

# Phase 1: 간단한 API 키 검증
EXTENSION_API_KEY = "sourcing-extension-phase1-key"  # TODO: settings에서 읽기


def verify_extension_key(x_extension_key: str = Header(...)) -> str:
    """익스텐션 API 키 검증"""
    if x_extension_key != EXTENSION_API_KEY:
        raise HTTPException(status_code=401, detail="유효하지 않은 익스텐션 키")
    return x_extension_key


@router.get("/commands")
async def get_pending_commands(
    _key: str = Depends(verify_extension_key),
    session: AsyncSession = Depends(get_write_session_dependency),
):
    """대기 중인 명령 조회 (익스텐션 폴링)"""
    service = ExtensionCommandService(session)
    commands = await service.get_pending_commands()
    return [
        {
            "id": cmd.id,
            "command_type": cmd.command_type,
            "payload": cmd.payload,
        }
        for cmd in commands
    ]


@router.post("/commands/{command_id}/ack")
async def ack_command(
    command_id: int,
    data: CommandAckRequest,
    _key: str = Depends(verify_extension_key),
    session: AsyncSession = Depends(get_write_session_dependency),
):
    """명령 처리 완료 보고"""
    service = ExtensionCommandService(session)
    result = await service.ack_command(
        command_id=command_id,
        status=data.status,
        message=data.message,
    )
    if not result:
        raise HTTPException(status_code=404, detail="명령을 찾을 수 없습니다")
    return {"status": "ok"}


@router.post("/products")
async def receive_collected_product(
    data: ExtensionProductRequest,
    _key: str = Depends(verify_extension_key),
    session: AsyncSession = Depends(get_write_session_dependency),
):
    """수집된 상품 데이터 수신"""
    service = CollectionService(session)
    # TODO: source_id를 source 문자열로부터 조회하는 로직 추가
    result = await service.process_collected_product(
        source=data.source,
        product_data=data.product,
        source_id=1,  # Phase 1: 무신사 고정. Phase 2에서 소싱처 조회
    )
    product = result["product"]
    response = {"status": "ok", "product_id": product.id}
    if result.get("ip_warning"):
        response["warning"] = result["ip_warning"]
    return response


@router.post("/products/{product_id}/changes")
async def receive_product_changes(
    product_id: int,
    data: ProductChangeRequest,
    _key: str = Depends(verify_extension_key),
    session: AsyncSession = Depends(get_write_session_dependency),
):
    """모니터링 변동 데이터 수신"""
    from backend.services.market_sync import MarketSyncService
    from backend.adapters.naver_adapter import NaverAdapter

    adapter = NaverAdapter()
    sync = MarketSyncService(session, adapter)

    updated = []
    if data.change_type in ("price", "both") and data.new_price:
        # TODO: MarketTemplate에서 commission_rate, margin_rate 조회
        result = await sync.sync_price_change(
            product_id=product_id,
            new_price=data.new_price,
            commission_rate=0.05,
            margin_rate=0.20,
        )
        updated.extend(result)

    if data.change_type in ("stock", "both") and data.stock_status:
        in_stock = data.stock_status == "in_stock"
        result = await sync.sync_stock_change(
            product_id=product_id,
            in_stock=in_stock,
        )
        updated.extend(result)

    return {"status": "ok", "updated_listings": updated}


@router.post("/heartbeat")
async def receive_heartbeat(
    data: HeartbeatRequest,
    _key: str = Depends(verify_extension_key),
):
    """익스텐션 생존 신호"""
    # Phase 1: 로그만 기록, Phase 2에서 offline 감지 추가
    return {"status": "ok"}
```

- [ ] **Step 3: main.py에 라우터 등록**

`backend/backend/main.py`에 추가:
```python
from backend.api.v1.routers.extension import router as extension_router
# include_router 부분에 추가
app.include_router(extension_router, prefix="/api/v1")
```

- [ ] **Step 4: 테스트 실행 — PASS 확인**

```bash
cd backend
source .venv/Scripts/activate && python -m pytest tests/api/test_extension_router.py -v
```

- [ ] **Step 5: 커밋**

```bash
git add -A
git commit -m "feat: 익스텐션 통신 API 라우터 추가

- GET /extension/commands (명령 큐 폴링)
- POST /extension/products (수집 데이터 수신 + 브랜드 IP 경고)
- POST /extension/products/{id}/changes (모니터링 변동)
- POST /extension/heartbeat (생존 신호)
- API 키 기반 인증 (X-Extension-Key)"
```

---

### Task 4: 백엔드 — 수집 설정 + 로그 + 상품 API 라우터

**Files:**
- Create: `backend/backend/api/v1/routers/collection_settings.py`
- Create: `backend/backend/api/v1/routers/collection_logs.py`
- Create: `backend/backend/api/v1/routers/products.py`
- Modify: `backend/backend/main.py`
- Test: `backend/tests/api/test_collection_settings_router.py`

- [ ] **Step 1: 수집 설정 라우터 구현 (JWT 인증 포함)**

```python
# backend/backend/api/v1/routers/collection_settings.py
"""수집 설정 CRUD API 라우터.

대시보드에서 사용하는 API — 기존 JWT 인증 적용.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.orm import get_write_session_dependency, get_read_session_dependency
from backend.domain.collection.service import CollectionService
from backend.dtos.collection import (
    CollectionSettingCreateRequest,
    CollectionSettingUpdateRequest,
    CollectionSettingResponse,
)
# Phase 1: 인증 의존성 (기존 프로젝트에 있으면 사용, 없으면 별도 구현)
# from backend.api.v1.dependencies import get_current_user

router = APIRouter(prefix="/collection-settings", tags=["collection-settings"])


@router.post("", response_model=CollectionSettingResponse)
async def create_setting(
    data: CollectionSettingCreateRequest,
    session: AsyncSession = Depends(get_write_session_dependency),
):
    """수집 설정 생성"""
    service = CollectionService(session)
    setting = await service.create_setting(data)
    return setting


@router.get("", response_model=List[CollectionSettingResponse])
async def list_settings(
    session: AsyncSession = Depends(get_read_session_dependency),
):
    """수집 설정 목록"""
    service = CollectionService(session)
    return await service.list_settings()


@router.get("/{setting_id}", response_model=CollectionSettingResponse)
async def get_setting(
    setting_id: int,
    session: AsyncSession = Depends(get_read_session_dependency),
):
    """수집 설정 상세"""
    service = CollectionService(session)
    setting = await service.get_setting(setting_id)
    if not setting:
        raise HTTPException(status_code=404, detail="수집 설정을 찾을 수 없습니다")
    return setting


@router.put("/{setting_id}", response_model=CollectionSettingResponse)
async def update_setting(
    setting_id: int,
    data: CollectionSettingUpdateRequest,
    session: AsyncSession = Depends(get_write_session_dependency),
):
    """수집 설정 수정"""
    service = CollectionService(session)
    result = await service.update_setting(setting_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="수집 설정을 찾을 수 없습니다")
    return result


@router.delete("/{setting_id}")
async def delete_setting(
    setting_id: int,
    session: AsyncSession = Depends(get_write_session_dependency),
):
    """수집 설정 삭제"""
    service = CollectionService(session)
    success = await service.delete_setting(setting_id)
    if not success:
        raise HTTPException(status_code=404, detail="수집 설정을 찾을 수 없습니다")
    return {"status": "ok"}
```

- [ ] **Step 2: 수집 로그 라우터 + SSE 구현**

```python
# backend/backend/api/v1/routers/collection_logs.py
"""수집 로그 조회 + SSE 실시간 스트림."""
import asyncio
import json
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from backend.db.orm import get_read_session_dependency
from backend.domain.collection.service import CollectionService

router = APIRouter(prefix="/collection-logs", tags=["collection-logs"])


@router.get("")
async def list_logs(
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_read_session_dependency),
):
    """수집 로그 목록"""
    service = CollectionService(session)
    logs = await service.list_logs(limit=limit, skip=skip)
    return [
        {
            "id": log.id,
            "setting_id": log.setting_id,
            "product_name": log.product_name,
            "status": log.status,
            "message": log.message,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/stream")
async def stream_logs():
    """SSE 실시간 로그 스트림 (Phase 1: 폴링 기반)"""
    async def event_generator():
        last_log_id = 0
        while True:
            # Phase 1: 5초마다 최신 로그 체크
            # Phase 2에서 Redis Pub/Sub 등으로 실시간 전환
            yield {"event": "heartbeat", "data": json.dumps({"status": "alive"})}
            await asyncio.sleep(5)

    return EventSourceResponse(event_generator())
```

- [ ] **Step 3: 상품 관리 라우터 구현**

```python
# backend/backend/api/v1/routers/products.py
"""상품 관리 API 라우터.

대시보드에서 수집된 상품 목록/상세를 조회하는 API.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.orm import get_read_session_dependency
from backend.domain.product.service import ProductService
from backend.domain.product.model import ProductStatusEnum

router = APIRouter(prefix="/products", tags=["products"])


@router.get("")
async def list_products(
    source_id: Optional[int] = Query(None),
    brand_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_read_session_dependency),
):
    """수집된 상품 목록"""
    service = ProductService(session)
    status_enum = ProductStatusEnum(status) if status else None
    products = await service.list_products(
        source_id=source_id,
        brand_id=brand_id,
        status=status_enum,
        skip=skip,
        limit=limit,
    )
    return [
        {
            "id": p.id,
            "name": p.name,
            "original_price": p.original_price,
            "brand_id": p.brand_id,
            "source_url": p.source_url,
            "stock_status": p.stock_status,
            "thumbnail_url": p.thumbnail_url,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in products
    ]


@router.get("/{product_id}")
async def get_product(
    product_id: int,
    session: AsyncSession = Depends(get_read_session_dependency),
):
    """상품 상세"""
    service = ProductService(session)
    product = await service.repo.get_async(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
    return {
        "id": product.id,
        "name": product.name,
        "original_price": product.original_price,
        "brand_id": product.brand_id,
        "source_id": product.source_id,
        "source_url": product.source_url,
        "source_product_id": product.source_product_id,
        "stock_status": product.stock_status,
        "thumbnail_url": product.thumbnail_url,
        "image_urls": product.image_urls,
        "status": product.status,
        "created_at": product.created_at.isoformat() if product.created_at else None,
    }
```

- [ ] **Step 4: main.py에 라우터 등록 추가**

```python
from backend.api.v1.routers.collection_settings import router as collection_settings_router
from backend.api.v1.routers.collection_logs import router as collection_logs_router
from backend.api.v1.routers.products import router as products_router

app.include_router(collection_settings_router, prefix="/api/v1")
app.include_router(collection_logs_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")
```

- [ ] **Step 5: 테스트 + 커밋**

```bash
cd backend
source .venv/Scripts/activate && python -m pytest tests/ -v --ignore=tests/domain/crawling --ignore=tests/services/test_scheduler.py
git add -A
git commit -m "feat: 수집 설정/로그/상품 API 라우터 추가

- 수집 설정 CRUD (PUT 사용)
- 수집 로그 조회 + SSE 스트림
- 상품 목록/상세 API
- main.py에 라우터 등록"
```

---

### Task 5: 백엔드 — DB 마이그레이션

**Files:**
- Create: `backend/alembic/versions/xxxx_add_collection_tables.py`

- [ ] **Step 1: Alembic 마이그레이션 생성**

```bash
cd backend
source .venv/Scripts/activate && alembic revision --autogenerate -m "add collection_settings, collection_logs, extension_commands tables"
```

마이그레이션이 자동 생성 안 되면 수동 작성:

```python
# 마이그레이션 파일 내용 (자동생성 대체)
def upgrade() -> None:
    op.create_table(
        "collection_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("brand_name", sa.String(200), nullable=False),
        sa.Column("category_url", sa.Text(), nullable=False),
        sa.Column("max_count", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_collection_settings_source_id", "collection_settings", ["source_id"])
    op.create_index("ix_collection_settings_is_active", "collection_settings", ["is_active"])

    op.create_table(
        "collection_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("setting_id", sa.Integer(), sa.ForeignKey("collection_settings.id"), nullable=True),
        sa.Column("product_name", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_collection_logs_created_at", "collection_logs", ["created_at"])

    op.create_table(
        "extension_commands",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("command_type", sa.String(50), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_extension_commands_status", "extension_commands", ["status"])


def downgrade() -> None:
    op.drop_table("extension_commands")
    op.drop_table("collection_logs")
    op.drop_table("collection_settings")
```

- [ ] **Step 2: 마이그레이션 적용**

```bash
cd backend
alembic upgrade head
```

- [ ] **Step 3: 커밋**

```bash
git add -A
git commit -m "feat: 수집 도메인 DB 마이그레이션 추가

- collection_settings, collection_logs, extension_commands 테이블"
```

---

### Task 6: 크롬 익스텐션 — 프로젝트 셋업 (Vite 5 + CRXJS)

**Files:**
- Create: `extension/package.json`
- Create: `extension/vite.config.ts`
- Create: `extension/tsconfig.json`
- Create: `extension/tailwind.config.ts`
- Create: `extension/postcss.config.js`
- Create: `extension/manifest.json`
- Create: `extension/src/shared/types.ts`
- Create: `extension/src/shared/constants.ts`

- [ ] **Step 1: package.json 생성**

```json
{
  "name": "sourcing-extension",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "zustand": "^5.0.0"
  },
  "devDependencies": {
    "@crxjs/vite-plugin": "^2.0.0-beta.28",
    "@vitejs/plugin-react": "^4.3.0",
    "@types/chrome": "^0.0.287",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.7.0",
    "vite": "^5.4.0"
  }
}
```

**주의:** Vite 5 사용 (CRXJS 2.0.0-beta.28은 Vite 6 미지원). `@vitejs/plugin-react` 추가.

- [ ] **Step 2: Vite + CRXJS 설정**

```typescript
// extension/vite.config.ts
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import { crx } from "@crxjs/vite-plugin"
import manifest from "./manifest.json"

export default defineConfig({
  plugins: [
    react(),
    crx({ manifest }),
  ],
})
```

```json
// extension/manifest.json
{
  "manifest_version": 3,
  "name": "소싱 어시스턴트",
  "version": "1.0.0",
  "description": "무재고 구매대행 상품 수집 익스텐션",
  "permissions": ["alarms", "storage", "notifications", "tabs"],
  "host_permissions": [
    "https://*.musinsa.com/*",
    "https://api.musinsa.com/*",
    "http://localhost:28080/*"
  ],
  "background": {
    "service_worker": "src/background/index.ts",
    "type": "module"
  },
  "content_scripts": [
    {
      "matches": ["https://www.musinsa.com/app/goods/*"],
      "js": ["src/content/musinsa-interceptor.ts"],
      "run_at": "document_start"
    },
    {
      "matches": ["https://www.musinsa.com/app/goods/*"],
      "js": ["src/content/musinsa-product.tsx"],
      "run_at": "document_idle"
    }
  ],
  "action": {
    "default_popup": "src/popup/index.html"
  }
}
```

**중요:** `content_scripts`를 2개로 분리:
- `musinsa-interceptor.ts`: `document_start` (fetch 오버라이드가 API 호출 전에 주입)
- `musinsa-product.tsx`: `document_idle` (DOM 준비 후 버튼 삽입)

- [ ] **Step 3: 공유 타입/상수**

```typescript
// extension/src/shared/types.ts
/** 수집 상품 데이터 (백엔드 전송용) */
export interface ProductData {
  name: string
  original_price: number
  source_url: string
  source_product_id: string
  brand_name: string
  stock_status: string
  grade_discount_available: boolean
  point_usable: boolean
  point_earnable: boolean
  thumbnail_url: string | null
  image_urls: string[]
  options: ProductOption[]
}

export interface ProductOption {
  color: string | null
  size: string | null
  stock: number
}

/** 백엔드 명령 */
export interface ExtensionCommand {
  id: number
  command_type: string
  payload: string
}

/** 모니터링 대상 */
export interface MonitoringItem {
  product_id: number
  source_url: string
  grade: string
  last_price: number
  last_stock_status: string
}

/** Content Script → Background 메시지 */
export type ContentMessage =
  | { type: "PRODUCT_DATA_CAPTURED"; data: ProductData }
  | { type: "COLLECT_BUTTON_CLICKED"; data: ProductData }
  | { type: "MONITORING_DATA_CAPTURED"; productId: number; data: ProductData }

/** Background → Content Script 메시지 */
export type BackgroundMessage =
  | { type: "PRODUCT_DATA_READY"; data: ProductData }
```

```typescript
// extension/src/shared/constants.ts
export const API_BASE_URL = "http://localhost:28080/api/v1"
export const HEARTBEAT_ALARM_NAME = "heartbeat"
export const COMMAND_POLL_ALARM_NAME = "command-poll"
```

- [ ] **Step 4: tsconfig, tailwind, postcss 설정**

```json
// extension/tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "dist",
    "rootDir": "src"
  },
  "include": ["src"]
}
```

```typescript
// extension/tailwind.config.ts
import type { Config } from "tailwindcss"
const config: Config = {
  content: ["./src/**/*.{ts,tsx,html}"],
  theme: { extend: {} },
  plugins: [],
}
export default config
```

```javascript
// extension/postcss.config.js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 5: 의존성 설치 + 빌드 테스트**

```bash
cd /c/Users/tjdql/wnsrlf/advanced-harness-main/extension
pnpm install
pnpm build
```

- [ ] **Step 6: 커밋**

```bash
git add extension/
git commit -m "feat: 크롬 익스텐션 프로젝트 셋업 (Vite 5 + CRXJS + Manifest V3)"
```

---

### Task 7: 크롬 익스텐션 — Background Service Worker

**Files:**
- Create: `extension/src/background/index.ts`
- Create: `extension/src/background/api-client.ts`
- Create: `extension/src/background/command-poller.ts`
- Create: `extension/src/background/monitoring-manager.ts`

- [ ] **Step 1: API Client 구현**

```typescript
// extension/src/background/api-client.ts
import { API_BASE_URL } from "../shared/constants"
import type { ExtensionCommand, ProductData } from "../shared/types"

/** chrome.storage.local에서 API 키 읽기 */
async function getApiKey(): Promise<string> {
  const result = await chrome.storage.local.get("apiKey")
  return result.apiKey || ""
}

/** 공통 헤더 */
async function getHeaders(): Promise<HeadersInit> {
  const apiKey = await getApiKey()
  return {
    "Content-Type": "application/json",
    "X-Extension-Key": apiKey,
  }
}

/** 대기 중인 명령 조회 */
export async function fetchPendingCommands(): Promise<ExtensionCommand[]> {
  const headers = await getHeaders()
  const res = await fetch(`${API_BASE_URL}/extension/commands`, { headers })
  if (!res.ok) return []
  return res.json()
}

/** 명령 처리 완료 보고 */
export async function ackCommand(
  commandId: number,
  status: "done" | "failed" = "done",
): Promise<void> {
  const headers = await getHeaders()
  await fetch(`${API_BASE_URL}/extension/commands/${commandId}/ack`, {
    method: "POST",
    headers,
    body: JSON.stringify({ status }),
  })
}

/** 수집 상품 전송 */
export async function sendCollectedProduct(
  source: string,
  product: ProductData,
): Promise<{ product_id: number; warning?: string } | null> {
  const headers = await getHeaders()
  const res = await fetch(`${API_BASE_URL}/extension/products`, {
    method: "POST",
    headers,
    body: JSON.stringify({ source, product }),
  })
  if (!res.ok) return null
  return res.json()
}

/** 모니터링 변동 전송 */
export async function sendProductChange(
  productId: number,
  changeType: string,
  oldPrice: number | null,
  newPrice: number | null,
  stockStatus: string | null,
): Promise<void> {
  const headers = await getHeaders()
  await fetch(`${API_BASE_URL}/extension/products/${productId}/changes`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      change_type: changeType,
      old_price: oldPrice,
      new_price: newPrice,
      stock_status: stockStatus,
    }),
  })
}

/** Heartbeat 전송 */
export async function sendHeartbeat(monitoringCount: number): Promise<void> {
  const headers = await getHeaders()
  await fetch(`${API_BASE_URL}/extension/heartbeat`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      monitoring_count: monitoringCount,
      extension_version: "1.0.0",
    }),
  }).catch(() => {
    // 서버 다운 시 무시
  })
}
```

- [ ] **Step 2: Command Poller 구현**

```typescript
// extension/src/background/command-poller.ts
import { COMMAND_POLL_ALARM_NAME } from "../shared/constants"
import { fetchPendingCommands, ackCommand } from "./api-client"
import { registerMonitoring, unregisterMonitoring } from "./monitoring-manager"

/** 명령 폴링 알람 등록 */
export function startCommandPolling(): void {
  // chrome.alarms 최소 주기 1분 (MV3 제약)
  chrome.alarms.create(COMMAND_POLL_ALARM_NAME, {
    periodInMinutes: 1,
  })
}

/** 명령 폴링 처리 */
export async function handleCommandPoll(): Promise<void> {
  const commands = await fetchPendingCommands()

  for (const cmd of commands) {
    try {
      const payload = JSON.parse(cmd.payload)

      switch (cmd.command_type) {
        case "monitor_register":
          await registerMonitoring(
            payload.product_id,
            payload.source_url,
            payload.grade || "normal",
          )
          break
        case "monitor_unregister":
          await unregisterMonitoring(payload.product_id)
          break
        default:
          console.warn(`알 수 없는 명령: ${cmd.command_type}`)
      }

      await ackCommand(cmd.id, "done")
    } catch (error) {
      console.error(`명령 처리 실패: ${cmd.id}`, error)
      await ackCommand(cmd.id, "failed")
    }
  }
}
```

- [ ] **Step 3: Monitoring Manager 구현**

```typescript
// extension/src/background/monitoring-manager.ts
import type { MonitoringItem, ProductData } from "../shared/types"
import { sendProductChange } from "./api-client"

const MONITORING_STORAGE_KEY = "monitoringItems"
const MONITOR_ALARM_PREFIX = "monitor_"

/** 모니터링 목록 로드 (chrome.storage.local) */
async function loadMonitoringItems(): Promise<MonitoringItem[]> {
  const result = await chrome.storage.local.get(MONITORING_STORAGE_KEY)
  return result[MONITORING_STORAGE_KEY] || []
}

/** 모니터링 목록 저장 */
async function saveMonitoringItems(items: MonitoringItem[]): Promise<void> {
  await chrome.storage.local.set({ [MONITORING_STORAGE_KEY]: items })
}

/** 모니터링 등록 */
export async function registerMonitoring(
  productId: number,
  sourceUrl: string,
  grade: string,
): Promise<void> {
  const items = await loadMonitoringItems()

  // 중복 방지
  if (items.some((item) => item.product_id === productId)) return

  items.push({
    product_id: productId,
    source_url: sourceUrl,
    grade,
    last_price: 0,
    last_stock_status: "unknown",
  })
  await saveMonitoringItems(items)

  // 랜덤 주기 알람 등록
  const intervalMinutes = getRandomInterval(grade)
  chrome.alarms.create(`${MONITOR_ALARM_PREFIX}${productId}`, {
    periodInMinutes: intervalMinutes,
  })
}

/** 모니터링 해제 */
export async function unregisterMonitoring(productId: number): Promise<void> {
  const items = await loadMonitoringItems()
  const filtered = items.filter((item) => item.product_id !== productId)
  await saveMonitoringItems(filtered)

  chrome.alarms.clear(`${MONITOR_ALARM_PREFIX}${productId}`)
}

/** 모니터링 알람 처리 (탭 열어서 데이터 수집) */
export async function handleMonitoringAlarm(alarmName: string): Promise<void> {
  const productId = parseInt(alarmName.replace(MONITOR_ALARM_PREFIX, ""), 10)
  if (isNaN(productId)) return

  const items = await loadMonitoringItems()
  const item = items.find((i) => i.product_id === productId)
  if (!item) return

  // 백그라운드 탭으로 무신사 상품 페이지 열기
  const tab = await chrome.tabs.create({
    url: item.source_url,
    active: false,
  })

  // Content Script가 데이터를 캡처하면 메시지로 받음
  // 일회성 알람으로 30초 후 탭 닫기 (setTimeout 대신 chrome.alarms 사용)
  if (tab.id) {
    chrome.alarms.create(`tab_cleanup_${tab.id}`, { delayInMinutes: 0.5 })
  }
}

/** 모니터링 데이터 비교 + 변동 전송 */
export async function checkProductChanges(
  productId: number,
  newData: ProductData,
): Promise<void> {
  const items = await loadMonitoringItems()
  const item = items.find((i) => i.product_id === productId)
  if (!item || item.last_price === 0) {
    // 최초 데이터 → 저장만
    if (item) {
      item.last_price = newData.original_price
      item.last_stock_status = newData.stock_status
      await saveMonitoringItems(items)
    }
    return
  }

  const priceChanged = newData.original_price !== item.last_price
  const stockChanged = newData.stock_status !== item.last_stock_status

  if (priceChanged || stockChanged) {
    let changeType = "both"
    if (priceChanged && !stockChanged) changeType = "price"
    if (!priceChanged && stockChanged) changeType = "stock"

    await sendProductChange(
      productId,
      changeType,
      priceChanged ? item.last_price : null,
      priceChanged ? newData.original_price : null,
      stockChanged ? newData.stock_status : null,
    )

    // 로컬 상태 업데이트
    item.last_price = newData.original_price
    item.last_stock_status = newData.stock_status
    await saveMonitoringItems(items)
  }
}

/** 등급별 랜덤 주기 (분) — chrome.alarms 최소 1분 */
function getRandomInterval(grade: string): number {
  if (grade === "high") {
    // 8~17분
    return 8 + Math.random() * 9
  }
  // 25~65분
  return 25 + Math.random() * 40
}

/** 모니터링 중인 상품 수 */
export async function getMonitoringCount(): Promise<number> {
  const items = await loadMonitoringItems()
  return items.length
}
```

- [ ] **Step 4: Service Worker 진입점 구현**

```typescript
// extension/src/background/index.ts
import { COMMAND_POLL_ALARM_NAME, HEARTBEAT_ALARM_NAME } from "../shared/constants"
import { sendHeartbeat, sendCollectedProduct } from "./api-client"
import { startCommandPolling, handleCommandPoll } from "./command-poller"
import {
  handleMonitoringAlarm,
  checkProductChanges,
  getMonitoringCount,
} from "./monitoring-manager"
import type { ContentMessage } from "../shared/types"

const MONITOR_ALARM_PREFIX = "monitor_"
const TAB_CLEANUP_PREFIX = "tab_cleanup_"

// 알람 이벤트 핸들러
chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === COMMAND_POLL_ALARM_NAME) {
    await handleCommandPoll()
  } else if (alarm.name === HEARTBEAT_ALARM_NAME) {
    const count = await getMonitoringCount()
    await sendHeartbeat(count)
  } else if (alarm.name.startsWith(MONITOR_ALARM_PREFIX)) {
    await handleMonitoringAlarm(alarm.name)
  } else if (alarm.name.startsWith(TAB_CLEANUP_PREFIX)) {
    // 모니터링 탭 정리
    const tabId = parseInt(alarm.name.replace(TAB_CLEANUP_PREFIX, ""), 10)
    if (!isNaN(tabId)) {
      try { await chrome.tabs.remove(tabId) } catch { /* 이미 닫힘 */ }
    }
  }
})

// Content Script 메시지 핸들러
chrome.runtime.onMessage.addListener((message: ContentMessage, sender, sendResponse) => {
  if (message.type === "COLLECT_BUTTON_CLICKED") {
    // 개별 수집: 백엔드로 전송
    sendCollectedProduct("musinsa", message.data).then((result) => {
      sendResponse({
        success: !!result,
        product_id: result?.product_id,
        warning: result?.warning,
      })
    })
    return true // 비동기 응답
  }

  if (message.type === "MONITORING_DATA_CAPTURED") {
    // 모니터링 데이터 수신: 변동 비교
    checkProductChanges(message.productId, message.data)
    sendResponse({ success: true })
    return true
  }

  if (message.type === "PRODUCT_DATA_CAPTURED") {
    // interceptor에서 데이터 캡처됨 → 같은 탭의 product script에 전달
    if (sender.tab?.id) {
      chrome.tabs.sendMessage(sender.tab.id, {
        type: "PRODUCT_DATA_READY",
        data: message.data,
      })
    }
    sendResponse({ success: true })
  }
})

// 익스텐션 설치/업데이트 시 초기화
chrome.runtime.onInstalled.addListener(() => {
  startCommandPolling()

  // Heartbeat 알람 (1분마다)
  chrome.alarms.create(HEARTBEAT_ALARM_NAME, { periodInMinutes: 1 })

  console.log("소싱 어시스턴트 익스텐션 초기화 완료")
})

// Service Worker 시작 시 폴링 재시작 (SW 재시작 대응)
startCommandPolling()
```

**중요 수정사항:**
- `PRODUCT_DATA_CAPTURED` 수신 시 `chrome.tabs.sendMessage()`로 동일 탭의 Content Script(musinsa-product)에 `PRODUCT_DATA_READY` 전달
- 탭 정리를 `setTimeout` 대신 `chrome.alarms`로 처리 (SW 종료 대응)

- [ ] **Step 5: 빌드 확인 + 커밋**

```bash
cd /c/Users/tjdql/wnsrlf/advanced-harness-main/extension
pnpm build
git add extension/src/background/
git commit -m "feat: 익스텐션 Background Service Worker (API 클라이언트, 폴링, 모니터링)"
```

---

### Task 8: 크롬 익스텐션 — Content Script (인터셉터 + 수집 버튼)

**Files:**
- Create: `extension/src/content/musinsa-interceptor.ts`
- Create: `extension/src/content/musinsa-product.tsx`
- Create: `extension/src/content/musinsa-product.css`

- [ ] **Step 1: fetch/XHR 오버라이드 인터셉터 구현**

```typescript
// extension/src/content/musinsa-interceptor.ts
/**
 * 무신사 페이지에 스크립트를 주입하여 fetch/XHR을 오버라이드.
 * 무신사 내부 API 응답을 가로채서 상품 데이터를 파싱합니다.
 *
 * 흐름: 주입 스크립트 → window.postMessage → Content Script → Background SW
 *
 * manifest.json에서 run_at: "document_start"로 실행 (API 호출 전 주입)
 */

// 페이지 컨텍스트에 주입할 스크립트
const injectedScript = `
(function() {
  const originalFetch = window.fetch;

  window.fetch = async function(...args) {
    const response = await originalFetch.apply(this, args);
    const url = typeof args[0] === "string" ? args[0] : args[0]?.url || "";

    // 무신사 상품 상세 API 감지
    if (url.includes("/api2/hm/goods/") || url.includes("/api/goods/")) {
      try {
        const clone = response.clone();
        const data = await clone.json();
        window.postMessage({
          type: "MUSINSA_API_RESPONSE",
          url: url,
          data: data,
        }, "*");
      } catch(e) { /* 파싱 실패 무시 */ }
    }

    return response;
  };
})();
`

// 페이지 컨텍스트에 스크립트 주입
const script = document.createElement("script")
script.textContent = injectedScript
document.documentElement.appendChild(script)
script.remove()

// 주입된 스크립트에서 보내는 메시지 수신
window.addEventListener("message", (event) => {
  if (event.source !== window) return
  if (event.data?.type !== "MUSINSA_API_RESPONSE") return

  const { url, data } = event.data

  // 무신사 API 응답에서 상품 데이터 파싱
  const productData = parseMusinsaProduct(data)
  if (productData) {
    // Background SW로 전달 (Background가 다시 product script에 PRODUCT_DATA_READY 전달)
    chrome.runtime.sendMessage({
      type: "PRODUCT_DATA_CAPTURED",
      data: productData,
    })
  }
})

/** 무신사 API 응답 → ProductData 파싱 */
function parseMusinsaProduct(apiData: Record<string, unknown>): Record<string, unknown> | null {
  try {
    // 무신사 API 응답 구조에 맞게 파싱 (실제 API 분석 후 조정 필요)
    const data = (apiData as Record<string, unknown>).data as Record<string, unknown> | undefined
    if (!data) return null

    const goodsNo = data.goodsNo || data.goodsNumber
    if (!goodsNo) return null

    const benefitInfo = (data.benefitInfo || {}) as Record<string, unknown>

    return {
      name: data.goodsName || data.goodsNm || "",
      original_price: Number(data.normalPrice || data.goodsPrice || 0),
      source_url: `https://www.musinsa.com/app/goods/${goodsNo}`,
      source_product_id: String(goodsNo),
      brand_name: data.brandName || (data.brand as Record<string, unknown>)?.name || "",
      stock_status: data.isSoldOut ? "out_of_stock" : "in_stock",
      grade_discount_available: benefitInfo.gradeDiscountAvailable !== false,
      point_usable: benefitInfo.pointUsable !== false,
      point_earnable: benefitInfo.pointEarnable !== false,
      thumbnail_url: data.thumbnailImageUrl || data.goodsImage || null,
      image_urls: (data.imageUrls || []) as string[],
      options: [], // Phase 2에서 옵션 파싱 추가
    }
  } catch {
    return null
  }
}
```

- [ ] **Step 2: 수집 버튼 Content Script 구현**

```tsx
// extension/src/content/musinsa-product.tsx
/**
 * 무신사 상품 상세 페이지에 [수집하기] 버튼을 삽입합니다.
 *
 * manifest.json에서 run_at: "document_idle"로 실행 (DOM 준비 후)
 *
 * 데이터 흐름:
 * 1. interceptor가 API 응답 캡처 → Background SW로 전송
 * 2. Background SW가 chrome.tabs.sendMessage()로 이 스크립트에 PRODUCT_DATA_READY 전달
 * 3. 사용자가 [수집하기] 클릭 → COLLECT_BUTTON_CLICKED → Background SW → 백엔드
 */
import type { ProductData, BackgroundMessage } from "../shared/types"

let capturedProductData: ProductData | null = null

// Background SW에서 PRODUCT_DATA_READY 수신 (tabs.sendMessage로 전달됨)
chrome.runtime.onMessage.addListener((message: BackgroundMessage, sender, sendResponse) => {
  if (message.type === "PRODUCT_DATA_READY") {
    capturedProductData = message.data
    updateButtonState("ready")
    sendResponse({ success: true })
  }
})

// 수집 버튼 생성 및 삽입
function createCollectButton(): HTMLButtonElement {
  const button = document.createElement("button")
  button.id = "sourcing-collect-btn"
  button.textContent = "데이터 로딩중..."
  button.disabled = true
  button.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 99999;
    padding: 12px 24px;
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    transition: all 0.2s;
  `

  button.addEventListener("click", handleCollectClick)
  document.body.appendChild(button)
  return button
}

function updateButtonState(state: "loading" | "ready" | "collecting" | "done" | "error"): void {
  const button = document.getElementById("sourcing-collect-btn") as HTMLButtonElement
  if (!button) return

  switch (state) {
    case "loading":
      button.textContent = "데이터 로딩중..."
      button.disabled = true
      button.style.background = "#6b7280"
      break
    case "ready":
      button.textContent = "수집하기"
      button.disabled = false
      button.style.background = "#2563eb"
      break
    case "collecting":
      button.textContent = "수집 중..."
      button.disabled = true
      button.style.background = "#f59e0b"
      break
    case "done":
      button.textContent = "수집 완료"
      button.disabled = true
      button.style.background = "#10b981"
      break
    case "error":
      button.textContent = "수집 실패"
      button.disabled = false
      button.style.background = "#ef4444"
      break
  }
}

async function handleCollectClick(): Promise<void> {
  if (!capturedProductData) return

  updateButtonState("collecting")

  try {
    const response = await chrome.runtime.sendMessage({
      type: "COLLECT_BUTTON_CLICKED",
      data: capturedProductData,
    })

    if (response?.success) {
      updateButtonState("done")
      // 브랜드 지재권 경고 표시
      if (response.warning) {
        console.warn(`[소싱 어시스턴트] ${response.warning}`)
      }
    } else {
      updateButtonState("error")
    }
  } catch {
    updateButtonState("error")
  }
}

// 페이지 로드 시 버튼 삽입 (document_idle이므로 DOM 준비됨)
createCollectButton()
```

- [ ] **Step 3: 빌드 + 커밋**

```bash
cd /c/Users/tjdql/wnsrlf/advanced-harness-main/extension
pnpm build
git add extension/src/content/
git commit -m "feat: Content Script (fetch/XHR 인터셉터 + 수집 버튼)

- interceptor: document_start에서 fetch 오버라이드 주입
- product: document_idle에서 수집 버튼 삽입
- 메시지 흐름: interceptor → Background → product (tabs.sendMessage)"
```

---

### Task 9: 크롬 익스텐션 — Popup UI

**Files:**
- Create: `extension/src/popup/index.html`
- Create: `extension/src/popup/index.tsx`
- Create: `extension/src/popup/Popup.tsx`
- Create: `extension/src/popup/popup.css`

- [ ] **Step 1: Popup 구현**

```html
<!-- extension/src/popup/index.html -->
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8" /></head>
<body>
  <div id="root"></div>
  <script type="module" src="./index.tsx"></script>
</body>
</html>
```

```tsx
// extension/src/popup/index.tsx
import React from "react"
import { createRoot } from "react-dom/client"
import { Popup } from "./Popup"
import "./popup.css"

createRoot(document.getElementById("root")!).render(<Popup />)
```

```tsx
// extension/src/popup/Popup.tsx
import React, { useEffect, useState } from "react"

export function Popup() {
  const [apiKey, setApiKey] = useState("")
  const [serverStatus, setServerStatus] = useState<"checking" | "online" | "offline">("checking")
  const [monitoringCount, setMonitoringCount] = useState(0)

  useEffect(() => {
    // 저장된 API 키 로드
    chrome.storage.local.get(["apiKey"], (result) => {
      if (result.apiKey) setApiKey(result.apiKey)
    })

    // 모니터링 수 로드
    chrome.storage.local.get(["monitoringItems"], (result) => {
      const items = result.monitoringItems || []
      setMonitoringCount(items.length)
    })

    // 서버 상태 확인
    checkServerStatus()
  }, [])

  async function checkServerStatus() {
    try {
      const result = await chrome.storage.local.get("apiKey")
      const res = await fetch("http://localhost:28080/api/v1/extension/heartbeat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Extension-Key": result.apiKey || "",
        },
        body: JSON.stringify({ monitoring_count: 0, extension_version: "1.0.0" }),
      })
      setServerStatus(res.ok ? "online" : "offline")
    } catch {
      setServerStatus("offline")
    }
  }

  function saveApiKey() {
    chrome.storage.local.set({ apiKey })
    checkServerStatus()
  }

  return (
    <div style={{ width: 320, padding: 16, fontFamily: "sans-serif" }}>
      <h2 style={{ fontSize: 16, marginBottom: 12 }}>소싱 어시스턴트</h2>

      {/* 서버 상태 */}
      <div style={{ marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{
          width: 8, height: 8, borderRadius: "50%",
          background: serverStatus === "online" ? "#10b981"
            : serverStatus === "offline" ? "#ef4444" : "#f59e0b",
        }} />
        <span style={{ fontSize: 13 }}>
          서버: {serverStatus === "online" ? "연결됨" : serverStatus === "offline" ? "연결 끊김" : "확인 중..."}
        </span>
      </div>

      {/* 모니터링 현황 */}
      <div style={{ marginBottom: 16, fontSize: 13, color: "#6b7280" }}>
        모니터링 중: {monitoringCount}개 상품
      </div>

      {/* API 키 설정 */}
      <div>
        <label style={{ fontSize: 12, color: "#6b7280" }}>API 키</label>
        <div style={{ display: "flex", gap: 4, marginTop: 4 }}>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="API 키 입력"
            style={{
              flex: 1, padding: "6px 8px", border: "1px solid #d1d5db",
              borderRadius: 4, fontSize: 13,
            }}
          />
          <button
            onClick={saveApiKey}
            style={{
              padding: "6px 12px", background: "#2563eb", color: "white",
              border: "none", borderRadius: 4, fontSize: 12, cursor: "pointer",
            }}
          >
            저장
          </button>
        </div>
      </div>
    </div>
  )
}
```

```css
/* extension/src/popup/popup.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  padding: 0;
}
```

- [ ] **Step 2: 빌드 + Chrome에서 사이드로딩 테스트**

```bash
cd /c/Users/tjdql/wnsrlf/advanced-harness-main/extension
pnpm build
```

Chrome → `chrome://extensions` → 개발자 모드 → "압축해제된 확장 프로그램을 로드합니다" → `extension/dist` 폴더 선택

- [ ] **Step 3: 커밋**

```bash
git add extension/src/popup/
git commit -m "feat: 익스텐션 Popup UI (서버 상태, 모니터링 현황, API 키 설정)"
```

---

### Task 10: 프론트엔드 — 타입 정의 + API 클라이언트

**Files:**
- Create: `frontend/src/types/sourcing.ts`
- Create: `frontend/src/lib/sourcing-api.ts`

**참고:** 기존 API 클라이언트 패턴은 `frontend/src/lib/api.ts` 참조 — `api.get<T>()`, `api.post<T>()` 패턴 사용.

- [ ] **Step 1: 타입 정의**

```typescript
// frontend/src/types/sourcing.ts
/** 수집 설정 */
export interface CollectionSetting {
  id: number
  name: string
  source_id: number
  brand_name: string
  category_url: string
  max_count: number
  is_active: boolean
  last_collected_at: string | null
  collected_count: number
  created_at: string
  updated_at: string
}

/** 수집 설정 생성/수정 폼 */
export interface CollectionSettingForm {
  name: string
  source_id: number
  brand_name: string
  category_url: string
  max_count: number
}

/** 수집된 상품 */
export interface SourcingProduct {
  id: number
  name: string
  original_price: number
  selling_price: number | null
  brand_name: string
  source_url: string
  stock_status: string
  thumbnail_url: string | null
  grade_discount_available: boolean
  point_usable: boolean
  listing_status: string | null
  created_at: string
}

/** 수집 로그 */
export interface CollectionLog {
  id: number
  setting_id: number | null
  product_name: string
  status: "success" | "failed"
  message: string | null
  created_at: string
}

/** 익스텐션 상태 */
export interface ExtensionStatus {
  is_online: boolean
  monitoring_count: number
  last_heartbeat: string | null
}
```

- [ ] **Step 2: 소싱 API 클라이언트**

```typescript
// frontend/src/lib/sourcing-api.ts
import { api } from "./api"
import type {
  CollectionSetting,
  CollectionSettingForm,
  SourcingProduct,
  CollectionLog,
} from "@/types/sourcing"

/** 수집 설정 API */
export const collectionSettingsApi = {
  list: () => api.get<CollectionSetting[]>("/collection-settings"),
  create: (data: CollectionSettingForm) => api.post<CollectionSetting>("/collection-settings", data),
  update: (id: number, data: Partial<CollectionSettingForm>) =>
    api.put<CollectionSetting>(`/collection-settings/${id}`, data),
  delete: (id: number) => api.delete(`/collection-settings/${id}`),
}

/** 상품 API */
export const productsApi = {
  list: (params?: { limit?: number; skip?: number }) =>
    api.get<SourcingProduct[]>(`/products?limit=${params?.limit || 50}&skip=${params?.skip || 0}`),
  get: (id: number) => api.get<SourcingProduct>(`/products/${id}`),
}

/** 수집 로그 API */
export const logsApi = {
  list: (params?: { limit?: number; skip?: number }) =>
    api.get<CollectionLog[]>(`/collection-logs?limit=${params?.limit || 50}&skip=${params?.skip || 0}`),
}
```

**수정사항:**
- `api.patch` → `api.put` (백엔드 PUT 라우터와 일치)
- `offset` → `skip` (백엔드 파라미터명과 일치)

- [ ] **Step 3: 커밋**

```bash
git add frontend/src/types/sourcing.ts frontend/src/lib/sourcing-api.ts
git commit -m "feat: 프론트엔드 소싱 타입 정의 + API 클라이언트"
```

---

### Task 11: 프론트엔드 — 소싱 대시보드 최소 UI

**Files:**
- Create: `frontend/src/app/sourcing/layout.tsx`
- Create: `frontend/src/app/sourcing/page.tsx`
- Create: `frontend/src/app/sourcing/collection-settings/page.tsx`
- Create: `frontend/src/app/sourcing/collection-settings/new/page.tsx`
- Create: `frontend/src/app/sourcing/products/page.tsx`
- Create: `frontend/src/app/sourcing/monitoring/page.tsx`
- Create: `frontend/src/app/sourcing/market-listings/page.tsx`
- Create: `frontend/src/app/sourcing/logs/page.tsx`
- Create: `frontend/src/components/sourcing/CollectionSettingsTable.tsx`
- Create: `frontend/src/components/sourcing/ProductsTable.tsx`
- Create: `frontend/src/components/sourcing/MonitoringStatus.tsx`
- Create: `frontend/src/components/sourcing/LogsViewer.tsx`
- Create: `frontend/src/components/sourcing/ExtensionStatus.tsx`

Phase 1 대시보드는 **최소 기능**: 수집 설정 목록/생성, 상품 목록, 모니터링 현황, 마켓 등록 관리, 로그 조회.
shadcn/ui 컴포넌트 + Tailwind CSS 사용.

- [ ] **Step 1: 레이아웃 + 메인 페이지**

소싱 레이아웃에 사이드바 네비게이션 포함:
```
/sourcing — 대시보드 메인 (수집 현황 요약 + 익스텐션 상태)
/sourcing/collection-settings — 수집 설정 관리
/sourcing/products — 수집된 상품 목록
/sourcing/monitoring — 모니터링 현황
/sourcing/market-listings — 마켓 등록 관리
/sourcing/logs — 수집 로그
```

`ExtensionStatus` 컴포넌트: 대시보드 메인에 익스텐션 연결 상태 표시 (최근 heartbeat 기준).

- [ ] **Step 2: 수집 설정 페이지 (목록 + 생성 폼)**

`/sourcing/collection-settings` — 설정 테이블 (오버링크 패턴)
`/sourcing/collection-settings/new` — 설정 생성 폼 (React Hook Form + Zod)

- [ ] **Step 3: 상품 목록 페이지**

`/sourcing/products` — 수집된 상품 테이블 (이미지, 상품명, 원가, 판매가, 재고)

- [ ] **Step 4: 모니터링 현황 + 마켓 등록 페이지**

`/sourcing/monitoring` — 모니터링 중인 상품 목록 (상태, 마지막 체크 시간, 변동 내역)
`/sourcing/market-listings` — 마켓 등록된 상품 관리 (등록 상태, 동기화 상태)

- [ ] **Step 5: 로그 페이지**

`/sourcing/logs` — 수집 로그 테이블 (시간, 상품명, 성공/실패, 메시지)

- [ ] **Step 6: 빌드 확인 + 커밋**

```bash
cd /c/Users/tjdql/wnsrlf/advanced-harness-main/frontend
pnpm build
git add frontend/src/app/sourcing/ frontend/src/components/sourcing/ frontend/src/types/ frontend/src/lib/sourcing-api.ts
git commit -m "feat: 소싱 대시보드 최소 UI (수집설정, 상품목록, 모니터링, 마켓등록, 로그)"
```

---

### Task 12: 통합 테스트 + 전체 파이프라인 검증

**목표:** 익스텐션 → 백엔드 → 대시보드 전체 파이프라인이 동작하는지 검증.

- [ ] **Step 1: 백엔드 전체 테스트 실행**

```bash
cd /c/Users/tjdql/wnsrlf/advanced-harness-main/backend
source .venv/Scripts/activate && python -m pytest tests/ -v --ignore=tests/domain/crawling --ignore=tests/services/test_scheduler.py
```
모든 테스트 PASS 확인

- [ ] **Step 2: 익스텐션 빌드 + 사이드로딩 설치**

```bash
cd /c/Users/tjdql/wnsrlf/advanced-harness-main/extension
pnpm build
```
Chrome에서 `extension/dist` 로드

- [ ] **Step 3: 수동 E2E 테스트**

1. 백엔드 서버 시작: `uvicorn backend.main:app --reload --port 28080`
2. 프론트엔드 시작: `cd frontend && pnpm dev`
3. 익스텐션 Popup에서 API 키 입력 → 서버 연결 확인
4. 무신사 상품 페이지 방문 → [수집하기] 버튼 클릭
5. 대시보드 `/sourcing/products`에서 수집된 상품 확인
6. 대시보드 `/sourcing/logs`에서 수집 로그 확인
7. 대시보드 `/sourcing/monitoring`에서 모니터링 현황 확인

- [ ] **Step 4: 최종 커밋**

```bash
git add -A
git commit -m "feat: Phase 1 크롬 익스텐션 기반 소싱 시스템 완료

전체 파이프라인:
- 크롬 익스텐션: 무신사 상품 수집 + 모니터링
- FastAPI 백엔드: 명령 큐 + 가격 계산 + 마켓 동기화
- Next.js 대시보드: 수집 설정 + 상품 관리 + 모니터링 + 로그"
```
