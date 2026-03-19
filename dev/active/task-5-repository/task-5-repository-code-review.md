# Task 5: Repository 레이어 코드 리뷰

Last Updated: 2026-03-19

---

## Executive Summary

5개 도메인 Repository 파일 전체 검토 결과, BaseRepository 상속 구조와 생성자 패턴은 모두 올바르게 구현되어 있습니다. 스펙에서 요구한 커스텀 메서드도 전부 존재합니다. 단, 중요도 높은 이슈 2건과 참고용 사항이 있습니다.

---

## 검토 대상 파일

| 파일 | Repository 클래스 |
|---|---|
| `domain/source/repository.py` | SourceRepository, SourceBrandRepository |
| `domain/brand/repository.py` | BrandRepository |
| `domain/product/repository.py` | ProductRepository, ProductOptionGroupRepository, ProductOptionValueRepository, ProductVariantRepository |
| `domain/market/repository.py` | BusinessGroupRepository, MarketRepository, MarketAccountRepository, CommonTemplateRepository, MarketTemplateRepository, SeoRuleRepository, CoupangBrandClearanceRepository, MarketListingRepository |
| `domain/monitoring/repository.py` | PriceStockHistoryRepository, CrawlJobRepository, NotificationRepository, CategoryMappingRepository |

---

## 스펙 체크리스트

### 1. BaseRepository 상속 여부

| Repository | 상속 | 생성자 순서 (session, Model) |
|---|---|---|
| SourceRepository | ✅ | ✅ |
| SourceBrandRepository | ✅ | ✅ |
| BrandRepository | ✅ | ✅ |
| ProductRepository | ✅ | ✅ |
| ProductOptionGroupRepository | ✅ | ✅ |
| ProductOptionValueRepository | ✅ | ✅ |
| ProductVariantRepository | ✅ | ✅ |
| BusinessGroupRepository | ✅ | ✅ |
| MarketRepository | ✅ | ✅ |
| MarketAccountRepository | ✅ | ✅ |
| CommonTemplateRepository | ✅ | ✅ |
| MarketTemplateRepository | ✅ | ✅ |
| SeoRuleRepository | ✅ | ✅ |
| CoupangBrandClearanceRepository | ✅ | ✅ |
| MarketListingRepository | ✅ | ✅ |
| PriceStockHistoryRepository | ✅ | ✅ |
| CrawlJobRepository | ✅ | ✅ |
| NotificationRepository | ✅ | ✅ |
| CategoryMappingRepository | ✅ | ✅ |

**결론: 전 파일 생성자 패턴 정상.**

### 2. 스펙 요구 커스텀 메서드 존재 여부

| 요구 메서드 | 파일 | 존재 여부 |
|---|---|---|
| `SourceRepository.find_active_sources()` | source/repository.py L22 | ✅ |
| `ProductRepository.find_by_source_product_id()` | product/repository.py L25 | ✅ |
| `ProductRepository.find_registered_products()` | product/repository.py L33 | ✅ |
| `ProductRepository.find_by_filters()` | product/repository.py L37 | ✅ |
| `MarketAccountRepository.find_active_accounts()` | market/repository.py L55 | ✅ |
| `CoupangBrandClearanceRepository.find_completed_clearances()` | market/repository.py L103 | ✅ |
| `CrawlJobRepository.find_pending_jobs()` | monitoring/repository.py L42 | ✅ |
| `CrawlJobRepository.find_in_progress_jobs()` | monitoring/repository.py L46 | ✅ |
| `NotificationRepository.find_unread()` | monitoring/repository.py L57 | ✅ |

**결론: 요구 메서드 전부 구현됨.**

---

## Critical Issues (반드시 수정)

해당 없음.

---

## Important Issues (수정 권장)

### [ISSUE-1] `product/repository.py` — `find_by_filters()` 내 `dict` 타입 힌트 누락

**위치:** `product/repository.py` L46

```python
filters: dict = {}
```

`dict`는 `any` 타입과 동일한 수준의 비명시 타입입니다. `Dict[str, Any]`로 명시해야 프로젝트 타입 안정성 규칙을 만족합니다. 현재 파일 상단에 `Optional, List`는 임포트되어 있으나 `Dict, Any`는 누락되어 있습니다.

**수정 방향:**

```python
from typing import Any, Dict, List, Optional
...
filters: Dict[str, Any] = {}
```

---

### [ISSUE-2] `monitoring/repository.py` — `NotificationRepository.find_unread()`에 user_id 필터 없음

**위치:** `monitoring/repository.py` L57~L63

```python
async def find_unread(self, limit: int = 20) -> List[Notification]:
    """읽지 않은 알림 목록 (최신순)"""
    return await self.filter_by_async(
        is_read=False,
        limit=limit,
        order_by="created_at",
        order_by_desc=True,
    )
```

현재 구현은 DB 전체의 읽지 않은 알림을 모두 반환합니다. 멀티 사용자(또는 멀티 사업자) 환경에서 `user_id` 또는 `business_group_id` 기반 격리 없이 호출하면 다른 사용자의 알림이 노출될 수 있습니다. 서비스 레이어에서 필터링한다 해도 Repository 레이어에서 수신자를 인자로 받는 것이 더 안전합니다.

**수정 방향:**

```python
async def find_unread(
    self, user_id: Optional[int] = None, limit: int = 20
) -> List[Notification]:
    """읽지 않은 알림 목록 (최신순)"""
    kwargs: Dict[str, Any] = {"is_read": False}
    if user_id is not None:
        kwargs["user_id"] = user_id
    return await self.filter_by_async(
        limit=limit,
        order_by="created_at",
        order_by_desc=True,
        **kwargs,
    )
```

---

## Minor Suggestions (참고용)

### [SUGGEST-1] `brand/repository.py` — `find_approved_brands()` 인덱스 의존성 주석 부재

`is_ip_approved=True` 조건으로 전체 테이블 스캔이 발생할 수 있습니다. 브랜드 마스터 테이블이 일정 규모 이상으로 커지면 `is_ip_approved` 컬럼에 DB 인덱스가 필요합니다. 모델 정의(`brand/model.py`)에 인덱스 설정 여부를 확인하고, 없다면 추가를 고려하세요.

### [SUGGEST-2] `market/repository.py` — `BusinessGroupRepository`에 커스텀 메서드 없음

스펙 요구사항에는 포함되지 않으나, 사업자 그룹 5개 조회는 매우 빈번할 것으로 예상됩니다. `find_active_groups()` 정도는 추후 서비스 레이어 작성 시 필요해질 수 있습니다.

### [SUGGEST-3] `product/repository.py` — `find_registered_products()` 대량 데이터 위험

```python
async def find_registered_products(self) -> List[Product]:
    return await self.filter_by_async(status=ProductStatusEnum.REGISTERED)
```

페이지네이션 없이 전체 반환합니다. 등록 상품이 수백~수천 건으로 늘어나면 메모리 및 응답 시간 문제가 발생합니다. 모니터링 스케줄러(`Task 11`)에서 이 메서드를 사용할 경우 배치 처리(`limit`, `offset`) 방식으로 교체를 고려하세요.

---

## Architecture Considerations

1. **BaseRepository 활용도 우수:** 모든 Repository가 raw `session.execute()` 직접 호출 없이 `find_by_async()`, `filter_by_async()` 등 BaseRepository 메서드를 일관되게 사용하고 있습니다. `user/repository.py` 기존 패턴과의 일관성도 유지됩니다.

2. **임포트 정리 상태 양호:** 각 파일이 필요한 모델과 Enum만 임포트하며, 미사용 임포트가 없습니다. 단 `product/repository.py`의 `Dict`, `Any` 누락은 ISSUE-1에서 지적한 대로 수정이 필요합니다.

3. **read/write session 분리 패턴:** `CLAUDE.md`에서 read/write session 분리를 요구하고 있으나, 현재 Repository 생성자는 `AsyncSession` 단일 파라미터만 받습니다. 이는 기존 `user/repository.py`와 동일한 패턴으로, session 분리는 서비스 또는 라우터 레이어의 `Depends()` 주입에서 처리하는 것으로 보입니다. Repository 레이어 자체는 문제 없습니다.

---

## Next Steps

1. **ISSUE-1 수정:** `product/repository.py` L1 임포트에 `Dict, Any` 추가, L46 타입 힌트 수정.
2. **ISSUE-2 검토:** `Notification` 모델에 `user_id` 또는 수신자 식별 컬럼이 있는지 `monitoring/model.py` 확인 후, 있다면 `find_unread()` 시그니처에 인자 추가.
3. Task 9 (서비스 레이어) 구현 시 `find_registered_products()` 대용량 처리 방안 결정.
