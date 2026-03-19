"""
소싱처(Source) 및 브랜드(Brand) 모델 단위 테스트.

DB 연결 없이 모델 인스턴스 생성만 검증합니다.
"""
from backend.domain.source.model import (
    AccountRoleEnum,
    Source,
    SourceAccount,
    SourceBrand,
)
from backend.domain.brand.model import Brand


def test_source_model_exists():
    """Source 모델 인스턴스 생성 및 필드 검증"""
    source = Source(
        name="무신사",
        base_url="https://www.musinsa.com",
        crawler_type="musinsa"
    )
    assert source.name == "무신사"
    assert source.crawler_type == "musinsa"
    assert source.is_active is True  # 기본값 검증
    assert source.created_at is not None  # default_factory로 즉시 값 설정


def test_brand_model_exists():
    """Brand 모델 인스턴스 생성 및 필드 검증"""
    brand = Brand(name="나이키")
    assert brand.name == "나이키"
    assert brand.is_ip_approved is False  # 기본값 검증


def test_source_brand_model_exists():
    """SourceBrand 모델 인스턴스 생성 및 필드 검증"""
    sb = SourceBrand(brand_id=1, source_id=1, display_name="NIKE")
    assert sb.display_name == "NIKE"
    assert sb.created_at is not None  # default_factory로 즉시 값 설정
    assert sb.updated_at is not None  # updated_at 필드 추가 검증


# --- SourceAccount 모델 테스트 ---


def test_source_account_model_creation():
    """SourceAccount 모델 인스턴스 생성 및 기본값 검증"""
    account = SourceAccount(
        source_id=1,
        account_name="무신사 계정1",
        grade="블루",
        base_discount_rate=0.03,
        point_rate=0.01,
        point_use_limit=0.05,
        available_points=5000,
        role=AccountRoleEnum.PRICE_BASE,
    )
    assert account.account_name == "무신사 계정1"
    assert account.grade == "블루"
    assert account.base_discount_rate == 0.03
    assert account.role == AccountRoleEnum.PRICE_BASE
    assert account.is_active is True


def test_source_account_defaults():
    """SourceAccount 기본값 확인"""
    account = SourceAccount(
        source_id=1,
        account_name="테스트",
        grade="화이트",
    )
    assert account.base_discount_rate == 0.0
    assert account.point_rate == 0.0
    assert account.point_use_limit == 0.0
    assert account.available_points == 0
    assert account.role == AccountRoleEnum.MONITOR


def test_source_account_effective_cost_with_discount_only():
    """등급 할인만 적용 (적립금 0)"""
    account = SourceAccount(
        source_id=1,
        account_name="블루",
        grade="블루",
        base_discount_rate=0.03,
        point_use_limit=0.05,
        available_points=0,  # 적립금 없음
    )
    # 100,000 * 0.03 = 3,000원 할인
    cost = account.calculate_effective_cost(100000)
    assert cost == 97000


def test_source_account_effective_cost_with_points():
    """등급 할인 + 적립금 사용"""
    account = SourceAccount(
        source_id=1,
        account_name="레드",
        grade="레드",
        base_discount_rate=0.05,
        point_use_limit=0.10,
        available_points=20000,
    )
    # 할인: 100,000 * 0.05 = 5,000
    # 적립금 한도: 100,000 * 0.10 = 10,000 (보유 20,000 중 10,000 사용)
    # 실구매가: 100,000 - 5,000 - 10,000 = 85,000
    cost = account.calculate_effective_cost(100000)
    assert cost == 85000


def test_source_account_effective_cost_points_capped():
    """적립금이 한도보다 적을 때"""
    account = SourceAccount(
        source_id=1,
        account_name="블루",
        grade="블루",
        base_discount_rate=0.03,
        point_use_limit=0.10,
        available_points=3000,  # 한도(10,000)보다 적음
    )
    # 할인: 100,000 * 0.03 = 3,000
    # 적립금 한도: 100,000 * 0.10 = 10,000, 보유 3,000 → 3,000 사용
    # 실구매가: 100,000 - 3,000 - 3,000 = 94,000
    cost = account.calculate_effective_cost(100000)
    assert cost == 94000


def test_source_account_effective_cost_no_grade_discount():
    """등급 할인 불가 상품 (무신사 아울렛 등)"""
    account = SourceAccount(
        source_id=1,
        account_name="레드",
        grade="레드",
        base_discount_rate=0.05,
        point_use_limit=0.10,
        available_points=20000,
    )
    # 등급 할인 불가 → 할인 0, 적립금도 사용 불가
    # 실구매가 = 정가 그대로
    cost = account.calculate_effective_cost(
        100000, grade_discount_available=False, point_usable=False
    )
    assert cost == 100000


def test_source_account_effective_cost_no_discount_but_point_ok():
    """등급 할인 불가 + 적립금 사용 가능"""
    account = SourceAccount(
        source_id=1,
        account_name="블루",
        grade="블루",
        base_discount_rate=0.03,
        point_use_limit=0.05,
        available_points=10000,
    )
    # 등급 할인 불가 → 할인 0
    # 적립금 사용 가능 → 한도: 100,000 * 0.05 = 5,000
    # 실구매가: 100,000 - 0 - 5,000 = 95,000
    cost = account.calculate_effective_cost(
        100000, grade_discount_available=False, point_usable=True
    )
    assert cost == 95000


def test_account_role_enum_values():
    """AccountRoleEnum 값 확인"""
    assert AccountRoleEnum.PRICE_BASE == "price_base"
    assert AccountRoleEnum.PRIMARY_BUYER == "primary_buyer"
    assert AccountRoleEnum.BACKUP == "backup"
    assert AccountRoleEnum.MONITOR == "monitor"
