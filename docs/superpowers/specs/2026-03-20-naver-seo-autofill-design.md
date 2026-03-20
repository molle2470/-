# Naver SEO Auto-fill Skill — 설계 문서

**작성일:** 2026-03-20
**상태:** 승인됨
**대상 Phase:** Phase 1 (무신사 → 네이버 스마트스토어)

---

## 1. 개요

무재고 구매대행 셀러가 소싱처(무신사 등)에서 상품을 수집할 때, 네이버 스마트스토어 등록에 필요한 20+ SEO 필드를 자동으로 생성하고 입력하는 기능이다.

**핵심 원칙:**
- 빈 칸 없음 — 모든 필드를 채움 ("상세페이지 참조" 금지)
- 수집 즉시 생성 — 대시보드 열면 이미 완성된 SEO 데이터
- 패션 특화 — 의류/신발/모자/가방/양말로 한정되어 규칙 적용 범위 넓음
- 멀티마켓 확장 가능 — DB에 저장하여 쿠팡, 11번가 등 재활용

---

## 2. 아키텍처

### 2.1 데이터 흐름

```
[Extension: 수집하기 클릭]
        ↓
[Backend: POST /api/v1/extension/products]
        ↓
  상품 DB 저장 (기존)
        ↓
  SeoGeneratorService.generate(product, brand, source_category)
   ├─ RuleEngine: 카테고리 매핑, 성별, 연령대, 원산지 (동기, 즉시)
   └─ Claude API: 상품명 최적화, 태그 10개, 소재 추론 (비동기, ~2-3초)
        ↓
  product_seo 테이블 저장
        ↓
[Dashboard: 상품 목록 → SEO 상태 표시]
        ↓
[Dashboard: SEO 미리보기 / 수정]
        ↓
[Extension: 네이버 스마트스토어 등록 페이지에서 자동 입력]
```

### 2.2 생성 방식 결정

| 방식 | 설명 |
|------|------|
| **즉시 생성 (A)** | 수집 API 호출 시 동기 생성 후 응답 반환 |
| 하이브리드 (C) | 규칙 기반 + Claude API 조합 |

수집 응답에 SEO 데이터를 포함하여 반환. 응답 지연 ~2-3초는 Phase 1 허용 범위.

---

## 3. SEO 필드 명세

### 3.1 검색 노출 필드

| 필드 | 생성 방법 | 규칙/프롬프트 |
|------|-----------|--------------|
| **상품명** | Claude | 원본 상품명 기반, 핵심 키워드 앞배치, 100자 이하, 브랜드+카테고리+색상+품번 포함 |
| **검색 태그** | Claude | 브랜드/스타일/소재/색상/시즌/용도 조합, 최대 10개, 각 15자 이하 |
| **카테고리** | 규칙 | 무신사 카테고리 → 네이버 카테고리 ID 매핑 테이블 |

### 3.2 상품 속성 필드

| 필드 | 생성 방법 | 규칙 |
|------|-----------|------|
| **브랜드** | 직접 | 수집된 brand_name 그대로 사용 |
| **소재** | Claude | 상품명 + 설명에서 추론, 의류/신발별 기본값 보유 |
| **색상** | 규칙 | 상품명에서 색상 키워드 추출 (화이트, 블랙, 네이비...) |
| **성별** | 규칙 | 브랜드 사전 + 상품명 키워드 (남성/여성/남녀공용) |
| **연령대** | 규칙 | 기본값 성인; 키즈 키워드 있으면 어린이 |
| **원산지** | 규칙 | 글로벌 브랜드 → 해외; 국내 브랜드 → 국내 |

### 3.3 Claude API 프롬프트 구조

```
시스템: 너는 네이버 스마트스토어 SEO 전문가야.
패션 상품(의류/신발/모자/가방/양말)의 노출도를 최대화하는 상품명과 태그를 생성해.

사용자:
- 원본 상품명: {name}
- 브랜드: {brand_name}
- 카테고리: {source_category}
- 수집 URL: {source_url}
- 가격: {original_price}원

다음을 JSON으로 반환해:
{
  "optimized_name": "...",  // 100자 이하, 핵심키워드 앞배치
  "tags": ["...", ...],     // 최대 10개
  "material": "..."         // 소재 추론
}
```

---

## 4. DB 스키마

### `product_seo` 테이블

```python
class ProductSeo(SQLModel, table=True):
    __tablename__ = "product_seo"

    id: int = Field(primary_key=True)
    product_id: int = Field(foreign_key="products.id", unique=True, index=True)

    # 검색 노출
    optimized_name: str          # Claude 생성 상품명 (100자 이하)
    tags: list[str]              # JSON array, 최대 10개
    naver_category_id: str       # 네이버 카테고리 ID

    # 상품 속성
    brand: str
    material: str                # Claude 추론
    color: str                   # 규칙 추출
    gender: str                  # 남성/여성/남녀공용
    age_group: str               # 성인/어린이
    origin: str                  # 국내/해외

    # 멀티마켓 확장 (Phase 2+)
    market_type: str = Field(default="naver")  # "naver" | "coupang" | "11st" | "lotteon"

    # 메타
    status: str                  # "generated" | "edited" | "fallback" | "failed"
    generated_at: datetime
    edited_at: datetime | None = None
```

> **fallback 상태:** Claude API 실패(타임아웃 5초 초과 또는 오류) 시 규칙 기반 기본값으로 대체되며 `status="fallback"` 저장. 빈 필드 없이 항상 완성된 데이터 보장.

---

## 4-1. ExtensionProductData 수정

익스텐션이 수집 시 `source_category` 필드를 함께 전송해야 SEO 카테고리 매핑이 가능하다.

```typescript
// extension/src/shared/types.ts 추가
interface ProductData {
  // ... 기존 필드
  source_category: string | null  // 무신사 카테고리명 (예: "스니커즈", "반소매 티셔츠")
}
```

```python
# backend/dtos/extension.py 추가
class ExtensionProductData(BaseModel):
    # ... 기존 필드
    source_category: str | None = None
```

`musinsa-product.tsx`의 `parseFromNextData()`에서 `__NEXT_DATA__`의 카테고리 필드를 추출하여 전송한다.

---

## 5. API 엔드포인트

### 기존 엔드포인트 수정

**POST /api/v1/extension/products**
- 기존: 상품 저장 후 `{success: true, product_id}` 반환
- 변경: SEO 생성 포함, `{success: true, product_id, seo: {...}}` 반환

### 신규 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/v1/products/{id}/seo` | SEO 데이터 조회 |
| PATCH | `/api/v1/products/{id}/seo` | SEO 데이터 수정 (대시보드) |

---

## 6. 컴포넌트 목록

### Backend (신규)

| 파일 | 역할 |
|------|------|
| `backend/domain/product/seo_model.py` | ProductSeo SQLModel 정의 |
| `backend/domain/product/seo_rules.py` | 카테고리 매핑 + 색상/성별/원산지 규칙 |
| `backend/domain/product/seo_generator.py` | SeoGeneratorService (규칙 + Claude API) |
| `backend/domain/product/seo_repository.py` | ProductSeoRepository |
| `backend/dtos/seo.py` | SeoCreateRequest, SeoResponse DTO |
| `backend/api/v1/routers/products.py` | SEO 조회/수정 라우터 추가 |
| `alembic/versions/xxx_add_product_seo.py` | product_seo 테이블 마이그레이션 |

### Extension (신규)

| 파일 | 역할 |
|------|------|
| `extension/src/content/naver-seo-autofill.ts` | 네이버 스마트스토어 DOM 자동입력 |
| `extension/manifest.json` | `smartstore.naver.com` 권한 추가 |

### Frontend (신규/수정)

| 파일 | 역할 |
|------|------|
| `frontend/src/app/dashboard/products/page.tsx` | SEO 상태 컬럼 추가 |
| `frontend/src/components/seo/SeoPreviewModal.tsx` | SEO 미리보기/수정 모달 |
| `frontend/src/lib/api/seo.ts` | SEO API 클라이언트 |

---

## 7. 네이버 카테고리 매핑 (패션 특화)

```python
MUSINSA_TO_NAVER_CATEGORY = {
    "스니커즈": "50000803",      # 스포츠/아웃도어 > 신발 > 스니커즈
    "슬립온": "50000803",
    "로퍼/보트슈즈": "50000795",
    "샌들/슬리퍼": "50000801",
    "부츠/워커": "50000797",
    "반소매 티셔츠": "50000000",  # 패션의류 > 상의 > 반소매티
    "맨투맨/스웨트셔츠": "50000001",
    "후드 티셔츠": "50000002",
    "니트/스웨터": "50000003",
    "바지": "50000100",
    "반바지": "50000101",
    "모자": "50000200",
    "가방": "50000300",
    "양말/레깅스": "50000400",
    # ... 확장 가능
}
```

---

## 8. 확장 계획

- **Phase 2:** 쿠팡, 11번가, 롯데온 SEO 필드 추가 (product_seo에 market_type 컬럼)
- **Phase 3:** 소재/색상 추론 정확도 향상 (수집된 상품 설명 이미지 분석)
- **Phase 4:** SEO 성과 피드백 루프 (노출수/클릭수 기반 태그 최적화)

---

## 9. 성공 기준

- [ ] 수집 후 3초 이내 SEO 필드 생성 완료
- [ ] 모든 필드 빈 칸 없음 (Claude 실패 시 규칙 기반 fallback)
- [ ] 네이버 스마트스토어 등록 페이지 자동입력 성공
- [ ] 대시보드에서 수정 후 익스텐션에 반영
