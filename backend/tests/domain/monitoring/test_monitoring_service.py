"""
MonitoringService 단위 테스트.

DB 세션과 Repository를 AsyncMock으로 모킹하여
서비스 비즈니스 로직만 검증합니다.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.domain.monitoring.model import (
    ChangeTypeEnum,
    Notification,
    NotificationTypeEnum,
    PriceStockHistory,
)
from backend.domain.monitoring.service import MonitoringService


@pytest.mark.asyncio
async def test_record_price_change():
    """가격 변동 이력 기록"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.monitoring.service.PriceStockHistoryRepository"), \
         patch("backend.domain.monitoring.service.NotificationRepository"):

        service = MonitoringService(session)
        result = await service.record_price_change(
            product_id=1,
            previous_price="100000",
            new_price="120000",
        )

        session.add.assert_called_once()
        session.commit.assert_called_once()
        session.refresh.assert_called_once()

        assert isinstance(result, PriceStockHistory)
        assert result.product_id == 1
        assert result.change_type == ChangeTypeEnum.PRICE_CHANGE
        assert result.previous_value == "100000"
        assert result.new_value == "120000"


@pytest.mark.asyncio
async def test_record_stock_change_out_of_stock():
    """재고 소진 이력 기록"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.monitoring.service.PriceStockHistoryRepository"), \
         patch("backend.domain.monitoring.service.NotificationRepository"):

        service = MonitoringService(session)
        result = await service.record_stock_change(
            product_id=1,
            previous_status="in_stock",
            new_status="out_of_stock",
        )

        assert result.change_type == ChangeTypeEnum.OUT_OF_STOCK
        assert result.previous_value == "in_stock"
        assert result.new_value == "out_of_stock"


@pytest.mark.asyncio
async def test_record_stock_change_restocked():
    """재입고 이력 기록"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.monitoring.service.PriceStockHistoryRepository"), \
         patch("backend.domain.monitoring.service.NotificationRepository"):

        service = MonitoringService(session)
        result = await service.record_stock_change(
            product_id=1,
            previous_status="out_of_stock",
            new_status="in_stock",
        )

        assert result.change_type == ChangeTypeEnum.RESTOCKED
        assert result.new_value == "in_stock"


@pytest.mark.asyncio
async def test_create_notification():
    """알림 생성"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.monitoring.service.PriceStockHistoryRepository"), \
         patch("backend.domain.monitoring.service.NotificationRepository"):

        service = MonitoringService(session)
        result = await service.create_notification(
            notification_type=NotificationTypeEnum.PRICE_CHANGE,
            product_id=1,
            message="나이키 에어맥스 90 가격이 변동되었습니다: 100,000원 → 120,000원",
        )

        session.add.assert_called_once()
        session.commit.assert_called_once()
        session.refresh.assert_called_once()

        assert isinstance(result, Notification)
        assert result.notification_type == NotificationTypeEnum.PRICE_CHANGE
        assert result.product_id == 1
        assert result.is_read is False


@pytest.mark.asyncio
async def test_get_recent_history():
    """상품의 최근 변동 이력 조회"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.monitoring.service.PriceStockHistoryRepository") as MockHistRepo, \
         patch("backend.domain.monitoring.service.NotificationRepository"):

        mock_hist_repo = AsyncMock()
        MockHistRepo.return_value = mock_hist_repo

        expected = [
            PriceStockHistory(
                id=1,
                product_id=1,
                change_type=ChangeTypeEnum.PRICE_CHANGE,
                previous_value="100000",
                new_value="120000",
            )
        ]
        mock_hist_repo.find_by_product.return_value = expected

        service = MonitoringService(session)
        result = await service.get_recent_history(product_id=1, limit=10)

        mock_hist_repo.find_by_product.assert_called_once_with(product_id=1, limit=10)
        assert len(result) == 1
        assert result[0].change_type == ChangeTypeEnum.PRICE_CHANGE


@pytest.mark.asyncio
async def test_get_unread_notifications():
    """읽지 않은 알림 목록 조회"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.monitoring.service.PriceStockHistoryRepository"), \
         patch("backend.domain.monitoring.service.NotificationRepository") as MockNotifRepo:

        mock_notif_repo = AsyncMock()
        MockNotifRepo.return_value = mock_notif_repo

        expected = [
            Notification(
                id=1,
                notification_type=NotificationTypeEnum.OUT_OF_STOCK,
                product_id=1,
                message="재고 소진",
                is_read=False,
            )
        ]
        mock_notif_repo.find_unread.return_value = expected

        service = MonitoringService(session)
        result = await service.get_unread_notifications()

        mock_notif_repo.find_unread.assert_called_once()
        assert len(result) == 1
        assert result[0].is_read is False


@pytest.mark.asyncio
async def test_get_unread_notifications_empty():
    """읽지 않은 알림 없을 때 빈 리스트 반환"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.monitoring.service.PriceStockHistoryRepository"), \
         patch("backend.domain.monitoring.service.NotificationRepository") as MockNotifRepo:

        mock_notif_repo = AsyncMock()
        MockNotifRepo.return_value = mock_notif_repo
        mock_notif_repo.find_unread.return_value = []

        service = MonitoringService(session)
        result = await service.get_unread_notifications()

        assert result == []
