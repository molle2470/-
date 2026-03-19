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
