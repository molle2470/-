"""
마켓 판매가 자동 계산 서비스.

가격 공식: 판매가 = 실구매가 ÷ (1 - 마켓수수료 - 마진율)
실구매가: 정가 - 등급할인 - 적립금사용 (확정 혜택만 반영)
"""
import math


class PriceCalculator:
    """마켓 판매가 계산 서비스"""

    def calculate(self, original_price: int, commission_rate: float, margin_rate: float) -> int:
        """
        판매가 계산 (원 단위, 올림 처리)

        Args:
            original_price: 원가 (원)
            commission_rate: 마켓수수료 (예: 0.08 = 8%)
            margin_rate: 마진율 (예: 0.20 = 20%)

        Returns:
            판매가 (원, 올림)

        Raises:
            ValueError: 수수료 + 마진율 >= 100%인 경우
        """
        denominator = 1 - commission_rate - margin_rate
        if denominator <= 0:
            raise ValueError(
                f"수수료({commission_rate*100:.0f}%) + 마진율({margin_rate*100:.0f}%)이 "
                f"100% 이상입니다. 판매가를 계산할 수 없습니다."
            )
        return math.ceil(original_price / denominator)

    def calculate_margin_amount(
        self,
        original_price: int,
        selling_price: int,
        commission_rate: float,
    ) -> int:
        """
        실제 마진 금액 계산

        Args:
            original_price: 원가 (원)
            selling_price: 판매가 (원)
            commission_rate: 마켓수수료 (예: 0.08 = 8%)

        Returns:
            마진 금액 (원) = 판매가 - 원가 - 수수료
        """
        commission = math.ceil(selling_price * commission_rate)
        return selling_price - original_price - commission

    def calculate_with_grade_discount(
        self,
        original_price: int,
        base_discount_rate: float,
        point_use_limit: float,
        available_points: int,
        commission_rate: float,
        margin_rate: float,
        grade_discount_available: bool = True,
        point_usable: bool = True,
    ) -> int:
        """
        등급 할인 적용 판매가 계산.

        소싱처 계정 등급의 확정 혜택(기본 할인 + 적립금 사용)을
        반영한 실구매가를 기준으로 판매가를 산출합니다.
        상품별로 혜택 적용 가능 여부가 다르므로 플래그를 확인합니다.

        Args:
            original_price: 상품 정가 (원)
            base_discount_rate: 등급 기본 할인율 (예: 0.03 = 3%)
            point_use_limit: 적립금 사용 한도 비율 (예: 0.05 = 5%)
            available_points: 보유 적립금 (원)
            commission_rate: 마켓수수료 (예: 0.08 = 8%)
            margin_rate: 마진율 (예: 0.20 = 20%)
            grade_discount_available: 등급 할인 가능 여부 (상품별)
            point_usable: 적립금 사용 가능 여부 (상품별)

        Returns:
            판매가 (원, 올림)
        """
        discount = 0
        if grade_discount_available:
            discount = int(original_price * base_discount_rate)

        point_use = 0
        if point_usable:
            max_point_use = int(original_price * point_use_limit)
            point_use = min(available_points, max_point_use)

        effective_cost = original_price - discount - point_use
        return self.calculate(effective_cost, commission_rate, margin_rate)

    def can_fulfill_order(
        self,
        selling_price: int,
        current_cost: int,
        commission_rate: float,
    ) -> bool:
        """
        주문 처리 가능 여부 검증 (주문 시점 안전장치).

        판매가 이뤄졌을 때 현재 원가 기준으로 마진이 양수인지 확인합니다.
        마진 음수면 주문 처리 불가 (원가 상승으로 손해 발생).

        Args:
            selling_price: 판매가
            current_cost: 현재 실구매가 (주문 시점 실시간 원가)
            commission_rate: 마켓수수료

        Returns:
            True면 주문 처리 가능 (마진 > 0)
        """
        margin = self.calculate_margin_amount(current_cost, selling_price, commission_rate)
        return margin > 0
