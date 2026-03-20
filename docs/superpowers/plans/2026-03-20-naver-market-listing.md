# 네이버 스마트스토어 마켓 등록 파이프라인 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 무신사에서 수집한 상품을 네이버 스마트스토어 Commerce API로 자동 등록하고, 대시보드에서 등록 상태를 관리한다.

**Architecture:** NaverAdapter에 OAuth2(HMAC-SHA256) + 이미지 업로드 + 상품 등록 API를 실제 구현하고, MarketService에 등록 로직을 추가한다. FastAPI 라우터로 등록/조회/비활성화 엔드포인트를 노출하고, Next.js 대시보드에서 상품 → 마켓 등록 UI를 제공한다.

**Tech Stack:** FastAPI + httpx (Naver API 호출), SQLModel (MarketListing 저장), Next.js 15 + shadcn/ui (등록 UI)

---

## 네이버 Commerce API 핵심 제약사항

구현 전 반드시 숙지:

| 제약 | 영향 | 대응 |
|------|------|------|
| 외부 이미지 URL 등록 불가 | 무신사 thumbnail_url 직접 사용 불가 | `POST /v2/product-images/upload`로 이미지 먼저 업로드 |
| `productInfoProvidedNotice` 카테고리별 유형 필수 | ETC 고정 사용 시 등록 거부 | 카테고리 → 유형 매핑 테이블 사용 |
| PATCH 시 미포함 필드 초기화 | 가격만 수정해도 이미지/배송정보 날아감 | GET → 병합 → PUT 패턴 사용 |
| `PROHIBITED` statusType은 판매자 설정 불가 | deactivate_product 실패 | `SUSPENSION` 사용 |
| API 호출 IP 사전 등록 필요 | 미등록 IP에서 호출 시 401 | 커머스 API 센터에서 IP 등록 먼저 |
| A/S 전화번호 필수 | 빈 문자열 시 등록 거부 | CommonTemplate.as_phone 사용 |

---

## 파일 구조

### 백엔드 — 수정

```
backend/backend/core/config.py                      # naver_* 설정 필드 추가
backend/backend/adapters/naver_adapter.py           # OAuth2 토큰 캐싱 + 이미지 업로드 + 실제 구현
backend/backend/domain/market/service.py            # register_product_to_market() 추가
```

### 백엔드 — 신규

```
backend/backend/adapters/naver_category_map.py      # 무신사→네이버 카테고리 ID + productInfoNotice 유형 매핑
backend/backend/api/v1/routers/market_listings.py   # POST/GET/PATCH 등록 라우터
backend/tests/adapters/test_naver_category_map.py   # 카테고리 매핑 테스트
backend/tests/adapters/test_naver_adapter_real.py   # OAuth2 + 이미지업로드 + 상품등록 단위 테스트 (mock httpx)
backend/tests/domain/market/test_market_listing_service.py  # 등록 서비스 테스트
backend/tests/api/test_market_listings_router.py    # 라우터 import + prefix 테스트
```

### 백엔드 — main.py 수정

```
backend/backend/main.py                             # market_listings_router 등록
```

### 프론트엔드 — 수정

```
frontend/src/app/sourcing/market-listings/page.tsx  # placeholder → serverFetchList 패턴으로 실제 구현
frontend/src/components/sourcing/ProductsTable.tsx  # 등록 버튼 추가 (Client Component로 전환)
```

### 프론트엔드 — 신규

```
frontend/src/components/sourcing/MarketListingTable.tsx  # 등록 현황 테이블
frontend/src/lib/market-listings-api.ts                  # API 클라이언트
```

---

## Task 분해

---

### Task 1: Config — 네이버 API 키 설정 추가 + IP 등록 안내

**Files:**
- Modify: `backend/backend/core/config.py`

> **선행 작업:** 구현 전 [네이버 커머스 API 센터](https://apicenter.commerce.naver.com/)에서
> 애플리케이션을 등록하고, 개발 서버의 IP를 허용 IP 목록에 추가해야 합니다.
> 미등록 IP에서 호출하면 401 오류가 발생합니다.

- [ ] **Step 1: config.py에 네이버 설정 필드 추가**

`# AI Configuration` 블록 아래에 추가:

```python
# ===========================================
# Naver Commerce API Configuration
# ===========================================
naver_client_id: Optional[str] = None
"""네이버 커머스 API 클라이언트 ID"""

naver_client_secret: Optional[str] = None
"""네이버 커머스 API 클라이언트 시크릿"""

naver_channel_id: Optional[str] = None
"""스마트스토어 채널 ID"""
```

- [ ] **Step 2: backend/.env에 키 추가**

```
NAVER_CLIENT_ID=발급받은_클라이언트_ID
NAVER_CLIENT_SECRET=발급받은_클라이언트_시크릿
NAVER_CHANNEL_ID=스마트스토어_채널_ID
```

- [ ] **Step 3: 커밋**

```bash
git add backend/backend/core/config.py
git commit -m "feat: Config에 네이버 커머스 API 설정 필드 추가"
```

---

### Task 2: 네이버 카테고리 + 상품정보제공고시 매핑 테이블

**Files:**
- Create: `backend/backend/adapters/naver_category_map.py`
- Create: `backend/tests/adapters/test_naver_category_map.py`

> **중요:** 네이버 상품 등록 시 `productInfoProvidedNotice` 유형이 카테고리별로 다릅니다.
> 잘못된 유형 사용 시 등록이 거부되거나 검수 제재를 받습니다.
> 카테고리 ID는 실제 등록 전 [네이버 커머스 API 카테고리 조회](https://apicenter.commerce.naver.com/)로 검증 필요.

- [ ] **Step 1: 카테고리 매핑 파일 생성**

```python
# backend/backend/adapters/naver_category_map.py
"""무신사 소싱 카테고리 → 네이버 스마트스토어 leafCategoryId + productInfoProvidedNotice 유형 매핑.

네이버 상품정보제공고시 유형 목록 (주요):
  - "WEAR": 의류 (상의/하의/아우터 등)
  - "SHOES": 신발
  - "BAG": 가방
  - "ACCESSORY": 패션잡화 (모자/벨트/지갑 등)
  - "ETC": 기타

카테고리 ID 검증 필요 URL:
  GET https://api.commerce.naver.com/external/v1/categories/{categoryId}
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class NaverCategoryInfo:
    """네이버 카테고리 매핑 정보"""
    leaf_category_id: str
    product_info_notice_type: str  # productInfoProvidedNoticeType 값


# 무신사 source_category 키워드 → 네이버 매핑 정보
# 키: 무신사 카테고리 문자열에 포함되는 키워드
# 순서 중요: 더 구체적인 키워드를 앞에 배치
MUSINSA_TO_NAVER: dict[str, NaverCategoryInfo] = {
    # 신발
    "스니커즈": NaverCategoryInfo("50000803", "SHOES"),
    "로퍼": NaverCategoryInfo("50000800", "SHOES"),
    "부츠": NaverCategoryInfo("50000797", "SHOES"),
    "샌들": NaverCategoryInfo("50000801", "SHOES"),
    "슬리퍼": NaverCategoryInfo("50000802", "SHOES"),
    "구두": NaverCategoryInfo("50000798", "SHOES"),
    # 가방
    "백팩": NaverCategoryInfo("50000148", "BAG"),
    "숄더백": NaverCategoryInfo("50000150", "BAG"),
    "토트백": NaverCategoryInfo("50000151", "BAG"),
    "크로스백": NaverCategoryInfo("50000149", "BAG"),
    # 상의
    "후드티": NaverCategoryInfo("50000042", "WEAR"),
    "맨투맨": NaverCategoryInfo("50000040", "WEAR"),
    "티셔츠": NaverCategoryInfo("50000039", "WEAR"),
    "셔츠": NaverCategoryInfo("50000038", "WEAR"),
    "니트": NaverCategoryInfo("50000043", "WEAR"),
    # 아우터
    "패딩": NaverCategoryInfo("50000022", "WEAR"),
    "코트": NaverCategoryInfo("50000021", "WEAR"),
    "자켓": NaverCategoryInfo("50000020", "WEAR"),
    "바람막이": NaverCategoryInfo("50000026", "WEAR"),
    # 하의
    "청바지": NaverCategoryInfo("50000050", "WEAR"),
    "슬랙스": NaverCategoryInfo("50000053", "WEAR"),
    "반바지": NaverCategoryInfo("50000055", "WEAR"),
    # 패션잡화
    "모자": NaverCategoryInfo("50000153", "ACCESSORY"),
    "양말": NaverCategoryInfo("50000161", "ACCESSORY"),
    "벨트": NaverCategoryInfo("50000157", "ACCESSORY"),
}

# 매핑 안 될 때 기본값 (패션잡화 > 기타)
DEFAULT_NAVER_INFO = NaverCategoryInfo("50000803", "ETC")


def get_naver_category_info(source_category: str | None) -> NaverCategoryInfo:
    """무신사 카테고리 문자열에서 네이버 카테고리 정보 반환.

    source_category 내 키워드 부분 매칭으로 찾고, 없으면 기본값(스니커즈/ETC) 반환.
    """
    if not source_category:
        return DEFAULT_NAVER_INFO

    for keyword, info in MUSINSA_TO_NAVER.items():
        if keyword in source_category:
            return info

    return DEFAULT_NAVER_INFO
```

- [ ] **Step 2: 테스트 작성**

```python
# backend/tests/adapters/test_naver_category_map.py
"""네이버 카테고리 + 상품정보제공고시 매핑 테스트."""
from backend.adapters.naver_category_map import get_naver_category_info, DEFAULT_NAVER_INFO


def test_shoes_category_returns_shoes_notice_type():
    """스니커즈 → SHOES 유형 반환"""
    info = get_naver_category_info("스니커즈")
    assert info.leaf_category_id == "50000803"
    assert info.product_info_notice_type == "SHOES"


def test_wear_category_returns_wear_notice_type():
    """티셔츠 → WEAR 유형 반환"""
    info = get_naver_category_info("무신사 티셔츠 카테고리")
    assert info.product_info_notice_type == "WEAR"


def test_bag_category_returns_bag_notice_type():
    """백팩 → BAG 유형 반환"""
    info = get_naver_category_info("백팩")
    assert info.product_info_notice_type == "BAG"


def test_none_returns_default():
    """None 입력 시 기본 카테고리 반환"""
    assert get_naver_category_info(None) == DEFAULT_NAVER_INFO


def test_unknown_category_returns_default():
    """알 수 없는 카테고리 → 기본값 반환"""
    assert get_naver_category_info("알수없는카테고리XYZ") == DEFAULT_NAVER_INFO
```

- [ ] **Step 3: 테스트 실행**

```bash
cd backend
pytest tests/adapters/test_naver_category_map.py -v
```

Expected: 5 PASSED

- [ ] **Step 4: 커밋**

```bash
git add backend/backend/adapters/naver_category_map.py backend/tests/adapters/test_naver_category_map.py
git commit -m "feat: 무신사→네이버 카테고리 + 상품정보제공고시 유형 매핑 테이블"
```

---

### Task 3: NaverAdapter — OAuth2 토큰 캐싱 + 이미지 업로드 + 상품 등록 실제 구현

**Files:**
- Modify: `backend/backend/adapters/naver_adapter.py`
- Create: `backend/tests/adapters/test_naver_adapter_real.py`

**설계 결정:**
- 토큰은 인스턴스 변수에 캐싱, 만료 전 30초 여유 두고 갱신
- 이미지는 `POST /v2/product-images/upload`로 먼저 업로드, 반환된 URL 사용
- `update_price`/`update_stock`은 GET → 필드 병합 → PUT 패턴 (미포함 필드 초기화 방지)
- `deactivate_product`는 `SUSPENSION` 사용 (`PROHIBITED`는 판매자 설정 불가)
- `httpx.AsyncClient`는 `close()` 메서드 제공 (라우터에서 finally 블록에서 호출)

- [ ] **Step 1: 테스트 작성 (mock httpx)**

```python
# backend/tests/adapters/test_naver_adapter_real.py
"""NaverAdapter 실제 구현 테스트 (httpx mock 사용)."""
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def adapter():
    from backend.adapters.naver_adapter import NaverAdapter
    return NaverAdapter("test_client_id", "test_client_secret", "test_channel_id")


def make_mock_response(json_data: dict) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = json_data
    return resp


@pytest.mark.asyncio
async def test_get_access_token_hmac_signature(adapter):
    """HMAC-SHA256 서명이 올바르게 생성되는지 검증"""
    import base64, hashlib, hmac as hmac_lib

    captured: dict = {}

    async def fake_post(url, **kwargs):
        captured.update(kwargs.get("data", {}))
        return make_mock_response({"access_token": "tok", "expires_in": 3600})

    with patch.object(adapter.http_client, "post", side_effect=fake_post):
        token = await adapter._get_access_token()

    assert token == "tok"
    ts = captured["timestamp"]
    password = f"test_client_id_{ts}"
    expected_sign = base64.urlsafe_b64encode(
        hmac_lib.new(
            "test_client_secret".encode("utf-8"),
            password.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    ).decode("utf-8")
    assert captured["client_secret_sign"] == expected_sign
    assert captured["grant_type"] == "client_credentials"


@pytest.mark.asyncio
async def test_get_access_token_cached(adapter):
    """두 번 호출해도 토큰이 유효하면 POST 1회만 발생"""
    call_count = 0

    async def fake_post(url, **kwargs):
        nonlocal call_count
        call_count += 1
        return make_mock_response({"access_token": "cached_tok", "expires_in": 3600})

    with patch.object(adapter.http_client, "post", side_effect=fake_post):
        t1 = await adapter._get_access_token()
        t2 = await adapter._get_access_token()

    assert t1 == t2 == "cached_tok"
    assert call_count == 1  # 캐시 적중으로 1번만 호출


@pytest.mark.asyncio
async def test_upload_image_returns_naver_url(adapter):
    """이미지 업로드 → 네이버 호스팅 URL 반환"""
    token_resp = make_mock_response({"access_token": "tok", "expires_in": 3600})
    image_resp = make_mock_response({
        "images": [{"url": "https://shop-phinf.pstatic.net/abc/img.jpg"}]
    })

    call_count = 0

    async def fake_post(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return token_resp
        return image_resp

    with patch.object(adapter.http_client, "post", side_effect=fake_post):
        result = await adapter.upload_image("https://external.com/img.jpg")

    assert result == "https://shop-phinf.pstatic.net/abc/img.jpg"


@pytest.mark.asyncio
async def test_register_product_returns_origin_product_no(adapter):
    """상품 등록 성공 시 originProductNo 문자열 반환"""
    token_resp = make_mock_response({"access_token": "tok", "expires_in": 3600})
    image_resp = make_mock_response({
        "images": [{"url": "https://shop-phinf.pstatic.net/abc/img.jpg"}]
    })
    register_resp = make_mock_response({"originProductNo": 12345678})

    call_count = 0

    async def fake_post(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return token_resp
        if call_count == 2:
            return image_resp
        return register_resp

    with patch.object(adapter.http_client, "post", side_effect=fake_post):
        result = await adapter.register_product({
            "name": "나이키 에어맥스 90",
            "selling_price": 150000,
            "thumbnail_url": "https://example.com/img.jpg",
            "source_category": "스니커즈",
            "return_fee": 5000,
            "as_phone": "02-1234-5678",
        })

    assert result == "12345678"


@pytest.mark.asyncio
async def test_update_price_uses_get_then_put(adapter):
    """가격 수정: GET으로 기존 데이터 조회 후 PUT으로 전체 업데이트"""
    token_resp = make_mock_response({"access_token": "tok", "expires_in": 3600})
    existing_product = {
        "originProduct": {
            "statusType": "SALE",
            "salePrice": 100000,
            "name": "기존상품명",
        }
    }
    get_resp = make_mock_response(existing_product)
    put_resp = make_mock_response({})

    with patch.object(adapter.http_client, "post", new=AsyncMock(return_value=token_resp)):
        with patch.object(adapter.http_client, "get", new=AsyncMock(return_value=get_resp)):
            with patch.object(adapter.http_client, "put", new=AsyncMock(return_value=put_resp)) as mock_put:
                result = await adapter.update_price("99999", 180000)

    assert result is True
    call_kwargs = mock_put.call_args.kwargs
    payload = call_kwargs.get("json", {})
    # 기존 name 보존 + 가격만 변경
    assert payload["originProduct"]["name"] == "기존상품명"
    assert payload["originProduct"]["salePrice"] == 180000


@pytest.mark.asyncio
async def test_update_stock_out_sets_suspension(adapter):
    """품절 처리: statusType=SUSPENSION 설정"""
    token_resp = make_mock_response({"access_token": "tok", "expires_in": 3600})
    existing = {"originProduct": {"statusType": "SALE", "salePrice": 100000, "name": "상품"}}
    get_resp = make_mock_response(existing)
    put_resp = make_mock_response({})

    with patch.object(adapter.http_client, "post", new=AsyncMock(return_value=token_resp)):
        with patch.object(adapter.http_client, "get", new=AsyncMock(return_value=get_resp)):
            with patch.object(adapter.http_client, "put", new=AsyncMock(return_value=put_resp)) as mock_put:
                result = await adapter.update_stock("99999", in_stock=False)

    assert result is True
    payload = mock_put.call_args.kwargs.get("json", {})
    assert payload["originProduct"]["statusType"] == "SUSPENSION"


@pytest.mark.asyncio
async def test_deactivate_product_uses_suspension(adapter):
    """비활성화: SUSPENSION 사용 (PROHIBITED는 판매자 설정 불가)"""
    token_resp = make_mock_response({"access_token": "tok", "expires_in": 3600})
    existing = {"originProduct": {"statusType": "SALE", "salePrice": 100000, "name": "상품"}}
    get_resp = make_mock_response(existing)
    put_resp = make_mock_response({})

    with patch.object(adapter.http_client, "post", new=AsyncMock(return_value=token_resp)):
        with patch.object(adapter.http_client, "get", new=AsyncMock(return_value=get_resp)):
            with patch.object(adapter.http_client, "put", new=AsyncMock(return_value=put_resp)) as mock_put:
                result = await adapter.deactivate_product("99999")

    assert result is True
    payload = mock_put.call_args.kwargs.get("json", {})
    assert payload["originProduct"]["statusType"] == "SUSPENSION"
```

- [ ] **Step 2: 기존 stub 테스트 파일 삭제**

```bash
rm backend/tests/adapters/test_naver_adapter.py
```

- [ ] **Step 3: 테스트 실행 — FAIL 확인**

```bash
cd backend
pytest tests/adapters/test_naver_adapter_real.py -v
```

Expected: FAIL (구현 없음)

- [ ] **Step 4: NaverAdapter 실제 구현**

`backend/backend/adapters/naver_adapter.py` 전체 교체:

```python
"""네이버 스마트스토어 Commerce API 어댑터.

네이버 커머스 API OAuth2(HMAC-SHA256) 인증 기반 상품 등록/수정/품절 처리.

핵심 설계 결정:
- 토큰 캐싱: expires_in 기반으로 만료 30초 전 갱신
- 이미지: 외부 URL 직접 등록 불가 → /v2/product-images/upload 먼저 업로드
- 수정: GET → 병합 → PUT 패턴 (미포함 필드 초기화 방지)
- 비활성화: SUSPENSION (PROHIBITED는 판매자 설정 불가)

참고: https://apicenter.commerce.naver.com/
"""
import base64
import hashlib
import hmac
import time
from typing import Any, Dict, Optional

import httpx

from backend.adapters.base_adapter import BaseMarketAdapter
from backend.adapters.naver_category_map import get_naver_category_info


class NaverAdapter(BaseMarketAdapter):
    """네이버 스마트스토어 Commerce API 어댑터"""

    BASE_URL = "https://api.commerce.naver.com/external"
    AUTH_URL = "https://api.commerce.naver.com/external/v1/oauth2/token"

    def __init__(self, client_id: str, client_secret: str, channel_id: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.channel_id = channel_id
        self.http_client = httpx.AsyncClient(timeout=30.0)
        # 토큰 캐시
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0  # Unix timestamp

    async def close(self) -> None:
        """httpx 클라이언트 종료 (라우터 finally 블록에서 호출)"""
        await self.http_client.aclose()

    async def _get_access_token(self) -> str:
        """OAuth2 액세스 토큰 발급 (HMAC-SHA256 서명, 만료 30초 전 갱신).

        서명 방식:
          password = f"{client_id}_{timestamp}"
          client_secret_sign = base64url(HMAC-SHA256(client_secret, password))
        """
        # 캐시된 토큰이 유효하면 재사용 (만료 30초 전까지)
        if self._access_token and time.time() < self._token_expires_at - 30:
            return self._access_token

        timestamp = str(int(time.time() * 1000))
        password = f"{self.client_id}_{timestamp}"
        hashed = hmac.new(
            self.client_secret.encode("utf-8"),
            password.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        client_secret_sign = base64.urlsafe_b64encode(hashed).decode("utf-8")

        response = await self.http_client.post(
            self.AUTH_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "timestamp": timestamp,
                "client_secret_sign": client_secret_sign,
                "type": "SELF",
            },
        )
        response.raise_for_status()
        data = response.json()
        self._access_token = str(data["access_token"])
        expires_in = int(data.get("expires_in", 3600))
        self._token_expires_at = time.time() + expires_in
        return self._access_token

    def _get_headers(self, access_token: str) -> Dict[str, str]:
        """Authorization 헤더 반환"""
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def upload_image(self, image_url: str) -> str:
        """외부 이미지 URL을 네이버 호스팅으로 업로드.

        네이버 Commerce API는 외부 URL 직접 등록이 불가능하므로
        /v2/product-images/upload API로 먼저 업로드해야 합니다.

        Args:
            image_url: 업로드할 외부 이미지 URL (무신사 CDN URL 등)

        Returns:
            네이버 호스팅 이미지 URL

        Raises:
            httpx.HTTPStatusError: 업로드 실패 시
            ValueError: 응답에 이미지 URL이 없을 때
        """
        access_token = await self._get_access_token()
        headers = self._get_headers(access_token)

        response = await self.http_client.post(
            f"{self.BASE_URL}/v2/product-images/upload",
            headers=headers,
            json={"imageUrls": [image_url]},
        )
        response.raise_for_status()
        images = response.json().get("images", [])
        if not images or not images[0].get("url"):
            raise ValueError(f"이미지 업로드 응답에 URL 없음: {response.json()}")
        return str(images[0]["url"])

    def _build_product_info_notice(
        self, notice_type: str
    ) -> Dict[str, Any]:
        """카테고리별 상품정보제공고시 생성.

        네이버 상품 등록 시 카테고리에 맞는 유형 필수.
        지원 유형: WEAR, SHOES, BAG, ACCESSORY, ETC
        """
        common_notice = {
            "returnCostReason": "제조사 및 수입원에 의한 경우 제조사 또는 수입원에서 부담",
            "noRefundReason": "상품의 하자 또는 오배송의 경우 판매자 귀책으로 반품 배송비 무료",
            "qualityAssuranceStandard": "소비자분쟁해결규정에 따름",
            "compensationProcedure": "소비자분쟁해결규정에 따름",
            "troubleShootingContents": "소비자분쟁해결규정에 따름",
        }

        notice_data: Dict[str, Any] = {
            "productInfoProvidedNoticeType": notice_type,
        }

        if notice_type == "WEAR":
            notice_data["wear"] = {**common_notice, "material": "상세페이지 참조", "color": "상세페이지 참조", "size": "상세페이지 참조", "manufacturer": "상세페이지 참조", "importDeclaration": "상세페이지 참조", "caution": "상세페이지 참조", "warrantyPolicy": "소비자분쟁해결규정에 따름", "afterServiceDirector": "판매자"}
        elif notice_type == "SHOES":
            notice_data["shoes"] = {**common_notice, "material": "상세페이지 참조", "color": "상세페이지 참조", "size": "상세페이지 참조", "manufacturer": "상세페이지 참조", "importDeclaration": "상세페이지 참조", "caution": "상세페이지 참조", "warrantyPolicy": "소비자분쟁해결규정에 따름", "afterServiceDirector": "판매자"}
        elif notice_type == "BAG":
            notice_data["bag"] = {**common_notice, "material": "상세페이지 참조", "color": "상세페이지 참조", "size": "상세페이지 참조", "manufacturer": "상세페이지 참조", "importDeclaration": "상세페이지 참조", "caution": "상세페이지 참조", "warrantyPolicy": "소비자분쟁해결규정에 따름", "afterServiceDirector": "판매자"}
        elif notice_type == "ACCESSORY":
            notice_data["accessory"] = {**common_notice, "material": "상세페이지 참조", "color": "상세페이지 참조", "size": "상세페이지 참조", "manufacturer": "상세페이지 참조", "importDeclaration": "상세페이지 참조", "caution": "상세페이지 참조", "warrantyPolicy": "소비자분쟁해결규정에 따름", "afterServiceDirector": "판매자"}
        else:  # ETC
            notice_data["etc"] = common_notice

        return notice_data

    async def _build_product_payload(
        self, product_data: Dict[str, Any], naver_image_url: str
    ) -> Dict[str, Any]:
        """상품 데이터 → 네이버 커머스 API v2 등록 payload 변환.

        Args:
            product_data: 등록할 상품 데이터
              - name (str): 상품명
              - selling_price (int): 판매가
              - source_category (str|None): 소싱처 카테고리
              - return_fee (int): 반품 배송비
              - as_phone (str): A/S 전화번호 (필수)
            naver_image_url: 네이버 호스팅 이미지 URL (upload_image() 결과)
        """
        category_info = get_naver_category_info(
            str(product_data.get("source_category") or "")
        )
        return_fee = int(product_data.get("return_fee") or 5000)
        as_phone = str(product_data.get("as_phone") or "")
        product_info_notice = self._build_product_info_notice(
            category_info.product_info_notice_type
        )

        return {
            "originProduct": {
                "statusType": "SALE",
                "saleType": "NEW",
                "leafCategoryId": category_info.leaf_category_id,
                "name": str(product_data["name"]),
                "detailContent": f"<p>{product_data['name']}</p>",
                "images": {
                    "representativeImage": {"url": naver_image_url},
                },
                "salePrice": int(product_data["selling_price"]),
                "stockQuantity": 999,
                "deliveryInfo": {
                    "deliveryType": "DELIVERY",
                    "deliveryAttributeType": "NORMAL",
                    "deliveryFee": {"deliveryFeeType": "FREE"},
                    "claimDeliveryInfo": {
                        "returnDeliveryFee": return_fee,
                        "exchangeDeliveryFee": return_fee,
                    },
                },
                "detailAttribute": {
                    "afterServiceInfo": {
                        "afterServiceTelephoneNumber": as_phone,
                        "afterServiceGuideContent": "소비자분쟁해결기준에 의거 교환 및 환불",
                    },
                    "originAreaInfo": {
                        "originAreaCode": "0200037",  # 기타
                        "content": "",
                    },
                    "productInfoProvidedNotice": product_info_notice,
                },
            },
            "smartstoreChannelProduct": {
                "naverShoppingRegistration": True,
                "channelProductDisplayStatusType": "ON",
            },
        }

    async def register_product(self, product_data: Dict[str, Any]) -> Optional[str]:
        """이미지 업로드 후 상품 등록 → originProductNo 반환.

        Returns:
            마켓 상품 ID (originProductNo 문자열), 실패 시 None
        """
        # 1. 이미지 먼저 네이버에 업로드
        thumbnail_url = str(product_data.get("thumbnail_url") or "")
        naver_image_url = await self.upload_image(thumbnail_url)

        # 2. 상품 등록 payload 빌드
        access_token = await self._get_access_token()
        headers = self._get_headers(access_token)
        payload = await self._build_product_payload(product_data, naver_image_url)

        # 3. 상품 등록 API 호출
        response = await self.http_client.post(
            f"{self.BASE_URL}/v2/products",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        origin_no = response.json().get("originProductNo")
        return str(origin_no) if origin_no else None

    async def _get_product(self, market_product_id: str) -> Dict[str, Any]:
        """기존 상품 전체 데이터 조회 (수정 시 필드 병합용)"""
        access_token = await self._get_access_token()
        headers = self._get_headers(access_token)
        response = await self.http_client.get(
            f"{self.BASE_URL}/v2/products/{market_product_id}",
            headers=headers,
        )
        response.raise_for_status()
        return dict(response.json())

    async def update_price(self, market_product_id: str, new_price: int) -> bool:
        """가격 수정 — GET → 병합 → PUT (미포함 필드 초기화 방지)"""
        existing = await self._get_product(market_product_id)
        existing.setdefault("originProduct", {})["salePrice"] = new_price

        access_token = await self._get_access_token()
        headers = self._get_headers(access_token)
        response = await self.http_client.put(
            f"{self.BASE_URL}/v2/products/{market_product_id}",
            headers=headers,
            json=existing,
        )
        response.raise_for_status()
        return True

    async def update_stock(self, market_product_id: str, in_stock: bool) -> bool:
        """재고/품절 처리 — GET → 병합 → PUT"""
        existing = await self._get_product(market_product_id)
        status = "SALE" if in_stock else "SUSPENSION"
        existing.setdefault("originProduct", {})["statusType"] = status

        access_token = await self._get_access_token()
        headers = self._get_headers(access_token)
        response = await self.http_client.put(
            f"{self.BASE_URL}/v2/products/{market_product_id}",
            headers=headers,
            json=existing,
        )
        response.raise_for_status()
        return True

    async def deactivate_product(self, market_product_id: str) -> bool:
        """상품 비활성화 — SUSPENSION 사용 (PROHIBITED는 판매자 설정 불가)"""
        return await self.update_stock(market_product_id, in_stock=False)
```

- [ ] **Step 5: 테스트 실행 — PASS 확인**

```bash
cd backend
pytest tests/adapters/test_naver_adapter_real.py tests/adapters/test_naver_category_map.py -v
```

Expected: 전체 PASS

- [ ] **Step 6: 커밋**

```bash
git add backend/backend/adapters/naver_adapter.py backend/tests/adapters/
git commit -m "feat: NaverAdapter OAuth2 토큰캐싱 + 이미지업로드 + 상품등록/수정/비활성화 실제 구현"
```

---

### Task 4: MarketService — 마켓 등록 비즈니스 로직

**Files:**
- Modify: `backend/backend/domain/market/service.py`
- Create: `backend/tests/domain/market/test_market_listing_service.py`

**설계 결정:**
- `as_phone`은 `CommonTemplate`에서 조회 (빈 문자열 시 네이버 등록 거부됨)
- NaverAdapter API 실패 시 `ListingStatusEnum.FAILED` 상태로 기록 (실패 이력 추적)
- commit은 서비스 레이어에서 수행 (세션 의존성 패턴 확인 후 조정)

- [ ] **Step 1: CommonTemplateRepository import 확인**

```bash
grep -n "CommonTemplateRepository\|as_phone" backend/backend/domain/market/repository.py
grep -n "as_phone" backend/backend/domain/market/model.py
```

`CommonTemplate.as_phone` 필드와 `CommonTemplateRepository` 존재 확인.

- [ ] **Step 2: 테스트 작성**

```python
# backend/tests/domain/market/test_market_listing_service.py
"""MarketService 마켓 등록 로직 테스트."""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_register_product_to_market_success(mock_session):
    """register_product_to_market 성공 시 REGISTERED 상태의 MarketListing 반환"""
    from backend.domain.market.service import MarketService
    from backend.domain.market.model import ListingStatusEnum

    service = MarketService(mock_session)

    # 리포지토리 mock
    mock_listing_repo = AsyncMock()
    mock_listing_repo.filter_by_async = AsyncMock(return_value=[])  # 중복 없음
    service.listing_repo = mock_listing_repo

    mock_template_repo = AsyncMock()
    mock_template = MagicMock()
    mock_template.commission_rate = 0.08
    mock_template.return_fee = 5000
    mock_template_repo.find_by_market = AsyncMock(return_value=mock_template)
    service.template_repo = mock_template_repo

    mock_common_template_repo = AsyncMock()
    mock_common = MagicMock()
    mock_common.as_phone = "02-1234-5678"
    mock_common_template_repo.get_async = AsyncMock(return_value=mock_common)
    service.common_template_repo = mock_common_template_repo

    mock_adapter = AsyncMock()
    mock_adapter.register_product = AsyncMock(return_value="NAVER_123456")
    mock_adapter.close = AsyncMock()

    product = MagicMock()
    product.id = 1
    product.name = "나이키 에어맥스"
    product.original_price = 100000
    product.thumbnail_url = "https://example.com/img.jpg"
    product.source_category = "스니커즈"

    result = await service.register_product_to_market(
        product=product,
        market_account_id=1,
        market_id=1,
        common_template_id=1,
        adapter=mock_adapter,
        margin_rate=0.2,
    )

    assert result.market_product_id == "NAVER_123456"
    assert result.listing_status == ListingStatusEnum.REGISTERED
    mock_adapter.register_product.assert_called_once()


@pytest.mark.asyncio
async def test_register_product_to_market_duplicate_blocked(mock_session):
    """이미 REGISTERED 상태 상품 재등록 시도 → ValueError"""
    from backend.domain.market.service import MarketService
    from backend.domain.market.model import ListingStatusEnum, MarketListing

    service = MarketService(mock_session)

    existing = MagicMock(spec=MarketListing)
    existing.listing_status = ListingStatusEnum.REGISTERED

    mock_listing_repo = AsyncMock()
    mock_listing_repo.filter_by_async = AsyncMock(return_value=[existing])
    service.listing_repo = mock_listing_repo

    product = MagicMock()
    product.id = 1

    with pytest.raises(ValueError, match="이미 등록된 상품"):
        await service.register_product_to_market(
            product=product,
            market_account_id=1,
            market_id=1,
            common_template_id=1,
            adapter=AsyncMock(),
            margin_rate=0.2,
        )


@pytest.mark.asyncio
async def test_register_product_to_market_api_failure_records_failed(mock_session):
    """NaverAdapter API 실패 시 FAILED 상태 MarketListing 저장"""
    from backend.domain.market.service import MarketService
    from backend.domain.market.model import ListingStatusEnum

    service = MarketService(mock_session)

    mock_listing_repo = AsyncMock()
    mock_listing_repo.filter_by_async = AsyncMock(return_value=[])
    service.listing_repo = mock_listing_repo

    mock_template_repo = AsyncMock()
    mock_template = MagicMock()
    mock_template.commission_rate = 0.08
    mock_template.return_fee = 5000
    mock_template_repo.find_by_market = AsyncMock(return_value=mock_template)
    service.template_repo = mock_template_repo

    mock_common_template_repo = AsyncMock()
    mock_common = MagicMock()
    mock_common.as_phone = "02-0000-0000"
    mock_common_template_repo.get_async = AsyncMock(return_value=mock_common)
    service.common_template_repo = mock_common_template_repo

    mock_adapter = AsyncMock()
    mock_adapter.register_product = AsyncMock(side_effect=Exception("API 오류"))

    product = MagicMock()
    product.id = 1
    product.name = "상품명"
    product.original_price = 100000
    product.thumbnail_url = "https://example.com/img.jpg"
    product.source_category = "스니커즈"

    with pytest.raises(Exception, match="API 오류"):
        await service.register_product_to_market(
            product=product,
            market_account_id=1,
            market_id=1,
            common_template_id=1,
            adapter=mock_adapter,
            margin_rate=0.2,
        )

    # FAILED 상태 리스팅이 저장되었는지 확인
    assert mock_session.add.called
    added_listing = mock_session.add.call_args[0][0]
    assert added_listing.listing_status == ListingStatusEnum.FAILED
```

- [ ] **Step 3: 테스트 실행 — FAIL 확인**

```bash
cd backend
pytest tests/domain/market/test_market_listing_service.py -v
```

Expected: FAIL (register_product_to_market 없음)

- [ ] **Step 4: MarketService에 register_product_to_market 추가**

`backend/backend/domain/market/service.py` 상단 import에 추가:

```python
from datetime import datetime, timezone
from backend.adapters.base_adapter import BaseMarketAdapter
from backend.domain.market.model import ListingStatusEnum, MarketListing
from backend.domain.market.repository import CommonTemplateRepository
```

클래스 `__init__`에 추가:

```python
self.common_template_repo = CommonTemplateRepository(session)
```

메서드 추가:

```python
async def register_product_to_market(
    self,
    product: Any,
    market_account_id: int,
    market_id: int,
    common_template_id: int,
    adapter: BaseMarketAdapter,
    margin_rate: float = 0.2,
) -> MarketListing:
    """상품을 마켓에 등록하고 MarketListing 저장.

    1. 중복 등록 차단 (REGISTERED 상태 이미 있으면 ValueError)
    2. 판매가 계산 (수수료 + 마진율)
    3. CommonTemplate에서 A/S 전화번호 조회 (필수)
    4. NaverAdapter로 이미지 업로드 + API 등록
    5. 성공: REGISTERED, 실패: FAILED 상태로 MarketListing 저장

    Args:
        product: Product 객체 (id, name, original_price, thumbnail_url, source_category)
        market_account_id: 마켓 계정 ID
        market_id: 마켓 ID (수수료율 조회용)
        common_template_id: 공통 템플릿 ID (A/S 전화번호 등 조회용)
        adapter: 마켓 API 어댑터 (NaverAdapter 등)
        margin_rate: 마진율 (기본 20%)

    Raises:
        ValueError: 이미 REGISTERED 상태 등록 내역이 있을 때
    """
    # 중복 등록 차단
    existing = await self.listing_repo.filter_by_async(
        product_id=product.id,
        market_account_id=market_account_id,
    )
    for e in existing:
        if e.listing_status == ListingStatusEnum.REGISTERED:
            raise ValueError(
                f"이미 등록된 상품 (product_id={product.id}, account_id={market_account_id})"
            )

    # 판매가 계산
    selling_price = await self.calculate_selling_price(
        original_price=product.original_price,
        market_id=market_id,
        margin_rate=margin_rate,
    )

    # 템플릿에서 반품배송비 + A/S 전화번호 조회
    template = await self.template_repo.find_by_market(market_id=market_id)
    return_fee = template.return_fee if template else 5000

    common_template = await self.common_template_repo.get_async(common_template_id)
    as_phone = common_template.as_phone if common_template else ""

    # MarketListing 초기 레코드 (PENDING 상태)
    listing = MarketListing(
        product_id=product.id,
        market_account_id=market_account_id,
        selling_price=selling_price,
        listing_status=ListingStatusEnum.PENDING,
    )

    try:
        # NaverAdapter API 호출 (이미지 업로드 포함)
        market_product_id = await adapter.register_product({
            "name": product.name,
            "selling_price": selling_price,
            "thumbnail_url": product.thumbnail_url,
            "source_category": getattr(product, "source_category", None),
            "return_fee": return_fee,
            "as_phone": as_phone,
        })
        listing.listing_status = ListingStatusEnum.REGISTERED
        listing.market_product_id = market_product_id
        listing.registered_at = datetime.now(tz=timezone.utc)
    except Exception:
        # API 실패 이력 기록 (재시도 추적용)
        listing.listing_status = ListingStatusEnum.FAILED
        self.session.add(listing)
        await self.session.flush()
        await self.session.commit()
        raise

    self.session.add(listing)
    await self.session.flush()
    await self.session.commit()
    return listing
```

- [ ] **Step 5: 테스트 실행 — PASS 확인**

```bash
cd backend
pytest tests/domain/market/test_market_listing_service.py -v
```

Expected: 3 PASSED

- [ ] **Step 6: 커밋**

```bash
git add backend/backend/domain/market/service.py backend/tests/domain/market/test_market_listing_service.py
git commit -m "feat: MarketService.register_product_to_market() — 가격계산 + A/S전화번호 + 실패이력 기록"
```

---

### Task 5: 마켓 등록 라우터

**Files:**
- Create: `backend/backend/api/v1/routers/market_listings.py`
- Modify: `backend/backend/main.py`
- Create: `backend/tests/api/test_market_listings_router.py`

**중요:** `ProductRepository.get_async(id)` 사용 (`get_by_id_async` 아님 — BaseRepository 메서드명 확인됨)

엔드포인트:
- `POST /api/v1/market-listings` — 상품 마켓 등록
- `GET /api/v1/market-listings` — 등록 목록 조회
- `PATCH /api/v1/market-listings/{listing_id}/deactivate` — 비활성화

- [ ] **Step 1: BaseRepository 메서드명 확인**

```bash
grep -n "async def get" backend/backend/domain/shared/base_repository.py
```

`get_async(id)` 또는 유사 메서드명을 확인하고, 아래 라우터 코드에 적용.

- [ ] **Step 2: 라우터 테스트 작성**

```python
# backend/tests/api/test_market_listings_router.py
"""마켓 등록 라우터 import + prefix 테스트."""
import sys
from unittest.mock import MagicMock, AsyncMock

_mock_orm = MagicMock()
_mock_orm.get_read_session_dependency = MagicMock(return_value=AsyncMock())
_mock_orm.get_write_session_dependency = MagicMock(return_value=AsyncMock())
if "backend.db.orm" not in sys.modules:
    sys.modules["backend.db.orm"] = _mock_orm

_mock_config = MagicMock()
_mock_config.settings = MagicMock(
    naver_client_id="test_id",
    naver_client_secret="test_secret",
    naver_channel_id="test_channel",
)
if "backend.core.config" not in sys.modules:
    sys.modules["backend.core.config"] = _mock_config


def test_market_listings_router_imports():
    from backend.api.v1.routers.market_listings import router
    assert router is not None


def test_router_has_correct_prefix():
    from backend.api.v1.routers.market_listings import router
    assert router.prefix == "/market-listings"
```

- [ ] **Step 3: 라우터 구현**

```python
# backend/backend/api/v1/routers/market_listings.py
"""마켓 등록 관리 API 라우터.

POST   /market-listings                     — 상품 마켓 등록
GET    /market-listings                     — 등록 목록 조회
PATCH  /market-listings/{id}/deactivate    — 비활성화
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.db.orm import get_read_session_dependency, get_write_session_dependency
from backend.domain.market.model import ListingStatusEnum
from backend.domain.market.repository import MarketListingRepository
from backend.domain.market.service import MarketService
from backend.domain.product.repository import ProductRepository

router = APIRouter(prefix="/market-listings", tags=["market-listings"])


class RegisterRequest(BaseModel):
    """마켓 등록 요청"""
    product_id: int
    market_account_id: int
    market_id: int
    common_template_id: int
    margin_rate: float = 0.2


class ListingResponse(BaseModel):
    """마켓 등록 내역 응답"""
    id: int
    product_id: int
    market_account_id: int
    selling_price: int
    listing_status: str
    market_product_id: Optional[str]
    registered_at: Optional[str]
    created_at: str


def _to_listing_response(listing: object) -> ListingResponse:
    return ListingResponse(
        id=listing.id,
        product_id=listing.product_id,
        market_account_id=listing.market_account_id,
        selling_price=listing.selling_price,
        listing_status=listing.listing_status.value,
        market_product_id=listing.market_product_id,
        registered_at=listing.registered_at.isoformat() if listing.registered_at else None,
        created_at=listing.created_at.isoformat(),
    )


@router.post("", status_code=201)
async def register_to_market(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_write_session_dependency),
) -> ListingResponse:
    """상품을 마켓에 등록한다."""
    # 상품 조회 (BaseRepository.get_async 사용)
    product_repo = ProductRepository(session)
    product = await product_repo.get_async(request.product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"상품 ID {request.product_id}을 찾을 수 없습니다.")

    # 네이버 API 설정 확인
    if not all([settings.naver_client_id, settings.naver_client_secret, settings.naver_channel_id]):
        raise HTTPException(status_code=503, detail="네이버 API 설정 없음. 환경변수(NAVER_*) 확인 필요.")

    from backend.adapters.naver_adapter import NaverAdapter
    adapter = NaverAdapter(
        client_id=settings.naver_client_id,
        client_secret=settings.naver_client_secret,
        channel_id=settings.naver_channel_id,
    )

    service = MarketService(session)
    try:
        listing = await service.register_product_to_market(
            product=product,
            market_account_id=request.market_account_id,
            market_id=request.market_id,
            common_template_id=request.common_template_id,
            adapter=adapter,
            margin_rate=request.margin_rate,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    finally:
        await adapter.close()

    return _to_listing_response(listing)


@router.get("")
async def list_listings(
    product_id: Optional[int] = Query(None),
    account_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_read_session_dependency),
) -> List[ListingResponse]:
    """마켓 등록 목록 조회"""
    service = MarketService(session)
    listings = await service.list_listings(product_id=product_id, account_id=account_id)
    return [_to_listing_response(listing) for listing in listings]


@router.patch("/{listing_id}/deactivate")
async def deactivate_listing(
    listing_id: int,
    session: AsyncSession = Depends(get_write_session_dependency),
) -> dict:
    """마켓 등록 상품 비활성화 (SUSPENSION)"""
    repo = MarketListingRepository(session)
    listing = await repo.get_async(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail=f"등록 ID {listing_id}을 찾을 수 없습니다.")

    if not all([settings.naver_client_id, settings.naver_client_secret, settings.naver_channel_id]):
        raise HTTPException(status_code=503, detail="네이버 API 설정 없음")

    from backend.adapters.naver_adapter import NaverAdapter
    adapter = NaverAdapter(
        client_id=settings.naver_client_id,
        client_secret=settings.naver_client_secret,
        channel_id=settings.naver_channel_id,
    )
    try:
        if listing.market_product_id:
            await adapter.deactivate_product(listing.market_product_id)
    finally:
        await adapter.close()

    listing.listing_status = ListingStatusEnum.DEACTIVATED
    session.add(listing)
    await session.commit()

    return {"success": True, "listing_id": listing_id}
```

- [ ] **Step 4: main.py에 라우터 등록**

`backend/backend/main.py`에 추가:

```python
from backend.api.v1.routers.market_listings import router as market_listings_router
# include_router 블록에:
app.include_router(market_listings_router, prefix="/api/v1")
```

- [ ] **Step 5: 테스트 + 서버 확인**

```bash
cd backend
pytest tests/api/test_market_listings_router.py -v
uvicorn backend.main:app --reload --port 28080
# http://localhost:28080/docs 에서 /api/v1/market-listings 확인
```

- [ ] **Step 6: 커밋**

```bash
git add backend/backend/api/v1/routers/market_listings.py backend/backend/main.py backend/tests/api/test_market_listings_router.py
git commit -m "feat: POST/GET/PATCH /api/v1/market-listings 라우터 (NaverAdapter close() 포함)"
```

---

### Task 6: 프론트엔드 — 마켓 등록 API 클라이언트 + 등록 현황 UI

**Files:**
- Create: `frontend/src/lib/market-listings-api.ts`
- Create: `frontend/src/components/sourcing/MarketListingTable.tsx`
- Modify: `frontend/src/app/sourcing/market-listings/page.tsx`
- Modify: `frontend/src/components/sourcing/ProductsTable.tsx`

> **패턴 확인:** 기존 `products/page.tsx`는 `serverFetchList`를 사용합니다.
> Server Component의 GET은 동일 패턴을 따르고, 등록(POST) 액션은 Client Component로.

- [ ] **Step 1: 기존 serverFetchList 패턴 확인**

```bash
grep -rn "serverFetchList" frontend/src/lib/ frontend/src/app/sourcing/
```

`serverFetchList` 함수 시그니처와 사용법 확인 후 아래 API 클라이언트에 적용.

- [ ] **Step 2: API 클라이언트 작성**

```typescript
// frontend/src/lib/market-listings-api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:28080"

export interface MarketListing {
  id: number
  product_id: number
  market_account_id: number
  selling_price: number
  listing_status: "pending" | "registered" | "failed" | "deactivated"
  market_product_id: string | null
  registered_at: string | null
  created_at: string
}

export interface RegisterRequest {
  product_id: number
  market_account_id: number
  market_id: number
  common_template_id: number
  margin_rate?: number
}

/** 클라이언트 사이드 마켓 등록 (POST) */
export async function registerToMarket(req: RegisterRequest): Promise<MarketListing> {
  const res = await fetch(`${API_BASE}/api/v1/market-listings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err as { detail?: string }).detail || "마켓 등록 실패")
  }
  return res.json() as Promise<MarketListing>
}

/** 클라이언트 사이드 비활성화 (PATCH) */
export async function deactivateListing(listingId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/market-listings/${listingId}/deactivate`, {
    method: "PATCH",
  })
  if (!res.ok) throw new Error("비활성화 실패")
}
```

- [ ] **Step 3: MarketListingTable 컴포넌트 작성**

```typescript
// frontend/src/components/sourcing/MarketListingTable.tsx
"use client"

import { useState } from "react"
import { deactivateListing, type MarketListing } from "@/lib/market-listings-api"

const STATUS_LABEL: Record<string, string> = {
  pending: "대기",
  registered: "등록됨",
  failed: "실패",
  deactivated: "비활성",
}

const STATUS_COLOR: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  registered: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  deactivated: "bg-gray-100 text-gray-500",
}

interface Props {
  listings: MarketListing[]
  onUpdate?: () => void
}

export function MarketListingTable({ listings, onUpdate }: Props) {
  const [loadingId, setLoadingId] = useState<number | null>(null)

  async function handleDeactivate(listingId: number) {
    if (!confirm("정말 비활성화하시겠습니까?")) return
    setLoadingId(listingId)
    try {
      await deactivateListing(listingId)
      onUpdate?.()
    } catch (e) {
      alert(e instanceof Error ? e.message : "오류 발생")
    } finally {
      setLoadingId(null)
    }
  }

  if (listings.length === 0) {
    return <p className="text-gray-400 text-sm mt-4">등록된 상품이 없습니다.</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b text-gray-500 text-left">
            <th className="py-2 pr-4">상품 ID</th>
            <th className="py-2 pr-4">판매가</th>
            <th className="py-2 pr-4">마켓 상품번호</th>
            <th className="py-2 pr-4">상태</th>
            <th className="py-2 pr-4">등록일</th>
            <th className="py-2">액션</th>
          </tr>
        </thead>
        <tbody>
          {listings.map((listing) => (
            <tr key={listing.id} className="border-b hover:bg-gray-50">
              <td className="py-2 pr-4 text-gray-700">#{listing.product_id}</td>
              <td className="py-2 pr-4 font-medium">
                {listing.selling_price.toLocaleString()}원
              </td>
              <td className="py-2 pr-4 text-gray-500 font-mono text-xs">
                {listing.market_product_id ?? "-"}
              </td>
              <td className="py-2 pr-4">
                <span
                  className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLOR[listing.listing_status]}`}
                >
                  {STATUS_LABEL[listing.listing_status]}
                </span>
              </td>
              <td className="py-2 pr-4 text-gray-500 text-xs">
                {listing.registered_at
                  ? new Date(listing.registered_at).toLocaleDateString("ko-KR")
                  : "-"}
              </td>
              <td className="py-2">
                {listing.listing_status === "registered" && (
                  <button
                    onClick={() => handleDeactivate(listing.id)}
                    disabled={loadingId === listing.id}
                    className="text-xs text-red-500 hover:text-red-700 disabled:opacity-50"
                  >
                    {loadingId === listing.id ? "처리중..." : "비활성화"}
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

- [ ] **Step 4: market-listings 페이지 구현 (serverFetchList 패턴)**

```typescript
// frontend/src/app/sourcing/market-listings/page.tsx
import { MarketListingTable } from "@/components/sourcing/MarketListingTable"
import { serverFetchList } from "@/lib/server-fetch"
import type { MarketListing } from "@/lib/market-listings-api"

export default async function MarketListingsPage() {
  const listings = await serverFetchList<MarketListing>("/api/v1/market-listings")

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-gray-900">마켓 등록 관리</h1>
        <span className="text-sm text-gray-400">총 {listings.length}개</span>
      </div>
      <MarketListingTable listings={listings} />
    </div>
  )
}
```

- [ ] **Step 5: ProductsTable에 마켓 등록 버튼 추가**

`frontend/src/components/sourcing/ProductsTable.tsx` 읽기 후 구조 파악.
Client Component로 전환 필요 시 `"use client"` 추가.
각 행 액션 열에 RegisterButton 추가:

```tsx
// ProductsTable.tsx 내부에 인라인으로 추가하거나 별도 파일로 분리
"use client"
import { useState } from "react"
import { registerToMarket } from "@/lib/market-listings-api"

// TODO: 실제 market_account_id, market_id, common_template_id는
// DB 조회 또는 환경변수로 관리. Phase 1은 DB에 직접 삽입한 값 사용.
const NAVER_MARKET_ACCOUNT_ID = 1  // market_accounts 테이블의 네이버 계정 ID
const NAVER_MARKET_ID = 1           // markets 테이블의 네이버 스마트스토어 ID
const COMMON_TEMPLATE_ID = 1        // common_templates 테이블의 기본 템플릿 ID

function RegisterButton({ productId }: { productId: number }) {
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  async function handleRegister() {
    if (!confirm("스마트스토어에 등록하시겠습니까?")) return
    setLoading(true)
    try {
      await registerToMarket({
        product_id: productId,
        market_account_id: NAVER_MARKET_ACCOUNT_ID,
        market_id: NAVER_MARKET_ID,
        common_template_id: COMMON_TEMPLATE_ID,
      })
      setDone(true)
    } catch (e) {
      alert(e instanceof Error ? e.message : "등록 실패")
    } finally {
      setLoading(false)
    }
  }

  if (done) return <span className="text-xs text-green-600 font-medium">등록완료</span>
  return (
    <button
      onClick={handleRegister}
      disabled={loading}
      className="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700 disabled:opacity-50"
    >
      {loading ? "등록중..." : "마켓 등록"}
    </button>
  )
}
```

- [ ] **Step 6: 빌드 확인**

```bash
cd frontend
pnpm build
```

Expected: 빌드 성공 (타입 오류 없음)

- [ ] **Step 7: 커밋**

```bash
git add frontend/src/
git commit -m "feat: 마켓 등록 UI — 상품 목록 등록 버튼 + 등록 현황 페이지 (serverFetchList 패턴)"
```

---

### Task 7: DB 초기 데이터 + 통합 테스트

**마켓 등록 전 DB에 필요한 레코드 확인/생성:**

- `markets` 테이블에 `name="네이버 스마트스토어"` 레코드
- `common_templates` 테이블에 A/S 전화번호 포함 레코드
- `market_templates` 테이블에 수수료율 + 반품배송비 레코드
- `market_accounts` 테이블에 네이버 계정 레코드

- [ ] **Step 1: DB 초기 데이터 삽입**

```sql
-- 1. 공통 템플릿 (A/S 전화번호 필수)
INSERT INTO common_templates (shipping_origin, return_address, courier, as_phone, as_description, origin_country, updated_at)
VALUES ('서울 강남구', '서울 강남구', 'CJ대한통운', '02-0000-0000', '소비자분쟁해결기준에 의거 교환 및 환불', '기타', NOW())
RETURNING id;  -- 반환된 id를 common_template_id로 사용

-- 2. 네이버 스마트스토어 마켓
INSERT INTO markets (name, created_at)
VALUES ('네이버 스마트스토어', NOW())
ON CONFLICT DO NOTHING
RETURNING id;  -- 반환된 id를 market_id로 사용

-- 3. 사업자 그룹 (없으면 생성)
INSERT INTO business_groups (name, created_at)
VALUES ('기본 사업자', NOW())
RETURNING id;

-- 4. 마켓 계정 (위에서 반환된 ID 사용)
INSERT INTO market_accounts (business_group_id, market_id, account_id, is_active, created_at, updated_at)
VALUES (1, 1, '스마트스토어_판매자_아이디', true, NOW(), NOW())
RETURNING id;  -- 반환된 id를 market_account_id로 사용

-- 5. 마켓 템플릿 (수수료 8%, 반품 5000원)
INSERT INTO market_templates (market_id, common_template_id, commission_rate, margin_rate, shipping_fee, return_fee, updated_at)
VALUES (1, 1, 0.08, 0.20, 0, 5000, NOW());
```

> **주의:** 삽입 후 반환된 ID를 프론트엔드의 `NAVER_MARKET_ACCOUNT_ID`, `NAVER_MARKET_ID`, `COMMON_TEMPLATE_ID` 상수에 반영.

- [ ] **Step 2: 전체 테스트 실행**

```bash
cd backend
pytest tests/ -v --tb=short
```

Expected: 전체 PASS

- [ ] **Step 3: E2E 수동 테스트**

```
1. 무신사에서 상품 수집 (익스텐션 수집 버튼 클릭)
2. 대시보드 /sourcing/products에서 수집된 상품 확인
3. "마켓 등록" 버튼 클릭 → 로딩 → "등록완료" 표시
4. /sourcing/market-listings에서 REGISTERED 상태 확인
5. 네이버 스마트스토어 판매자 센터에서 상품 등록 확인
6. "비활성화" 버튼 → 네이버 SUSPENSION 처리 확인
```

- [ ] **Step 4: 최종 커밋**

```bash
git add .
git commit -m "feat: 네이버 스마트스토어 마켓 등록 파이프라인 Phase 1 완성"
```

---

## 구현 후 검증 체크리스트

- [ ] 전체 테스트 통과: `pytest backend/tests/ -v`
- [ ] Swagger UI에서 `POST /api/v1/market-listings` 수동 호출
- [ ] 실제 네이버 API 키로 OAuth2 토큰 발급 성공
- [ ] 이미지 업로드 API 성공 (네이버 호스팅 URL 반환)
- [ ] 네이버 스마트스토어 판매자 센터에서 상품 등록 확인
- [ ] 카테고리별 `productInfoProvidedNotice` 유형 검증
- [ ] 등록 후 가격 수정 (update_price) 동작 확인
- [ ] 비활성화 (SUSPENSION) 동작 확인

## 주의사항

1. **네이버 카테고리 ID 검증 필수** — `naver_category_map.py`의 ID들은 추정값. 실제 등록 전 네이버 커머스 API 카테고리 조회 API로 검증
2. **API 호출 IP 등록** — 네이버 커머스 API 센터에서 개발 서버 IP를 허용 목록에 추가 (미등록 시 401)
3. **판매가 단위** — 네이버는 10원 미만 단위 설정 불가할 수 있음. PriceCalculator 결과를 `round(price / 10) * 10`으로 10원 단위 올림 고려
4. **stockQuantity=999** — 무재고 구매대행이므로 임의 수량. 모니터링으로 품절 감지 시 update_stock(False) 호출
