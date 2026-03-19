"""
모니터링(Monitoring) 도메인 서비스 레이어.

가격/재고 변동 이력 기록, 알림 생성, 최근 이력 조회 등
모니터링 도메인 핵심 비즈니스 로직을 담당합니다.
"""
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.monitoring.model import (
    ChangeTypeEnum,
    Notification,
    NotificationTypeEnum,
    PriceStockHistory,
)
from backend.domain.product.model import StockStatusEnum
from backend.domain.monitoring.repository import (
    NotificationRepository,
    PriceStockHistoryRepository,
)


class MonitoringService:
    """모니터링 도메인 서비스"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.history_repo = PriceStockHistoryRepository(session)
        self.notification_repo = NotificationRepository(session)

    async def record_price_change(
        self,
        product_id: int,
        previous_price: str,
        new_price: str,
    ) -> PriceStockHistory:
        """
        가격 변동 이력 기록.

        Args:
            product_id: 상품 ID
            previous_price: 이전 가격 (문자열)
            new_price: 새 가격 (문자열)

        Returns:
            생성된 PriceStockHistory 객체
        """
        history = PriceStockHistory(
            product_id=product_id,
            change_type=ChangeTypeEnum.PRICE_CHANGE,
            previous_value=previous_price,
            new_value=new_price,
        )
        self.session.add(history)
        await self.session.commit()
        await self.session.refresh(history)
        return history

    async def record_stock_change(
        self,
        product_id: int,
        previous_status: StockStatusEnum,
        new_status: StockStatusEnum,
    ) -> PriceStockHistory:
        """
        재고 변동 이력 기록.

        재고 상태에 따라 OUT_OF_STOCK 또는 RESTOCKED 타입으로 기록합니다.

        Args:
            product_id: 상품 ID
            previous_status: 이전 재고 상태 (StockStatusEnum)
            new_status: 새 재고 상태 (StockStatusEnum)

        Returns:
            생성된 PriceStockHistory 객체
        """
        # 재고 상태에 따른 change_type 결정
        if new_status == StockStatusEnum.OUT_OF_STOCK:
            change_type = ChangeTypeEnum.OUT_OF_STOCK
        else:
            change_type = ChangeTypeEnum.RESTOCKED

        history = PriceStockHistory(
            product_id=product_id,
            change_type=change_type,
            previous_value=previous_status.value,
            new_value=new_status.value,
        )
        self.session.add(history)
        await self.session.commit()
        await self.session.refresh(history)
        return history

    async def create_notification(
        self,
        notification_type: NotificationTypeEnum,
        product_id: int,
        message: str,
    ) -> Notification:
        """
        알림 생성.

        Args:
            notification_type: 알림 종류
            product_id: 관련 상품 ID
            message: 알림 메시지

        Returns:
            생성된 Notification 객체
        """
        notification = Notification(
            notification_type=notification_type,
            product_id=product_id,
            message=message,
        )
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def get_recent_history(
        self,
        product_id: int,
        limit: int = 10,
    ) -> List[PriceStockHistory]:
        """
        상품의 최근 변동 이력 조회.

        Args:
            product_id: 상품 ID
            limit: 최대 반환 수 (기본값: 10)

        Returns:
            최신순 변동 이력 목록
        """
        return await self.history_repo.find_by_product(
            product_id=product_id,
            limit=limit,
        )

    async def get_unread_notifications(self) -> List[Notification]:
        """
        읽지 않은 알림 목록 조회.

        Returns:
            is_read=False인 알림 목록 (최신순)
        """
        return await self.notification_repo.find_unread()
