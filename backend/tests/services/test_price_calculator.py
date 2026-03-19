import math
import pytest
from backend.services.price_calculator import PriceCalculator


def test_calculate_selling_price():
    """판매가 = 원가 ÷ (1 - 마켓수수료 - 마진율), 올림 처리"""
    calc = PriceCalculator()
    # 원가 50,000 / (1 - 0.08 - 0.20) = 50000 / 0.72 = 69444.4 → 69445
    price = calc.calculate(original_price=50000, commission_rate=0.08, margin_rate=0.20)
    assert price == 69445


def test_calculate_coupang_price():
    """쿠팡 수수료 15%"""
    calc = PriceCalculator()
    # 50000 / (1 - 0.15 - 0.20) = 50000 / 0.65 = 76923.07 → 76924
    price = calc.calculate(original_price=50000, commission_rate=0.15, margin_rate=0.20)
    assert price == 76924


def test_price_change_recalculation():
    """원가 변동 시 재계산"""
    calc = PriceCalculator()
    old = calc.calculate(original_price=50000, commission_rate=0.08, margin_rate=0.20)
    new = calc.calculate(original_price=45000, commission_rate=0.08, margin_rate=0.20)
    assert new < old
    # 45000 / 0.72 = 62500.0 → 62500
    assert new == 62500


def test_margin_change_recalculation():
    """마진율 변경 시 재계산"""
    calc = PriceCalculator()
    old = calc.calculate(original_price=50000, commission_rate=0.08, margin_rate=0.20)
    new = calc.calculate(original_price=50000, commission_rate=0.08, margin_rate=0.25)
    assert new > old


def test_invalid_rates_raise_error():
    """수수료 + 마진율 >= 100%인 경우 ValueError"""
    calc = PriceCalculator()
    with pytest.raises(ValueError):
        calc.calculate(original_price=50000, commission_rate=0.60, margin_rate=0.50)


def test_calculate_margin_amount():
    """실제 마진 금액 계산"""
    calc = PriceCalculator()
    # 판매가 69445, 원가 50000, 수수료 8%
    margin = calc.calculate_margin_amount(
        original_price=50000,
        selling_price=69445,
        commission_rate=0.08,
    )
    # 69445 - 50000 - ceil(69445 * 0.08) = 69445 - 50000 - 5556 = 13889
    assert margin == 13889


def test_zero_commission_rate():
    """수수료 0%인 경우"""
    calc = PriceCalculator()
    # 50000 / (1 - 0.0 - 0.20) = 50000 / 0.80 = 62500
    price = calc.calculate(original_price=50000, commission_rate=0.0, margin_rate=0.20)
    assert price == 62500


# --- 등급 할인 적용 판매가 계산 테스트 ---


def test_calculate_with_grade_discount_basic():
    """중간 등급(블루 3%) 할인 적용 판매가 계산"""
    calc = PriceCalculator()
    # 정가 100,000 → 할인 3,000 → 실구매가 97,000 (적립금 없음)
    # 97,000 / (1 - 0.08 - 0.20) = 97,000 / 0.72 = 134,722.2 → 134,723
    price = calc.calculate_with_grade_discount(
        original_price=100000,
        base_discount_rate=0.03,
        point_use_limit=0.05,
        available_points=0,
        commission_rate=0.08,
        margin_rate=0.20,
    )
    assert price == 134723


def test_calculate_with_grade_discount_and_points():
    """등급 할인 + 적립금 사용 적용"""
    calc = PriceCalculator()
    # 정가 100,000 → 할인 5,000 → 적립금 한도 10,000 (보유 20,000) → 실구매가 85,000
    # 85,000 / 0.72 = 118,055.5 → 118,056
    price = calc.calculate_with_grade_discount(
        original_price=100000,
        base_discount_rate=0.05,
        point_use_limit=0.10,
        available_points=20000,
        commission_rate=0.08,
        margin_rate=0.20,
    )
    assert price == 118056


def test_calculate_with_grade_discount_no_benefits():
    """혜택 불가 상품 (등급 할인 X, 적립금 X) → 정가 기준 판매가"""
    calc = PriceCalculator()
    # 등급 할인 불가, 적립금 불가 → 실구매가 = 정가 100,000
    # 100,000 / 0.72 = 138,888.8 → 138,889
    price = calc.calculate_with_grade_discount(
        original_price=100000,
        base_discount_rate=0.05,  # 이 값은 무시됨
        point_use_limit=0.10,    # 이 값도 무시됨
        available_points=20000,
        commission_rate=0.08,
        margin_rate=0.20,
        grade_discount_available=False,
        point_usable=False,
    )
    assert price == 138889


def test_calculate_with_grade_discount_partial_benefits():
    """등급 할인 불가 + 적립금 사용 가능"""
    calc = PriceCalculator()
    # 등급 할인 불가 → 할인 0
    # 적립금 사용 가능 → 한도: 100,000 * 0.10 = 10,000, 보유 20,000 → 10,000 사용
    # 실구매가: 100,000 - 0 - 10,000 = 90,000
    # 90,000 / 0.72 = 125,000
    price = calc.calculate_with_grade_discount(
        original_price=100000,
        base_discount_rate=0.05,
        point_use_limit=0.10,
        available_points=20000,
        commission_rate=0.08,
        margin_rate=0.20,
        grade_discount_available=False,
        point_usable=True,
    )
    assert price == 125000


def test_can_fulfill_order_positive_margin():
    """마진 양수 → 주문 처리 가능"""
    calc = PriceCalculator()
    # 판매가 134,723, 현재 원가 97,500, 수수료 8%
    assert calc.can_fulfill_order(134723, 97500, 0.08) is True


def test_can_fulfill_order_negative_margin():
    """마진 음수 → 주문 처리 불가 (원가 상승으로 손해)"""
    calc = PriceCalculator()
    # 판매가 90,000, 현재 원가 95,000 → 주문하면 손해
    assert calc.can_fulfill_order(90000, 95000, 0.08) is False
