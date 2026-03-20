# Naver SEO Auto-fill Skill 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 무신사에서 상품 수집 시 네이버 스마트스토어 SEO 필드(상품명/태그/카테고리/소재 등)를 자동 생성하여 DB에 저장하고, 대시보드 미리보기 + 익스텐션 자동입력까지 완성한다.

**Architecture:** 수집 API(`POST /api/v1/extension/products`) 호출 시 `SeoGeneratorService`가 규칙 기반(카테고리 매핑, 색상, 성별) + Claude API(상품명 최적화, 태그, 소재)로 SEO 데이터를 즉시 생성하여 `product_seo` 테이블에 저장한다. Claude API 실패 시 규칙 기반 fallback으로 항상 완성된 데이터를 보장한다. 대시보드에서 SEO 데이터를 미리보기/수정하고, 익스텐션이 네이버 스마트스토어 등록 페이지에 자동입력한다.

**Tech Stack:** Python FastAPI + SQLModel/SQLAlchemy, Anthropic Python SDK (`anthropic`), TypeScript Chrome Extension MV3, Next.js 15 + Tailwind CSS

---

## 파일 맵

### 생성 파일
| 파일 | 역할 |
|------|------|
| `backend/backend/domain/product/seo_model.py` | ProductSeo SQLModel |
| `backend/backend/domain/product/seo_repository.py` | ProductSeoRepository |
| `backend/backend/domain/product/seo_rules.py` | 카테고리/색상/성별/원산지 규칙 테이블 |
| `backend/backend/domain/product/seo_service.py` | SeoGeneratorService (규칙 + Claude API) |
| `backend/backend/dtos/seo.py` | SeoResponse, SeoUpdateRequest DTO |
| `backend/alembic/versions/20260320_0001_add_product_seo.py` | DB 마이그레이션 |
| `backend/tests/domain/product/test_seo_rules.py` | 규칙 테이블 테스트 |
| `backend/tests/domain/product/test_seo_service.py` | SeoGeneratorService 테스트 |
| `backend/tests/api/test_products_seo_router.py` | SEO 라우터 테스트 |
| `extension/src/content/naver-seo-autofill.ts` | 네이버 DOM 자동입력 |
| `frontend/src/lib/api/seo.ts` | SEO API 클라이언트 |
| `frontend/src/components/sourcing/SeoPreviewModal.tsx` | SEO 미리보기/수정 모달 |

### 수정 파일
| 파일 | 변경 내용 |
|------|-----------|
| `backend/backend/core/config.py` | `anthropic_api_key` 필드 추가 |
| `backend/backend/dtos/extension.py` | `ExtensionProductData`에 `source_category` 추가 |
| `backend/backend/domain/collection/service.py` | SEO 생성 + 저장 로직 추가 |
| `backend/backend/api/v1/routers/products.py` | SEO 조회/수정 엔드포인트 추가 |
| `backend/backend/main.py` | `seo_model` 사전 임포트 추가 |
| `extension/src/shared/types.ts` | `ProductData`에 `source_category` 추가 |
| `extension/src/content/musinsa-product.tsx` | `source_category` 추출 + 전송 |
| `extension/manifest.json` | `smartstore.naver.com` 권한 추가 |
| `frontend/src/types/sourcing.ts` | `ProductSeo` 타입 추가 |
| `frontend/src/components/sourcing/ProductsTable.tsx` | SEO 상태 컬럼 추가 |

---

## Task 1: source_category 필드 전달 (Extension → Backend)

**Files:**
- Modify: `extension/src/shared/types.ts`
- Modify: `extension/src/content/musinsa-product.tsx`
- Modify: `backend/backend/dtos/extension.py`

### 배경
무신사 `__NEXT_DATA__`에는 `categoryInfo.categoryName` 같은 필드가 있다. 이를 수집 시 함께 보내야 SEO 카테고리 매핑이 가능하다. `Product` 모델에는 이미 `source_category` 필드가 있으나, 익스텐션이 이 값을 보내지 않고 있다.

- [ ] **Step 1: types.ts에 source_category 필드 추가**

`extension/src/shared/types.ts`의 `ProductData` 인터페이스에 추가:
```typescript
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
  source_category: string | null  // 추가: 무신사 카테고리명
}
```

- [ ] **Step 2: musinsa-product.tsx에서 카테고리 추출**

`parseFromNextData()` 함수 내 return 객체에 `source_category` 추가:
```typescript
// 카테고리: categoryInfo.categoryName 또는 category 필드
const sourceCategory = String(
  data.categoryInfo?.categoryName
  || data.category?.categoryName
  || data.goodsCategory?.categoryName
  || ""
) || null

return {
  // ... 기존 필드
  source_category: sourceCategory,
}
```

- [ ] **Step 3: extension.py DTO에 source_category 추가**

`backend/backend/dtos/extension.py`의 `ExtensionProductData`에:
```python
source_category: Optional[str] = None
```

- [ ] **Step 4: TypeScript 빌드 확인 (타입 에러 없음)**

```bash
cd extension && npm run build 2>&1 | head -30
```
Expected: 빌드 성공 (에러 없음)

- [ ] **Step 5: 커밋**
```bash
git add extension/src/shared/types.ts extension/src/content/musinsa-product.tsx backend/backend/dtos/extension.py
git commit -m "feat: 수집 시 source_category 필드 전달 (무신사→백엔드)"
```

---

## Task 2: ProductSeo 모델 + DB 마이그레이션

**Files:**
- Create: `backend/backend/domain/product/seo_model.py`
- Create: `backend/alembic/versions/20260320_0001_add_product_seo.py`
- Modify: `backend/backend/main.py`

- [ ] **Step 1: ProductSeo SQLModel 작성**

`backend/backend/domain/product/seo_model.py` 생성:
```python
"""네이버 SEO 데이터 모델."""
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, JSON
from sqlalchemy import Column, String, Text, DateTime, UniqueConstraint


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
```

- [ ] **Step 2: main.py에 seo_model 사전 임포트 추가**

`backend/backend/main.py`에서 다른 domain import 아래에 추가:
```python
import backend.domain.product.seo_model  # noqa: F401
```

- [ ] **Step 3: Alembic 마이그레이션 파일 작성**

`backend/alembic/versions/20260320_0001_add_product_seo.py` 생성:
```python
"""add product_seo table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-20 00:01:00.000000
"""
from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "product_seo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("market_type", sa.String(50), nullable=False, server_default="naver"),
        sa.Column("optimized_name", sa.String(200), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("naver_category_id", sa.String(100), nullable=True),
        sa.Column("brand", sa.String(200), nullable=False),
        sa.Column("material", sa.String(500), nullable=True),
        sa.Column("color", sa.String(200), nullable=True),
        sa.Column("gender", sa.String(50), nullable=True),
        sa.Column("age_group", sa.String(50), nullable=False, server_default="성인"),
        sa.Column("origin", sa.String(100), nullable=False, server_default="해외"),
        sa.Column("status", sa.String(20), nullable=False, server_default="generated"),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "market_type", name="uq_product_market_seo"),
    )
    op.create_index("ix_product_seo_product_id", "product_seo", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_product_seo_product_id", table_name="product_seo")
    op.drop_table("product_seo")
```

- [ ] **Step 4: 마이그레이션 실행**

> `down_revision = "a1b2c3d4e5f6"`은 현재 최신 revision (`backend/alembic/versions/20260319_0000_add_collection_tables.py`)과 일치한다.

```bash
cd backend
# .env가 있고 Docker DB가 실행 중인 상태에서:
alembic upgrade head
```
Expected: `Running upgrade a1b2c3d4e5f6 -> b2c3d4e5f6a7, add product_seo table`

- [ ] **Step 5: 커밋**
```bash
git add backend/backend/domain/product/seo_model.py backend/backend/main.py backend/alembic/versions/20260320_0001_add_product_seo.py
git commit -m "feat: ProductSeo 모델 + product_seo DB 마이그레이션"
```

---

## Task 3: SEO 규칙 테이블 (seo_rules.py)

**Files:**
- Create: `backend/backend/domain/product/seo_rules.py`
- Create: `backend/tests/domain/product/test_seo_rules.py`

패션 상품에 특화된 규칙 테이블. 카테고리 매핑, 색상 키워드, 성별 키워드, 원산지 규칙을 정의한다.

- [ ] **Step 1: 테스트 먼저 작성**

`backend/tests/domain/product/test_seo_rules.py` 생성:
```python
"""SEO 규칙 테이블 테스트."""
import pytest
from backend.domain.product.seo_rules import (
    get_naver_category_id,
    extract_color,
    infer_gender,
    infer_origin,
    get_material_default,
)


def test_category_mapping_sneakers():
    """스니커즈 카테고리 매핑"""
    result = get_naver_category_id("스니커즈")
    assert result == "50000803"


def test_category_mapping_unknown_returns_none():
    """알 수 없는 카테고리는 None 반환"""
    result = get_naver_category_id("없는카테고리")
    assert result is None


def test_extract_color_white():
    """상품명에서 화이트 추출"""
    result = extract_color("나이키 에어맥스 화이트 / BQ1234")
    assert result == "화이트"


def test_extract_color_multiple_returns_first():
    """여러 색상 있으면 첫 번째 반환"""
    result = extract_color("나이키 블랙 화이트")
    assert result == "블랙"


def test_extract_color_none_when_no_match():
    """색상 키워드 없으면 None"""
    result = extract_color("나이키 에어맥스 90")
    assert result is None


def test_infer_gender_unisex():
    """기본값은 남녀공용"""
    result = infer_gender("나이키", "에어맥스 90")
    assert result == "남녀공용"


def test_infer_origin_global_brand():
    """나이키는 해외"""
    result = infer_origin("NIKE")
    assert result == "해외"


def test_get_material_default_shoes():
    """신발 기본 소재"""
    result = get_material_default("스니커즈")
    assert result == "합성섬유/합성피혁"


def test_get_material_default_clothing():
    """의류 기본 소재"""
    result = get_material_default("반소매 티셔츠")
    assert result == "면혼합"
```

- [ ] **Step 2: 테스트 실행 (실패 확인)**
```bash
cd backend && python -m pytest tests/domain/product/test_seo_rules.py -v 2>&1 | tail -20
```
Expected: `ImportError` 또는 `ModuleNotFoundError`

- [ ] **Step 3: seo_rules.py 구현**

`backend/backend/domain/product/seo_rules.py` 생성:
```python
"""네이버 SEO 패션 특화 규칙 테이블."""
from typing import Optional

# 무신사 카테고리명 → 네이버 카테고리 ID
MUSINSA_TO_NAVER_CATEGORY: dict[str, str] = {
    "스니커즈": "50000803",
    "슬립온": "50000803",
    "로퍼": "50000795",
    "보트슈즈": "50000795",
    "샌들": "50000801",
    "슬리퍼": "50000801",
    "부츠": "50000797",
    "워커": "50000797",
    "반소매 티셔츠": "50000000",
    "긴소매 티셔츠": "50000000",
    "맨투맨": "50000001",
    "스웨트셔츠": "50000001",
    "후드 티셔츠": "50000002",
    "후디": "50000002",
    "니트": "50000003",
    "스웨터": "50000003",
    "바지": "50000100",
    "팬츠": "50000100",
    "반바지": "50000101",
    "숏팬츠": "50000101",
    "모자": "50000200",
    "캡": "50000200",
    "비니": "50000200",
    "가방": "50000300",
    "백팩": "50000300",
    "토트백": "50000300",
    "양말": "50000400",
    "레깅스": "50000400",
}

# 색상 키워드 (우선순위 순)
COLOR_KEYWORDS: list[str] = [
    "블랙", "화이트", "네이비", "그레이", "베이지", "브라운",
    "레드", "블루", "그린", "옐로우", "핑크", "퍼플", "오렌지",
    "아이보리", "카키", "와인", "민트", "코랄", "라벤더",
    "BLACK", "WHITE", "NAVY", "GRAY", "GREY", "BEIGE", "BROWN",
]

# 국내 브랜드 키워드 (소문자 포함 판단)
DOMESTIC_BRAND_KEYWORDS: list[str] = [
    "MLB", "디스이즈네버댓", "커버낫", "더콰이엇", "아크메드라비",
    "마하그리드", "플리츠마마", "뮬라웨어", "뉴발란스코리아",
]

# 카테고리별 기본 소재
CATEGORY_DEFAULT_MATERIAL: dict[str, str] = {
    "스니커즈": "합성섬유/합성피혁",
    "슬립온": "합성섬유/합성피혁",
    "로퍼": "합성피혁",
    "부츠": "합성피혁",
    "워커": "합성피혁",
    "샌들": "합성소재",
    "슬리퍼": "합성소재",
    "반소매 티셔츠": "면혼합",
    "긴소매 티셔츠": "면혼합",
    "맨투맨": "면폴리혼합",
    "후드 티셔츠": "면폴리혼합",
    "니트": "아크릴혼합",
    "바지": "면폴리혼합",
    "반바지": "면폴리혼합",
    "모자": "면폴리혼합",
    "가방": "합성섬유",
    "양말": "면혼합",
}


def get_naver_category_id(source_category: str) -> Optional[str]:
    """무신사 카테고리명 → 네이버 카테고리 ID"""
    if not source_category:
        return None
    # 정확히 일치하는 것 먼저 시도
    if source_category in MUSINSA_TO_NAVER_CATEGORY:
        return MUSINSA_TO_NAVER_CATEGORY[source_category]
    # 부분 일치
    for key, value in MUSINSA_TO_NAVER_CATEGORY.items():
        if key in source_category or source_category in key:
            return value
    return None


def extract_color(product_name: str) -> Optional[str]:
    """상품명에서 첫 번째 색상 키워드 추출"""
    upper_name = product_name.upper()
    for color in COLOR_KEYWORDS:
        if color.upper() in upper_name:
            return color if not color.isupper() else color.capitalize()
    return None


def infer_gender(brand: str, product_name: str) -> str:
    """브랜드/상품명에서 성별 추론 (기본값: 남녀공용)"""
    combined = f"{brand} {product_name}".upper()
    if "우먼" in combined or "WOMEN" in combined or "레이디" in combined:
        return "여성"
    if "맨즈" in combined or "MEN'S" in combined or "MENS" in combined:
        return "남성"
    return "남녀공용"


def infer_origin(brand: str) -> str:
    """브랜드명으로 원산지 추론 (기본값: 해외)"""
    if any(domestic in brand.upper() for domestic in [b.upper() for b in DOMESTIC_BRAND_KEYWORDS]):
        return "국내"
    return "해외"


def get_material_default(source_category: str) -> str:
    """카테고리별 기본 소재 반환"""
    if not source_category:
        return "혼합소재"
    for key, material in CATEGORY_DEFAULT_MATERIAL.items():
        if key in source_category:
            return material
    return "혼합소재"
```

- [ ] **Step 4: 테스트 통과 확인**
```bash
cd backend && python -m pytest tests/domain/product/test_seo_rules.py -v 2>&1 | tail -20
```
Expected: 모든 테스트 PASS

- [ ] **Step 5: 커밋**
```bash
git add backend/backend/domain/product/seo_rules.py backend/tests/domain/product/test_seo_rules.py
git commit -m "feat: SEO 패션 특화 규칙 테이블 (카테고리/색상/성별/원산지)"
```

---

## Task 4: SeoGeneratorService (규칙 + Claude API + Fallback)

**Files:**
- Create: `backend/backend/domain/product/seo_service.py`
- Create: `backend/tests/domain/product/test_seo_service.py`
- Modify: `backend/backend/core/config.py`

- [ ] **Step 1: config.py에 anthropic_api_key 추가**

`backend/backend/core/config.py`의 `BackendSettings` 클래스에 추가:
```python
# ===========================================
# AI Configuration
# ===========================================
anthropic_api_key: Optional[str] = None
"""Claude API 키 (SEO 생성용). None이면 규칙 기반 fallback만 사용."""
anthropic_model: str = "claude-haiku-4-5-20251001"
"""사용할 Claude 모델 ID"""
```
파일 상단 import에 `Optional` 추가: `from typing import Literal, Optional`

- [ ] **Step 2: anthropic 패키지 설치 확인**
```bash
cd backend && python -c "import anthropic; print(anthropic.__version__)"
```
없으면:
```bash
uv pip install anthropic
```

- [ ] **Step 3: 테스트 먼저 작성**

`backend/tests/domain/product/test_seo_service.py` 생성:
```python
"""SeoGeneratorService 테스트 (Claude API mock 사용)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def make_product_data(
    name="나이키 에어맥스 97 화이트 / BQ1234-100",
    brand_name="NIKE",
    source_category="스니커즈",
    original_price=139000,
):
    """테스트용 ExtensionProductData mock"""
    data = MagicMock()
    data.name = name
    data.brand_name = brand_name
    data.source_category = source_category
    data.original_price = original_price
    return data


@pytest.mark.asyncio
async def test_generate_uses_rules_for_color():
    """색상 추출은 규칙 기반"""
    from backend.domain.product.seo_service import SeoGeneratorService

    service = SeoGeneratorService(api_key=None)  # fallback 모드
    result = await service.generate(
        product_data=make_product_data(name="나이키 에어맥스 화이트"),
        product_id=1,
    )
    assert result["color"] == "화이트"


@pytest.mark.asyncio
async def test_generate_fallback_when_no_api_key():
    """API 키 없으면 규칙 기반 fallback"""
    from backend.domain.product.seo_service import SeoGeneratorService

    service = SeoGeneratorService(api_key=None)
    result = await service.generate(
        product_data=make_product_data(),
        product_id=1,
    )
    # fallback이어도 모든 필드가 채워져야 함
    assert result["optimized_name"]
    assert len(result["tags"]) > 0
    assert result["brand"] == "NIKE"
    assert result["status"] == "fallback"


@pytest.mark.asyncio
async def test_generate_fallback_on_api_error():
    """Claude API 에러 시 fallback"""
    from backend.domain.product.seo_service import SeoGeneratorService

    service = SeoGeneratorService(api_key="fake-key")

    with patch.object(service, "_call_claude_api", new_callable=AsyncMock) as mock_api:
        mock_api.side_effect = Exception("API Error")
        result = await service.generate(
            product_data=make_product_data(),
            product_id=1,
        )

    assert result["status"] == "fallback"
    assert result["optimized_name"]  # 빈 칸 없음


@pytest.mark.asyncio
async def test_generate_with_claude_success():
    """Claude API 성공 시 generated 상태"""
    from backend.domain.product.seo_service import SeoGeneratorService

    service = SeoGeneratorService(api_key="fake-key")

    claude_result = {
        "optimized_name": "나이키 에어맥스 97 화이트 운동화",
        "tags": ["나이키", "에어맥스", "화이트스니커즈"],
        "material": "메쉬/합성피혁",
    }

    with patch.object(service, "_call_claude_api", new_callable=AsyncMock) as mock_api:
        mock_api.return_value = claude_result
        result = await service.generate(
            product_data=make_product_data(),
            product_id=1,
        )

    assert result["optimized_name"] == "나이키 에어맥스 97 화이트 운동화"
    assert result["material"] == "메쉬/합성피혁"
    assert result["status"] == "generated"


@pytest.mark.asyncio
async def test_generate_category_mapped():
    """스니커즈 카테고리가 네이버 ID로 매핑됨"""
    from backend.domain.product.seo_service import SeoGeneratorService

    service = SeoGeneratorService(api_key=None)
    result = await service.generate(
        product_data=make_product_data(source_category="스니커즈"),
        product_id=1,
    )
    assert result["naver_category_id"] == "50000803"


@pytest.mark.asyncio
async def test_generate_no_empty_fields():
    """모든 필드가 채워져 있어야 함 (빈 칸 없음)"""
    from backend.domain.product.seo_service import SeoGeneratorService

    service = SeoGeneratorService(api_key=None)
    result = await service.generate(
        product_data=make_product_data(),
        product_id=1,
    )
    assert result["optimized_name"]
    assert result["brand"]
    assert result["age_group"]
    assert result["origin"]
    assert result["gender"]
```

- [ ] **Step 4: 테스트 실행 (실패 확인)**
```bash
cd backend && python -m pytest tests/domain/product/test_seo_service.py -v 2>&1 | tail -20
```
Expected: `ImportError` (파일 없음)

- [ ] **Step 5: SeoGeneratorService 구현**

`backend/backend/domain/product/seo_service.py` 생성:
```python
"""SEO 자동 생성 서비스 (규칙 기반 + Claude API)."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

from backend.domain.product.seo_rules import (
    extract_color,
    get_material_default,
    get_naver_category_id,
    infer_gender,
    infer_origin,
)
from backend.services.seo_generator import SeoGenerator  # 기존 규칙 기반 태그 생성기 (backend/services/seo_generator.py에 존재)

if TYPE_CHECKING:
    from backend.dtos.extension import ExtensionProductData

logger = logging.getLogger(__name__)


class SeoGeneratorService:
    """규칙 기반 + Claude API 하이브리드 SEO 생성 서비스"""

    def __init__(self, api_key: Optional[str], model: str = "claude-haiku-4-5-20251001"):
        self.api_key = api_key
        self.model = model
        self._rule_generator = SeoGenerator()

    async def generate(
        self,
        product_data: "ExtensionProductData",
        product_id: int,
        market_type: str = "naver",
    ) -> Dict[str, Any]:
        """
        SEO 데이터 생성.

        1. 규칙 기반으로 즉시 처리 가능한 필드 생성
        2. Claude API로 상품명 최적화, 태그, 소재 생성 (api_key 있을 때)
        3. Claude 실패 시 규칙 기반 fallback

        Returns:
            product_seo 테이블에 저장할 데이터 dict
        """
        brand = product_data.brand_name or ""
        name = product_data.name or ""
        source_category = getattr(product_data, "source_category", None) or ""

        # 규칙 기반 필드 (항상 실행)
        color = extract_color(name)
        gender = infer_gender(brand, name)
        origin = infer_origin(brand)
        naver_category_id = get_naver_category_id(source_category)
        material_default = get_material_default(source_category)

        # 태그 fallback (규칙 기반)
        fallback_tags = self._rule_generator.generate_tags(
            brand=brand,
            category=source_category,
            product_name=name,
            max_tags=10,
        )
        # 이름 fallback
        fallback_name = name[:100] if name else f"{brand} {source_category}".strip()

        # Claude API 시도
        claude_result = None
        if self.api_key:
            try:
                claude_result = await asyncio.wait_for(
                    self._call_claude_api(
                        name=name,
                        brand=brand,
                        source_category=source_category,
                        original_price=product_data.original_price,
                    ),
                    timeout=5.0,
                )
            except Exception as e:
                logger.warning(f"[SEO] Claude API 실패 (product_id={product_id}): {e}")

        status = "generated" if claude_result else "fallback"

        return {
            "product_id": product_id,
            "market_type": market_type,
            "optimized_name": (claude_result or {}).get("optimized_name") or fallback_name,
            "tags": (claude_result or {}).get("tags") or fallback_tags,
            "naver_category_id": naver_category_id,
            "brand": brand,
            "material": (claude_result or {}).get("material") or material_default,
            "color": color,
            "gender": gender,
            "age_group": "성인",
            "origin": origin,
            "status": status,
        }

    async def _call_claude_api(
        self,
        name: str,
        brand: str,
        source_category: str,
        original_price: int,
    ) -> Dict[str, Any]:
        """Claude API 호출하여 SEO 필드 생성"""
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        prompt = f"""네이버 스마트스토어 SEO 최적화 전문가로서 아래 패션 상품의 SEO 데이터를 JSON으로 생성해주세요.

상품 정보:
- 원본 상품명: {name}
- 브랜드: {brand}
- 카테고리: {source_category}
- 가격: {original_price}원

규칙:
1. optimized_name: 100자 이하, 핵심 키워드(브랜드+카테고리+색상+품번) 앞에 배치
2. tags: 검색량 높은 키워드 10개 이하, 각 15자 이하, 브랜드/스타일/색상/소재 포함
3. material: 실제 소재 추론 (예: "메쉬/합성피혁", "면100%")

반드시 JSON만 반환 (다른 텍스트 없이):
{{"optimized_name": "...", "tags": ["...", ...], "material": "..."}}"""

        message = await client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        # JSON 파싱
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
```

- [ ] **Step 6: 테스트 통과 확인**
```bash
cd backend && python -m pytest tests/domain/product/test_seo_service.py -v 2>&1 | tail -30
```
Expected: 모든 테스트 PASS

- [ ] **Step 7: 커밋**
```bash
git add backend/backend/core/config.py backend/backend/domain/product/seo_service.py backend/tests/domain/product/test_seo_service.py
git commit -m "feat: SeoGeneratorService — Claude API + 규칙 기반 fallback"
```

---

## Task 5: ProductSeoRepository

**Files:**
- Create: `backend/backend/domain/product/seo_repository.py`

- [ ] **Step 1: seo_repository.py 작성**

`backend/backend/domain/product/seo_repository.py` 생성:
```python
"""ProductSeo 리포지토리."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.domain.product.seo_model import ProductSeo
from backend.domain.shared.base_repository import BaseRepository


class ProductSeoRepository(BaseRepository[ProductSeo]):
    """ProductSeo CRUD"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ProductSeo)

    async def find_by_product_id(
        self,
        product_id: int,
        market_type: str = "naver",
    ) -> Optional[ProductSeo]:
        """product_id + market_type으로 SEO 데이터 조회"""
        stmt = select(ProductSeo).where(
            ProductSeo.product_id == product_id,
            ProductSeo.market_type == market_type,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
```

- [ ] **Step 2: 커밋**
```bash
git add backend/backend/domain/product/seo_repository.py
git commit -m "feat: ProductSeoRepository 추가"
```

---

## Task 6: 수집 API에 SEO 생성 통합

**Files:**
- Modify: `backend/backend/domain/collection/service.py`
- Modify: `backend/backend/api/v1/routers/extension.py`
- Modify: `backend/backend/dtos/seo.py` (신규)

- [ ] **Step 1: SeoResponse DTO 작성**

`backend/backend/dtos/seo.py` 생성:
```python
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
```

- [ ] **Step 2: CollectionService에 SEO 생성 통합**

`backend/backend/domain/collection/service.py` 수정:

파일 상단 import 추가:
```python
from backend.domain.product.seo_service import SeoGeneratorService
from backend.domain.product.seo_repository import ProductSeoRepository
from backend.core.config import settings
```

`CollectionService.__init__` 수정:
```python
def __init__(self, session: AsyncSession):
    self.session = session
    self.setting_repo = CollectionSettingRepository(session)
    self.log_repo = CollectionLogRepository(session)
    self.product_service = ProductService(session)
    self.brand_repo = BrandRepository(session)
    self.price_calculator = PriceCalculator()
    self.seo_generator = SeoGenerator()
    self.seo_service = SeoGeneratorService(api_key=settings.anthropic_api_key)
    self.seo_repo = ProductSeoRepository(session)
```

`process_collected_product()` 내 `# 4. SeoGenerator로 태그 생성` 부분을 교체:
```python
        # 4. SEO 데이터 생성 + 저장
        try:
            seo_data = await self.seo_service.generate(
                product_data=product_data,
                product_id=product.id,
            )
            await self.seo_repo.create_async(**seo_data)
            logger.info(f"SEO 생성 완료 (product_id={product.id}, status={seo_data['status']})")
        except Exception as e:
            logger.warning(f"SEO 생성 실패 (product_id={product.id}): {e}")
```

- [ ] **Step 3: extension router 응답에 seo_id 포함**

`backend/backend/api/v1/routers/extension.py`의 `receive_collected_product` 응답 수정:
```python
    response: dict = {"status": "ok", "product_id": product.id}
    if result.get("ip_warning"):
        response["warning"] = result["ip_warning"]
    return response
```
→ 변경 없음 (seo 데이터는 별도 GET 엔드포인트로 조회)

- [ ] **Step 4: 백엔드 서버 재시작 후 수집 테스트**

```bash
cd backend && uvicorn backend.main:app --reload --port 28080
```
무신사 상품 페이지에서 수집 시 서버 로그 확인:
Expected 로그: `SEO 생성 완료 (product_id=X, status=fallback)` (API 키 없을 때)

- [ ] **Step 5: 커밋**
```bash
git add backend/backend/dtos/seo.py backend/backend/domain/collection/service.py
git commit -m "feat: 수집 시 SEO 자동 생성 + product_seo 저장"
```

---

## Task 7: SEO 조회/수정 API 엔드포인트

**Files:**
- Modify: `backend/backend/api/v1/routers/products.py`
- Create: `backend/tests/api/test_products_seo_router.py`

- [ ] **Step 1: 테스트 먼저 작성**

`backend/tests/api/test_products_seo_router.py` 생성:
```python
"""상품 SEO 라우터 테스트."""
import sys
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# DB/settings mock
_mock_orm = MagicMock()
_mock_orm.get_read_session_dependency = MagicMock(return_value=AsyncMock())
_mock_orm.get_write_session_dependency = MagicMock(return_value=AsyncMock())
if "backend.db.orm" not in sys.modules:
    sys.modules["backend.db.orm"] = _mock_orm


def test_products_router_has_seo_get():
    """GET /products/{id}/seo 라우트 존재 확인"""
    from backend.api.v1.routers.products import router
    paths = [r.path for r in router.routes]
    assert "/{product_id}/seo" in paths


def test_products_router_has_seo_patch():
    """PATCH /products/{id}/seo 라우트 존재 확인"""
    from backend.api.v1.routers.products import router
    routes = {r.path: r.methods for r in router.routes if hasattr(r, "methods")}
    assert "PATCH" in routes.get("/{product_id}/seo", set())
```

- [ ] **Step 2: 테스트 실행 (실패 확인)**
```bash
cd backend && python -m pytest tests/api/test_products_seo_router.py -v 2>&1 | tail -10
```
Expected: AssertionError (라우트 없음)

- [ ] **Step 3: products.py에 SEO 엔드포인트 추가**

`backend/backend/api/v1/routers/products.py` 파일 끝에 추가:
```python
from backend.db.orm import get_read_session_dependency, get_write_session_dependency
from backend.domain.product.seo_repository import ProductSeoRepository
from backend.dtos.seo import SeoUpdateRequest
from datetime import datetime, timezone

@router.get("/{product_id}/seo")
async def get_product_seo(
    product_id: int,
    market_type: str = Query(default="naver"),
    session: AsyncSession = Depends(get_read_session_dependency),
):
    """상품 SEO 데이터 조회"""
    repo = ProductSeoRepository(session)
    seo = await repo.find_by_product_id(product_id, market_type)
    if not seo:
        raise HTTPException(status_code=404, detail="SEO 데이터가 없습니다")
    return {
        "id": seo.id,
        "product_id": seo.product_id,
        "market_type": seo.market_type,
        "optimized_name": seo.optimized_name,
        "tags": seo.tags,
        "naver_category_id": seo.naver_category_id,
        "brand": seo.brand,
        "material": seo.material,
        "color": seo.color,
        "gender": seo.gender,
        "age_group": seo.age_group,
        "origin": seo.origin,
        "status": seo.status,
        "generated_at": seo.generated_at.isoformat() if seo.generated_at else None,
        "edited_at": seo.edited_at.isoformat() if seo.edited_at else None,
    }


@router.patch("/{product_id}/seo")
async def update_product_seo(
    product_id: int,
    data: SeoUpdateRequest,
    market_type: str = Query(default="naver"),
    session: AsyncSession = Depends(get_write_session_dependency),
):
    """상품 SEO 데이터 수정 (대시보드에서 편집 시)"""
    repo = ProductSeoRepository(session)
    seo = await repo.find_by_product_id(product_id, market_type)
    if not seo:
        raise HTTPException(status_code=404, detail="SEO 데이터가 없습니다")

    update_fields = data.model_dump(exclude_unset=True)
    update_fields["status"] = "edited"
    update_fields["edited_at"] = datetime.now(tz=timezone.utc)

    updated = await repo.update_async(seo.id, **update_fields)
    return {"status": "ok", "seo_id": updated.id}
```

- [ ] **Step 4: import 정리** (products.py 상단에 추가 import 확인)
```python
from backend.db.orm import get_read_session_dependency, get_write_session_dependency
```

- [ ] **Step 5: 테스트 통과 확인**
```bash
cd backend && python -m pytest tests/api/test_products_seo_router.py -v 2>&1 | tail -10
```
Expected: 모든 테스트 PASS

- [ ] **Step 6: 커밋**
```bash
git add backend/backend/api/v1/routers/products.py backend/tests/api/test_products_seo_router.py
git commit -m "feat: GET/PATCH /api/v1/products/{id}/seo 엔드포인트 추가"
```

---

## Task 8: 프론트엔드 SEO 미리보기/수정

**Files:**
- Modify: `frontend/src/types/sourcing.ts`
- Create: `frontend/src/lib/api/seo.ts`
- Create: `frontend/src/components/sourcing/SeoPreviewModal.tsx`
- Modify: `frontend/src/components/sourcing/ProductsTable.tsx`

- [ ] **Step 1: sourcing.ts에 SEO 타입 추가**

`frontend/src/types/sourcing.ts`에 추가:
```typescript
/** 상품 SEO 데이터 */
export interface ProductSeo {
  id: number
  product_id: number
  market_type: string
  optimized_name: string
  tags: string[] | null
  naver_category_id: string | null
  brand: string
  material: string | null
  color: string | null
  gender: string | null
  age_group: string
  origin: string
  status: "generated" | "edited" | "fallback" | "failed"
  generated_at: string
  edited_at: string | null
}

/** SEO 수정 폼 */
export interface SeoUpdateForm {
  optimized_name?: string
  tags?: string[]
  material?: string
  color?: string
  gender?: string
  age_group?: string
  origin?: string
}
```

- [ ] **Step 2: SEO API 클라이언트 작성**

`frontend/src/lib/api/seo.ts` 생성:
```typescript
import type { ProductSeo, SeoUpdateForm } from "@/types/sourcing"

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:28080"

export async function getSeoData(
  productId: number,
  marketType = "naver"
): Promise<ProductSeo | null> {
  const res = await fetch(
    `${BASE_URL}/api/v1/products/${productId}/seo?market_type=${marketType}`,
    { cache: "no-store" }
  )
  if (res.status === 404) return null
  if (!res.ok) throw new Error(`SEO 조회 실패: ${res.status}`)
  return res.json()
}

export async function updateSeoData(
  productId: number,
  data: SeoUpdateForm,
  marketType = "naver"
): Promise<void> {
  const res = await fetch(
    `${BASE_URL}/api/v1/products/${productId}/seo?market_type=${marketType}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }
  )
  if (!res.ok) throw new Error(`SEO 수정 실패: ${res.status}`)
}
```

- [ ] **Step 3: SeoPreviewModal 컴포넌트 작성**

`frontend/src/components/sourcing/SeoPreviewModal.tsx` 생성:
```typescript
"use client"

import { useState } from "react"
import type { ProductSeo, SeoUpdateForm } from "@/types/sourcing"
import { updateSeoData } from "@/lib/api/seo"

interface Props {
  productId: number
  seo: ProductSeo
  onClose: () => void
  onSaved: () => void
}

/** SEO 상태 뱃지 */
function SeoStatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    generated: { label: "AI 생성", cls: "bg-blue-100 text-blue-700" },
    edited: { label: "수동 수정", cls: "bg-purple-100 text-purple-700" },
    fallback: { label: "규칙 생성", cls: "bg-yellow-100 text-yellow-700" },
    failed: { label: "생성 실패", cls: "bg-red-100 text-red-700" },
  }
  const style = map[status] ?? { label: status, cls: "bg-gray-100 text-gray-500" }
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${style.cls}`}>
      {style.label}
    </span>
  )
}

/** SEO 미리보기/수정 모달 */
export function SeoPreviewModal({ productId, seo, onClose, onSaved }: Props) {
  const [form, setForm] = useState<SeoUpdateForm>({
    optimized_name: seo.optimized_name,
    tags: seo.tags ?? [],
    material: seo.material ?? "",
    color: seo.color ?? "",
    gender: seo.gender ?? "남녀공용",
    age_group: seo.age_group,
    origin: seo.origin,
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      await updateSeoData(productId, form)
      onSaved()
    } catch (e) {
      setError(e instanceof Error ? e.message : "저장 실패")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-lg rounded-xl bg-white shadow-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">SEO 미리보기/수정</h2>
          <SeoStatusBadge status={seo.status} />
        </div>

        <div className="space-y-3">
          {/* 최적화 상품명 */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              최적화 상품명 (100자 이하)
            </label>
            <input
              type="text"
              maxLength={100}
              value={form.optimized_name ?? ""}
              onChange={(e) => setForm({ ...form, optimized_name: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
            <span className="text-xs text-gray-400">{form.optimized_name?.length ?? 0}/100자</span>
          </div>

          {/* 태그 */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              검색 태그 (쉼표로 구분, 최대 10개)
            </label>
            <input
              type="text"
              value={(form.tags ?? []).join(", ")}
              onChange={(e) =>
                setForm({
                  ...form,
                  tags: e.target.value.split(",").map((t) => t.trim()).filter(Boolean).slice(0, 10),
                })
              }
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </div>

          {/* 소재 / 색상 / 성별 / 원산지 */}
          <div className="grid grid-cols-2 gap-3">
            {(
              [
                { key: "material", label: "소재" },
                { key: "color", label: "색상" },
                { key: "gender", label: "성별" },
                { key: "origin", label: "원산지" },
              ] as const
            ).map(({ key, label }) => (
              <div key={key}>
                <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
                <input
                  type="text"
                  value={(form[key] as string) ?? ""}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
            ))}
          </div>
        </div>

        {error && <p className="mt-3 text-sm text-red-500">{error}</p>}

        <div className="mt-5 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            취소
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "저장 중..." : "저장"}
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: ProductsTable에 SEO 컬럼 추가**

`frontend/src/components/sourcing/ProductsTable.tsx` 수정:

1. import 추가:
```typescript
import { useState, useCallback } from "react"
import type { ProductSeo } from "@/types/sourcing"
import { getSeoData } from "@/lib/api/seo"
import { SeoPreviewModal } from "./SeoPreviewModal"
```

2. `SourcingProduct` 타입에 `seo?: ProductSeo` 추가 (인터페이스 확장 없이 컴포넌트 내에서 상태로 관리)

3. `ProductsTable` 컴포넌트 내에 SEO 모달 상태 추가:
```typescript
const [seoModal, setSeoModal] = useState<{ productId: number; seo: ProductSeo } | null>(null)

const openSeoModal = useCallback(async (productId: number) => {
  const seo = await getSeoData(productId)
  if (seo) setSeoModal({ productId, seo })
}, [])
```

4. 테이블 헤더에 "SEO" 컬럼 추가:
```tsx
<th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
  SEO
</th>
```

5. 테이블 바디 행에 SEO 버튼 추가:
```tsx
<td className="px-4 py-3 whitespace-nowrap">
  <button
    onClick={() => void openSeoModal(product.id)}
    className="inline-flex items-center rounded px-2 py-1 text-xs font-medium bg-indigo-50 text-indigo-700 hover:bg-indigo-100"
  >
    SEO 보기
  </button>
</td>
```

6. 컴포넌트 반환 값에 모달 추가:
```tsx
{seoModal && (
  <SeoPreviewModal
    productId={seoModal.productId}
    seo={seoModal.seo}
    onClose={() => setSeoModal(null)}
    onSaved={() => setSeoModal(null)}
  />
)}
```

- [ ] **Step 5: TypeScript 빌드 확인**
```bash
cd frontend && npm run build 2>&1 | grep -E "Error|error" | head -20
```
Expected: 에러 없음

- [ ] **Step 6: 커밋**
```bash
git add frontend/src/types/sourcing.ts frontend/src/lib/api/seo.ts frontend/src/components/sourcing/SeoPreviewModal.tsx frontend/src/components/sourcing/ProductsTable.tsx
git commit -m "feat: 대시보드 SEO 미리보기/수정 UI"
```

---

## Task 9: Extension — 네이버 스마트스토어 자동입력

**Files:**
- Create: `extension/src/content/naver-seo-autofill.ts`
- Modify: `extension/manifest.json`
- Modify: `extension/src/background/index.ts`
- Modify: `extension/src/background/api-client.ts`

### 배경
네이버 스마트스토어 상품 등록 페이지(`smartstore.naver.com/...`)에서 SEO 데이터를 자동입력한다. 백그라운드 SW가 수집된 상품의 `product_id`를 저장했다가, 자동입력 명령 수신 시 Content Script에 전달한다.

- [ ] **Step 1: manifest.json에 네이버 권한 추가**

`extension/manifest.json`의 `host_permissions`에 추가:
```json
"https://sell.smartstore.naver.com/*"
```
그리고 `content_scripts`에 추가:
```json
{
  "matches": ["https://sell.smartstore.naver.com/*"],
  "js": ["src/content/naver-seo-autofill.ts"],
  "run_at": "document_idle"
}
```

- [ ] **Step 2: api-client.ts에 SEO 조회 함수 추가**

`extension/src/background/api-client.ts`에 추가:
```typescript
/** product_id로 SEO 데이터 조회 */
export async function fetchProductSeo(productId: number): Promise<Record<string, unknown> | null> {
  const BASE_URL = "http://localhost:28080"
  const EXTENSION_KEY = "sourcing-extension-phase1-key"
  try {
    const res = await fetch(`${BASE_URL}/api/v1/products/${productId}/seo`, {
      headers: { "X-Extension-Key": EXTENSION_KEY },
    })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}
```

- [ ] **Step 3: shared/types.ts에 메시지 타입 추가**

`extension/src/shared/types.ts`에 추가:
```typescript
/** Background → Content Script 메시지 (확장) */
export type BackgroundMessage =
  | { type: "PRODUCT_DATA_READY"; data: ProductData }
  | { type: "SEO_AUTOFILL"; seoData: Record<string, unknown> }
```

- [ ] **Step 4: naver-seo-autofill.ts 작성**

`extension/src/content/naver-seo-autofill.ts` 생성:
```typescript
/**
 * 네이버 스마트스토어 상품 등록 페이지 SEO 자동입력
 *
 * 흐름:
 * 1. 페이지 로드 시 Background SW에 준비 알림
 * 2. Background SW가 SEO_AUTOFILL 메시지 전달
 * 3. DOM 필드에 SEO 데이터 자동입력
 */

interface SeoData {
  optimized_name?: string
  tags?: string[]
  material?: string
  color?: string
  gender?: string
  age_group?: string
  origin?: string
}

/** input/textarea에 값 설정 (React 상태 업데이트 트리거 포함) */
function setInputValue(el: HTMLInputElement | HTMLTextAreaElement, value: string): void {
  const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
    el.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype,
    "value"
  )?.set
  nativeInputValueSetter?.call(el, value)
  el.dispatchEvent(new Event("input", { bubbles: true }))
  el.dispatchEvent(new Event("change", { bubbles: true }))
}

/** SEO 데이터를 네이버 등록 폼에 자동입력 */
function autofillSeoData(seoData: SeoData): void {
  // 상품명 (id="goodsName" 또는 name="goodsName")
  const nameEl = document.querySelector<HTMLInputElement>(
    'input[id="goodsName"], input[name="goodsName"]'
  )
  if (nameEl && seoData.optimized_name) {
    setInputValue(nameEl, seoData.optimized_name)
  }

  // 태그 (textarea 또는 input)
  const tagEl = document.querySelector<HTMLTextAreaElement | HTMLInputElement>(
    'textarea[id*="tag"], input[id*="tag"], textarea[placeholder*="태그"]'
  )
  if (tagEl && seoData.tags?.length) {
    setInputValue(tagEl, seoData.tags.join(" "))
  }

  console.info("[소싱 어시스턴트] SEO 자동입력 완료:", {
    name: seoData.optimized_name,
    tags: seoData.tags,
  })
}

/** Background SW 메시지 수신 */
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "SEO_AUTOFILL") {
    autofillSeoData(message.seoData as SeoData)
    sendResponse({ success: true })
  }
})

// 페이지 로드 알림 (Background SW에서 상품 매칭에 활용)
chrome.runtime.sendMessage({ type: "NAVER_REGISTER_PAGE_LOADED" })
```

- [ ] **Step 5: 빌드 확인**
```bash
cd extension && npm run build 2>&1 | tail -20
```
Expected: 빌드 성공

- [ ] **Step 6: 커밋**
```bash
git add extension/src/content/naver-seo-autofill.ts extension/manifest.json extension/src/background/api-client.ts extension/src/shared/types.ts
git commit -m "feat: 네이버 스마트스토어 SEO 자동입력 스크립트 + manifest 권한 추가"
```

---

## Task 10: .env에 anthropic_api_key 추가 + E2E 테스트

**Files:**
- Modify: `backend/.env`

- [ ] **Step 1: .env에 Claude API 키 추가**

`backend/.env`에 추가:
```
ANTHROPIC_API_KEY=your-actual-api-key-here
```

- [ ] **Step 2: 백엔드 재시작**
```bash
cd backend && uvicorn backend.main:app --reload --port 28080
```

- [ ] **Step 3: 무신사에서 수집 테스트**

1. Chrome 익스텐션 새로고침
2. 무신사 상품 페이지 접속 (예: `https://www.musinsa.com/products/12345`)
3. [수집하기] 클릭
4. 서버 로그 확인: `SEO 생성 완료 (product_id=X, status=generated)`

- [ ] **Step 4: 대시보드에서 SEO 확인**

1. `http://localhost:3001/sourcing/products` 접속
2. 수집된 상품 행에서 [SEO 보기] 버튼 클릭
3. SEO 미리보기 모달 확인 (상품명, 태그, 소재 등이 채워져 있어야 함)

- [ ] **Step 5: 전체 테스트 실행**
```bash
cd backend && python -m pytest tests/ -v --tb=short 2>&1 | tail -30
```
Expected: 모든 테스트 PASS

- [ ] **Step 6: 최종 커밋**
```bash
git add -A
git commit -m "chore: E2E 검증 완료 — Naver SEO Auto-fill Skill Phase 1"
```

---

## 테스트 실행 명령 요약

```bash
# 전체 백엔드 테스트
cd backend && python -m pytest tests/ -v

# SEO 관련 테스트만
cd backend && python -m pytest tests/domain/product/test_seo_rules.py tests/domain/product/test_seo_service.py tests/api/test_products_seo_router.py -v

# 프론트엔드 타입 체크
cd frontend && npx tsc --noEmit

# 익스텐션 빌드
cd extension && npm run build
```
