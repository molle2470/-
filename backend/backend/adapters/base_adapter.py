"""마켓 API 어댑터 공통 인터페이스.

모든 마켓(쿠팡, 네이버 스마트스토어 등) 어댑터의 기반 추상 클래스.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional


class BaseMarketAdapter(ABC):
    """마켓 API 어댑터 공통 인터페이스

    모든 마켓 어댑터는 이 클래스를 상속받아 구현합니다.
    """

    @abstractmethod
    async def register_product(self, product_data: Dict[str, object]) -> Optional[str]:
        """상품 등록, 마켓 상품 ID 반환"""
        ...

    @abstractmethod
    async def update_price(self, market_product_id: str, new_price: int) -> bool:
        """가격 수정"""
        ...

    @abstractmethod
    async def update_stock(self, market_product_id: str, in_stock: bool) -> bool:
        """재고/품절 처리"""
        ...

    @abstractmethod
    async def deactivate_product(self, market_product_id: str) -> bool:
        """상품 비활성화"""
        ...
