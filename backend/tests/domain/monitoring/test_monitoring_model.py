import pytest
from backend.domain.monitoring.model import (
    PriceStockHistory, CrawlJob, Notification, CategoryMapping,
    ChangeTypeEnum, CrawlJobStatusEnum, NotificationTypeEnum,
)


def test_price_stock_history_model():
    h = PriceStockHistory(
        product_id=1,
        change_type=ChangeTypeEnum.PRICE_CHANGE,
        previous_value="100000",
        new_value="90000",
    )
    assert h.change_type == ChangeTypeEnum.PRICE_CHANGE
    assert h.previous_value == "100000"
    assert h.created_at is not None


def test_crawl_job_model():
    job = CrawlJob(source_id=1, source_url="https://musinsa.com/category/001")
    assert job.status == CrawlJobStatusEnum.PENDING
    assert job.target_count == 0
    assert job.collected_count == 0
    assert job.error_message is None


def test_notification_model():
    notif = Notification(
        notification_type=NotificationTypeEnum.OUT_OF_STOCK,
        product_id=1,
        message="나이키 에어맥스 90이 품절되었습니다.",
    )
    assert notif.is_read is False
    assert notif.notification_type == NotificationTypeEnum.OUT_OF_STOCK


def test_category_mapping_model():
    cm = CategoryMapping(
        source_id=1, source_category="스니커즈",
        market_id=1, market_category_id="50000803",
    )
    assert cm.confidence == 0.0
    assert cm.is_confirmed is False


def test_change_type_enum():
    assert ChangeTypeEnum.PRICE_CHANGE == "price_change"
    assert ChangeTypeEnum.OUT_OF_STOCK == "out_of_stock"
    assert ChangeTypeEnum.RESTOCKED == "restocked"


def test_crawl_job_status_enum():
    assert CrawlJobStatusEnum.PENDING == "pending"
    assert CrawlJobStatusEnum.IN_PROGRESS == "in_progress"
    assert CrawlJobStatusEnum.COMPLETED == "completed"
    assert CrawlJobStatusEnum.FAILED == "failed"


def test_notification_type_enum():
    assert NotificationTypeEnum.PRICE_CHANGE == "price_change"
    assert NotificationTypeEnum.OUT_OF_STOCK == "out_of_stock"
    assert NotificationTypeEnum.RESTOCKED == "restocked"
    assert NotificationTypeEnum.CRAWL_ERROR == "crawl_error"
    assert NotificationTypeEnum.MARKET_SYNC_ERROR == "market_sync_error"


def test_price_stock_history_requires_change_type():
    """change_type은 필수 필드"""
    from pydantic import ValidationError
    with pytest.raises((ValidationError, TypeError)):
        PriceStockHistory.model_validate({"product_id": 1})


def test_notification_requires_type():
    """notification_type은 필수 필드"""
    from pydantic import ValidationError
    with pytest.raises((ValidationError, TypeError)):
        Notification.model_validate({"message": "테스트"})
