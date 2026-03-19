# 크롬 익스텐션 기반 소싱 시스템 설계서

## 개요

국내 무재고 구매대행 소싱 통합 시스템의 아키텍처를 서버 크롤링에서 크롬 익스텐션 기반으로 전환한다.
기존 백엔드 비즈니스 로직(가격 계산, 마켓 연동, SEO 생성)은 유지하고,
소싱처 데이터 수집/모니터링만 크롬 익스텐션이 담당한다.

### 전환 배경

- 무신사 등 소싱처의 안티봇(Cloudflare, 핑거프린팅) → 서버 크롤링 차단
- 로그인 세션/등급별 가격 관리의 복잡성 → 실제 브라우저 세션 활용
- 경쟁 솔루션(오버링크, 더망고, 샵마인) 모두 익스텐션 방식 채택
- 프록시/headless 브라우저 인프라 비용 절감

### Phase 1 목표

- 소싱처: 무신사 (1개)
- 판매 마켓: 네이버 스마트스토어 (1개)
- 상품 수: 10-20개
- 목표: 수집 → 등록 → 모니터링 전체 파이프라인 동작 검증

---

## 전체 아키텍처

```
┌──────────────────────────────────────────────┐
│         Next.js 대시보드 (메인 UI)             │
│                                              │
│  · 수집 설정 (사이트, 브랜드, 카테고리 매핑)     │
│  · 상품 관리 (등록/수정/삭제)                   │
│  · 마켓 등록 관리 (스마트스토어)                 │
│  · 가격/재고 모니터링 현황                      │
│  · 실시간 로그 뷰어                            │
└──────────┬───────────────────────────────────┘
           │ REST API + SSE (실시간 로그)
           ▼
┌──────────────────────────────────────────────┐
│              FastAPI 백엔드                    │
│                                              │
│  · 익스텐션 명령 큐 (REST 기반 폴링)            │
│  · 수집 설정 CRUD                             │
│  · 비즈니스 로직 (PriceCalculator, SEO 등)     │
│  · 마켓 API 연동 (NaverAdapter)               │
│  · MarketSyncService (가격/재고 동기화)        │
│  · 도메인 서비스 (Product/Source/Brand/Market)  │
└──────────┬───────────────────────────────────┘
           │ REST API (폴링 + 결과 전송)
           ▼
┌──────────────────────────────────────────────┐
│           크롬 익스텐션 (워커)                  │
│                                              │
│  · chrome.alarms로 주기적 백엔드 폴링           │
│  · 명령 수신 → 무신사 탭 열기 → 데이터 수집     │
│  · Content Script: fetch/XHR 오버라이드로       │
│    무신사 API 응답 가로채기 (JSON 파싱)          │
│  · Content Script: 상품 페이지 [수집] 버튼      │
│  · Popup: 연결 상태 표시                       │
└──────────────────────────────────────────────┘
           │
           ▼
      무신사 웹사이트 (소싱처)
```

### 역할 분리 원칙

- **대시보드 = 두뇌**: 모든 관리, 설정, 명령, 조회
- **백엔드 = 심장**: 비즈니스 로직, 마켓 API, DB 관리, 명령 큐
- **익스텐션 = 손과 발**: 소싱처 데이터 수집 실행

---

## 크롬 익스텐션 설계

### Manifest V3 제약사항 및 대응

| MV3 제약 | 영향 | 대응 |
|----------|------|------|
| `webRequest`로 응답 본문 읽기 불가 | 네트워크 응답 JSON 직접 접근 불가 | Content Script에서 fetch/XHR 오버라이드 (페이지 컨텍스트 주입) |
| Service Worker 5분 후 자동 종료 | WebSocket 상시 연결 불가 | REST API 폴링 + chrome.alarms (연결 대신 주기적 요청) |
| chrome.alarms 최소 주기 1분 | 짧은 주기 모니터링 제한 | 모니터링은 10분+ 주기이므로 문제없음 |

### Manifest V3 설정

```json
{
  "manifest_version": 3,
  "permissions": ["alarms", "storage", "notifications", "tabs"],
  "host_permissions": [
    "https://*.musinsa.com/*",
    "https://api.musinsa.com/*",
    "http://localhost:28080/*"
  ],
  "content_scripts": [
    {
      "matches": ["https://www.musinsa.com/app/goods/*"],
      "js": ["content/musinsa-product.js"],
      "run_at": "document_idle"
    }
  ]
}
```

### 파일 구조

```
extension/
├── manifest.json
├── vite.config.ts
├── package.json
├── src/
│   ├── background/
│   │   ├── index.ts                # Service Worker 진입점
│   │   ├── api-client.ts           # 백엔드 REST API 호출
│   │   ├── command-poller.ts       # 백엔드 명령 큐 폴링 (chrome.alarms)
│   │   └── monitoring-manager.ts   # 모니터링 알람 관리 (chrome.alarms)
│   ├── content/
│   │   ├── musinsa-product.tsx     # 상품 페이지 [수집] 버튼 삽입
│   │   └── musinsa-interceptor.ts  # fetch/XHR 오버라이드 (페이지 컨텍스트 주입)
│   ├── popup/
│   │   ├── Popup.tsx               # 연결 상태 UI
│   │   └── index.html
│   └── shared/
│       ├── types.ts                # 공유 타입 정의
│       └── constants.ts            # API URL, 설정값
```

### 데이터 수집 방식: fetch/XHR 오버라이드

Manifest V3에서는 `chrome.webRequest`로 응답 본문을 읽을 수 없다.
대신 Content Script가 페이지 컨텍스트에 스크립트를 주입하여
원래의 `fetch`/`XMLHttpRequest`를 래핑하고 응답 데이터를 가로챈다.
이것이 경쟁 솔루션들이 실제 사용하는 표준 방식이다.

```
[무신사 페이지 로드]
       │
       ▼
[Content Script: musinsa-interceptor.ts]
  페이지 컨텍스트에 스크립트 주입
       │
       ▼
[주입된 스크립트: fetch/XHR 래핑]
  원본 fetch → 래핑 fetch (응답 복사 후 전달)
       │
       ▼
[무신사 SPA가 내부 API 호출]
  예: GET /api2/hm/goods/12345
       │
       ▼
[래핑된 fetch가 응답 JSON을 캡처]
  window.postMessage로 Content Script에 전달
       │
       ▼
[Content Script → Background SW]
  chrome.runtime.sendMessage로 파싱된 데이터 전달
       │
       ▼
[Background SW → 백엔드 REST API]
  POST /api/v1/extension/products
```

### 모듈별 역할

**Background Service Worker**
- `api-client.ts`: 백엔드 REST API 호출 (인증 토큰 포함)
- `command-poller.ts`: chrome.alarms로 주기적(30초)으로 백엔드 명령 큐 폴링
  - 명령 수신 시: 탭 열기, 모니터링 등록/해제 등 실행
  - Service Worker 종료 후 재시작 시 alarms가 자동으로 다시 트리거
- `monitoring-manager.ts`: chrome.alarms로 등록된 상품 주기적 체크
  - HIGH 등급: 10-15분 (±2분 랜덤)
  - NORMAL 등급: 30-60분 (±5분 랜덤)
  - 알람 트리거 → `chrome.tabs.create()`로 무신사 상품 페이지 열기
  - Content Script가 데이터 수집 → Background SW로 전달 → 백엔드 전송
  - 수집 완료 후 탭 자동 닫기
  - **모니터링 목록은 chrome.storage.local에 영속화** (SW 재시작 시 복원)

**Content Script**
- `musinsa-product.tsx`: 상품 상세 페이지에 [수집하기] 버튼 삽입, 수집 완료 시 [수집됨 ✓] 표시
- `musinsa-interceptor.ts`: 페이지 컨텍스트에 fetch/XHR 오버라이드 스크립트 주입
  - 무신사 API 응답을 가로채서 상품 JSON 파싱
  - 파싱 대상: 상품명, 정가, 브랜드, 재고 상태, 혜택 플래그, 이미지, 옵션

**Popup**
- 백엔드 서버 연결 상태 (정상/끊김)
- 모니터링 중인 상품 수
- 최근 수집 건수
- 설정: 백엔드 URL, API 키 입력

---

## 익스텐션 ↔ 백엔드 통신 설계

### REST API 폴링 방식 (WebSocket 대신)

Manifest V3의 Service Worker는 5분 후 자동 종료되어 WebSocket 상시 연결이 불가능하다.
대신 **REST API 폴링 + chrome.alarms** 방식을 사용한다.

```
[chrome.alarms: 30초마다 트리거]
       │
       ▼
[Background SW 깨어남]
       │
       ▼
[GET /api/v1/extension/commands]
  백엔드 명령 큐에서 대기 중인 명령 가져오기
       │
   명령 있음?
   ├── 없음 → SW 다시 슬립
   └── 있음 → 명령 실행
              │
              ▼
        [명령 실행 완료]
              │
              ▼
        [POST /api/v1/extension/commands/{id}/ack]
          명령 처리 완료 보고
```

### 인증

- 백엔드에서 **API 키** 발급 (사이드로딩 개인용이므로 간단한 방식)
- 모든 요청 헤더에 `X-Extension-Key: {api_key}` 포함
- Phase 2 이후 JWT 토큰 기반으로 업그레이드 가능

### 백엔드 API 엔드포인트

```
# 익스텐션 통신 (폴링 기반)
GET    /api/v1/extension/commands           # 대기 중인 명령 조회
POST   /api/v1/extension/commands/{id}/ack  # 명령 처리 완료 보고
POST   /api/v1/extension/products           # 수집된 상품 데이터 전송
POST   /api/v1/extension/products/{id}/changes  # 모니터링 변동 전송
POST   /api/v1/extension/heartbeat          # 익스텐션 생존 신호

# 수집 설정 관리 (대시보드 → 백엔드)
POST   /api/v1/collection-settings          # 수집 설정 생성
GET    /api/v1/collection-settings          # 수집 설정 목록
PUT    /api/v1/collection-settings/{id}     # 수집 설정 수정
DELETE /api/v1/collection-settings/{id}     # 수집 설정 삭제

# 수집 명령 (대시보드 → 백엔드 명령 큐 → 익스텐션 폴링)
POST   /api/v1/collection-settings/{id}/start   # 수집 시작 (Phase 2)
POST   /api/v1/collection-settings/{id}/stop    # 수집 중지 (Phase 2)

# 실시간 로그
GET    /api/v1/collection-logs              # 수집 로그 조회
GET    /api/v1/collection-logs/stream       # SSE 실시간 로그 스트림

# 기존 API 유지
/api/v1/sources/*        # 소싱처 관리
/api/v1/brands/*         # 브랜드 관리
/api/v1/products/*       # 상품 관리
/api/v1/markets/*        # 마켓/등록 관리
/api/v1/monitoring/*     # 변동 이력
```

### 명령 큐 구조

```python
class ExtensionCommand(SQLModel, table=True):
    """익스텐션 명령 큐"""
    __tablename__ = "extension_commands"

    id: Optional[int] = Field(default=None, primary_key=True)
    command_type: str       # MONITOR_REGISTER, MONITOR_UNREGISTER, COLLECT_START (Phase 2)
    payload: str            # JSON 문자열 (명령 파라미터)
    status: str = "pending" # pending → processing → done / failed
    created_at: datetime
    processed_at: Optional[datetime]
```

### 명령 타입

**Phase 1:**

```json
// 모니터링 등록 (상품 마켓 등록 시 자동 생성)
{
  "command_type": "MONITOR_REGISTER",
  "payload": {
    "product_id": 42,
    "source_url": "https://www.musinsa.com/app/goods/12345",
    "grade": "high"
  }
}

// 모니터링 해제
{
  "command_type": "MONITOR_UNREGISTER",
  "payload": { "product_id": 42 }
}
```

**Phase 2 (일괄 수집):**

```json
{
  "command_type": "COLLECT_START",
  "payload": {
    "setting_id": 1,
    "site": "musinsa",
    "brand": "나이키",
    "category_url": "https://www.musinsa.com/categories/...",
    "max_count": 500
  }
}
```

### 익스텐션 → 백엔드 데이터 전송

```json
// 개별 수집 결과
POST /api/v1/extension/products
{
  "source": "musinsa",
  "product": {
    "name": "나이키 에어맥스 90",
    "original_price": 169000,
    "source_url": "https://www.musinsa.com/app/goods/12345",
    "source_product_id": "12345",
    "brand_name": "나이키",
    "stock_status": "in_stock",
    "grade_discount_available": true,
    "point_usable": true,
    "point_earnable": true,
    "thumbnail_url": "https://...",
    "image_urls": ["https://..."],
    "options": [{"color": "블랙", "size": "270", "stock": 5}]
  }
}

// 모니터링 변동 보고
POST /api/v1/extension/products/42/changes
{
  "change_type": "price",    // "price" | "stock" | "both"
  "old_price": 52000,
  "new_price": 48000,
  "stock_status": "in_stock"
}
```

---

## 백엔드 변경사항

### 신규 도메인 모델

**CollectionSetting — 수집 설정 (브랜드×카테고리 매핑)**

```python
class CollectionSetting(SQLModel, table=True):
    __tablename__ = "collection_settings"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str                         # 수집설정명 (예: 나이키_신발)
    source_id: int                    # 소싱처 FK (인덱스)
    brand_name: str                   # 브랜드명
    category_url: str                 # 수집 대상 URL
    max_count: int = 500              # 수집 한도
    is_active: bool = True            # 인덱스
    last_collected_at: Optional[datetime]
    collected_count: int = 0
    created_at: datetime
    updated_at: datetime
```

**CollectionLog — 수집 로그**

```python
class CollectionLog(SQLModel, table=True):
    __tablename__ = "collection_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    setting_id: Optional[int]         # 수집 설정 FK (개별 수집 시 null)
    product_name: str                 # 수집된 상품명
    status: str                       # success / failed
    message: Optional[str]            # 에러 메시지
    created_at: datetime              # 인덱스 (보관 기간 정책용)
```

**ExtensionCommand — 익스텐션 명령 큐**

```python
class ExtensionCommand(SQLModel, table=True):
    __tablename__ = "extension_commands"

    id: Optional[int] = Field(default=None, primary_key=True)
    command_type: str                 # MONITOR_REGISTER, MONITOR_UNREGISTER 등
    payload: str                      # JSON 문자열
    status: str = "pending"           # pending / processing / done / failed (인덱스)
    created_at: datetime
    processed_at: Optional[datetime]
```

### 기존 모델 관계 정리

| 기존 모델 | 판정 | 설명 |
|----------|------|------|
| `CrawlJob` (monitoring/model.py) | **폐기** | `ExtensionCommand` + `CollectionLog`로 대체 |
| `CrawledProduct` (crawling/base_crawler.py) | **DTO로 이전** | 익스텐션 수신 DTO(`ExtensionProductData`)로 변환, `backend/dtos/extension.py`에 배치 |
| 그 외 monitoring 모델 | **유지** | `PriceStockHistory`, `MonitoringAlert` 등은 그대로 |

### 신규 서비스

**CollectionService — 수집 비즈니스 로직**

```python
class CollectionService:
    # 수집 설정 CRUD
    # 수집된 상품 데이터 처리:
    #   1. 브랜드 지재권 필터링 (is_ip_approved 확인)
    #   2. DB 저장 (ProductService)
    #   3. 가격 계산 (PriceCalculator)
    #   4. SEO 생성 (SeoGenerator)
    # 수집 로그 기록
```

**ExtensionCommandService — 명령 큐 관리**

```python
class ExtensionCommandService:
    # 명령 생성 (대시보드/시스템 → 명령 큐)
    # 대기 명령 조회 (익스텐션 폴링)
    # 명령 상태 업데이트 (처리 완료/실패)
    # 만료 명령 정리
```

### 삭제 대상

| 파일 | 이유 |
|------|------|
| `domain/crawling/base_crawler.py` | 익스텐션이 대체 |
| `domain/crawling/musinsa_crawler.py` | 익스텐션이 대체 |
| `services/scheduler.py` | chrome.alarms가 대체 |
| `tests/domain/crawling/*` | 대상 코드 삭제 |
| `tests/services/test_scheduler.py` | 대상 코드 삭제 |
| `monitoring/model.py`의 `CrawlJob` | `ExtensionCommand`로 대체 |

### 유지 대상

| 파일 | 이유 |
|------|------|
| `services/price_calculator.py` | 가격 계산 로직 그대로 사용 |
| `services/seo_generator.py` | SEO 생성 로직 그대로 사용 |
| `services/market_sync.py` | 마켓 동기화 로직 그대로 사용 |
| `adapters/naver_adapter.py` | 스마트스토어 API 그대로 사용 |
| `domain/{source,brand,product,market,monitoring}/*` | 도메인 모델/서비스/레포지토리 유지 |

---

## 대시보드 (Next.js) 설계

### 페이지 구조

```
/sourcing                          # 대시보드 메인 (수집 현황 요약)
/sourcing/collection-settings      # 수집 설정 목록/관리
/sourcing/collection-settings/new  # 수집 설정 생성
/sourcing/products                 # 수집된 상품 목록
/sourcing/products/[id]            # 상품 상세/수정
/sourcing/market-listings          # 마켓 등록 관리
/sourcing/monitoring               # 모니터링 현황
/sourcing/logs                     # 수집/변동 로그
```

### 주요 화면

**수집 설정 관리** (오버링크 스크린샷과 유사)
- 수집사이트 선택 (Phase 1: 무신사만)
- 브랜드명, 카테고리 URL 입력
- 수집 한도 설정
- 수집 설정 테이블 (No, 사이트, 설정명, URL, 상품수, 수집일)
- Phase 2: 수집 시작/중지 버튼, 진행률 표시

**상품 목록**
- 수집된 상품 테이블 (이미지, 상품명, 원가, 판매가, 마진, 재고상태)
- 마켓 등록 상태 표시
- 브랜드 지재권 경고 표시 (is_ip_approved=false인 상품)
- 선택 → 마켓 등록 액션

**실시간 로그**
- SSE 기반 실시간 로그 스트림
- 수집 진행률 표시 (Phase 2)
- 에러/성공 상태 색상 구분

---

## 기술 스택

### 익스텐션

| 항목 | 기술 |
|------|------|
| 빌드 | Vite + CRXJS |
| 언어 | TypeScript |
| UI | React + Tailwind CSS |
| 상태 관리 | Zustand |
| 영속 저장 | chrome.storage.local |
| 통신 | REST API (fetch) |

### 백엔드 (기존 + 추가)

| 항목 | 기술 |
|------|------|
| 프레임워크 | FastAPI |
| SSE | sse-starlette |
| ORM | SQLModel + SQLAlchemy |
| DB | PostgreSQL |
| HTTP 클라이언트 | httpx (마켓 API용) |

### 대시보드 (기존)

| 항목 | 기술 |
|------|------|
| 프레임워크 | Next.js 15 (App Router) |
| 언어 | TypeScript |
| UI | shadcn/ui + Tailwind CSS 4 |
| 상태 관리 | Zustand |
| 폼 | React Hook Form + Zod |

---

## 데이터 흐름

### 개별 수집 흐름 (Phase 1 핵심)

```
1. 사용자: 무신사 상품 페이지 방문
2. Content Script (musinsa-interceptor.ts):
   페이지 컨텍스트에 fetch/XHR 오버라이드 스크립트 주입
3. 무신사 SPA가 내부 API 호출 (자동 발생)
4. 오버라이드된 fetch가 응답 JSON 캡처 →
   window.postMessage → Content Script → Background SW
5. Content Script (musinsa-product.tsx):
   [수집하기] 버튼 활성화 (데이터 준비됨)
6. 사용자: [수집하기] 버튼 클릭
7. Background SW → POST /api/v1/extension/products
8. 백엔드:
   a. 브랜드 지재권 확인 (is_ip_approved)
   b. Product DB 저장
   c. PriceCalculator로 판매가 계산
   d. SeoGenerator로 SEO 태그 생성
9. Content Script: [수집됨 ✓] 표시
```

### 모니터링 흐름 (Phase 1)

```
1. 상품 마켓 등록 시:
   백엔드가 ExtensionCommand 생성 (MONITOR_REGISTER)
2. 익스텐션 폴링 (30초마다):
   GET /api/v1/extension/commands → 명령 수신
3. Background SW:
   chrome.alarms 등록 + chrome.storage.local에 모니터링 목록 저장
4. 알람 트리거 (10-60분 주기):
   chrome.tabs.create()로 무신사 상품 페이지 열기 (백그라운드 탭)
5. Content Script가 페이지 로드 시 자동으로 API 응답 캡처
6. Background SW: 기존 데이터와 비교
   · 가격 변동 → POST /api/v1/extension/products/{id}/changes
   · 재고 변동 → POST /api/v1/extension/products/{id}/changes
7. 백엔드: MarketSyncService → 스마트스토어 가격/재고 자동 반영
8. 수집 완료 후 탭 자동 닫기
9. 대시보드: SSE로 변동 알림 표시
```

### 일괄 수집 흐름 (Phase 2)

```
1. 대시보드: 수집 설정 선택 → "수집 시작" 클릭
2. 백엔드: ExtensionCommand 생성 (COLLECT_START)
3. 익스텐션 폴링 → 명령 수신
4. Background SW: 카테고리 URL로 탭 열기
5. Content Script: 목록 페이지에서 상품 목록 파싱
6. 페이지 순회하며 상품별 데이터 수집 → 백엔드 전송
7. 대시보드: SSE로 실시간 진행률 표시
```

---

## 에러 핸들링

| 시나리오 | 대응 |
|---------|------|
| 백엔드 서버 다운 | 익스텐션 Popup에 "서버 연결 끊김" 표시, 수집 데이터 chrome.storage.local에 임시 저장, 서버 복구 시 재전송 |
| 무신사 API 구조 변경 | musinsa-interceptor.ts 파싱 실패 → 에러 로그 전송, 수동 업데이트 필요 |
| 브라우저 닫기 (모니터링 중단) | 대시보드에 "익스텐션 오프라인" 표시 (heartbeat 30초 이상 미수신) |
| 수집 중 무신사 페이지 에러 | 3회 재시도 → 실패 로그 기록 |
| 지재권 미승인 브랜드 수집 시도 | 백엔드에서 경고와 함께 수집은 허용 (대시보드에서 경고 표시) |

---

## Phase 구분

### Phase 1 (현재) — 핵심 파이프라인

- 크롬 익스텐션 코어 (Background SW + Content Script + Popup)
- REST API 폴링 통신 (백엔드 ↔ 익스텐션)
- 수집 설정 CRUD (대시보드, 조회/관리 목적)
- **개별 수집** (Content Script [수집] 버튼으로 상품 1개씩)
- 모니터링 (chrome.alarms → 탭 기반 주기적 체크)
- 대시보드 최소 UI (수집 설정 + 상품 목록 + 실시간 로그)
- 스마트스토어 등록 (기존 NaverAdapter)
- 브랜드 지재권 필터링

### Phase 2 — 일괄 수집 + 확장

- **일괄 수집** (대시보드에서 "수집 시작" → 익스텐션이 목록 페이지 순회)
- 수집 한도/페이지 범위 설정
- 수집 진행률 실시간 표시
- SSG 소싱처 추가
- 쿠팡 마켓 + 소명 관리

### Phase 3 — 운영 자동화

- 주문 관리 (마켓 주문 → 소싱처 자동 주문)
- 셀링 리포트 (매출/마진 통계)
- 다중 사업자 (5개 사업자 × 6개 마켓)
- 추가 마켓/소싱처 확장

---

## Phase 1 파일 구조

```
extension/                          # 크롬 익스텐션 (신규)
├── manifest.json
├── vite.config.ts
├── package.json
├── src/
│   ├── background/
│   │   ├── index.ts
│   │   ├── api-client.ts
│   │   ├── command-poller.ts
│   │   └── monitoring-manager.ts
│   ├── content/
│   │   ├── musinsa-product.tsx
│   │   └── musinsa-interceptor.ts
│   ├── popup/
│   │   ├── Popup.tsx
│   │   └── index.html
│   └── shared/
│       ├── types.ts
│       └── constants.ts

backend/                            # 기존 + 추가
├── backend/
│   ├── api/v1/routers/
│   │   ├── extension.py            # 익스텐션 통신 (신규)
│   │   ├── collection_settings.py  # 수집 설정 CRUD (신규)
│   │   ├── collection_logs.py      # 수집 로그 + SSE (신규)
│   │   ├── products.py             # 상품 관리 (기존 계획)
│   │   ├── sources.py              # 소싱처 관리 (기존 계획)
│   │   ├── brands.py               # 브랜드 관리 (기존 계획)
│   │   └── markets.py              # 마켓 관리 (기존 계획)
│   ├── domain/
│   │   ├── collection/             # 수집 설정 도메인 (신규)
│   │   │   ├── model.py            # CollectionSetting, CollectionLog, ExtensionCommand
│   │   │   ├── repository.py
│   │   │   └── service.py          # CollectionService, ExtensionCommandService
│   │   └── crawling/               # 삭제 (익스텐션으로 대체)
│   ├── dtos/
│   │   └── extension.py            # 익스텐션 수신 DTO (CrawledProduct 계승, 신규)
│   └── services/
│       └── scheduler.py            # 삭제 (chrome.alarms로 대체)

frontend/                           # 기존 + 소싱 대시보드
├── src/
│   ├── app/sourcing/               # 소싱 관리 페이지들
│   │   ├── page.tsx                # 대시보드 메인
│   │   ├── collection-settings/    # 수집 설정 관리
│   │   ├── products/               # 상품 목록/관리
│   │   ├── market-listings/        # 마켓 등록 관리
│   │   ├── monitoring/             # 모니터링 현황
│   │   └── logs/                   # 수집/변동 로그
│   ├── components/sourcing/        # 소싱 전용 컴포넌트
│   ├── lib/sourcing-api.ts         # 소싱 API 클라이언트
│   └── types/sourcing.ts           # 소싱 TypeScript 타입
```
