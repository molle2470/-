"""
마켓 판매가 자동 계산 서비스.

가격 공식: 판매가 = 원가 ÷ (1 - 마켓수수료 - 마진율)
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
