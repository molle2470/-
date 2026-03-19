"""MonitoringScheduler 단위 테스트.

APScheduler 기반 스마트 주기 모니터링 스케줄러 검증:
- 등급별 주기 계산 (HIGH/NORMAL)
- 상품 스케줄 등록/제거
- 가격 변동 감지 시 MarketSync 호출
- 크롤링 3회 실패 → 품절 처리
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from backend.services.scheduler import MonitoringScheduler


def test_scheduler_init():
    """스케줄러 초기화 상태 검증"""
    scheduler = MonitoringScheduler(
        session_factory=MagicMock(),
        crawler=MagicMock(),
        sync_adapter=MagicMock(),
    )
    assert scheduler._running is False


def test_get_interval_seconds_high_grade():
    """HIGH 등급: 480~1020초 범위 (10분-2분 ~ 15분+2분)"""
    scheduler = MonitoringScheduler(MagicMock(), MagicMock(), MagicMock())
    for _ in range(20):
        interval = scheduler._get_interval_seconds("high")
        assert 480 <= interval <= 1020, f"HIGH 등급 주기 범위 벗어남: {interval}"


def test_get_interval_seconds_normal_grade():
    """NORMAL 등급: 1500~3900초 범위 (30분-5분 ~ 60분+5분)"""
    scheduler = MonitoringScheduler(MagicMock(), MagicMock(), MagicMock())
    for _ in range(20):
        interval = scheduler._get_interval_seconds("normal")
        assert 1500 <= interval <= 3900, f"NORMAL 등급 주기 범위 벗어남: {interval}"


def test_get_interval_seconds_unknown_grade_defaults_to_normal():
    """알 수 없는 등급 → NORMAL 범위 기본 적용"""
    scheduler = MonitoringScheduler(MagicMock(), MagicMock(), MagicMock())
    interval = scheduler._get_interval_seconds("unknown")
    assert 1500 <= interval <= 3900


def test_schedule_product_adds_job():
    """상품 스케줄 등록 시 APScheduler에 job 추가"""
    scheduler = MonitoringScheduler(MagicMock(), MagicMock(), MagicMock())

    with patch.object(scheduler.scheduler, "add_job") as mock_add_job:
        scheduler.schedule_product(
            product_id=1,
            source_url="https://www.musinsa.com/app/goods/12345",
            grade="high",
        )
        mock_add_job.assert_called_once()
        # job_id가 상품 ID 기반인지 확인
        call_kwargs = mock_add_job.call_args
        assert call_kwargs.kwargs.get("id") == "product_1" or (
            len(call_kwargs.args) > 0 and "product_1" in str(call_kwargs)
        )


def test_unschedule_product_removes_job():
    """상품 스케줄 제거 시 APScheduler에서 job 삭제"""
    scheduler = MonitoringScheduler(MagicMock(), MagicMock(), MagicMock())

    with patch.object(scheduler.scheduler, "remove_job") as mock_remove_job:
        scheduler.unschedule_product(product_id=42)
        mock_remove_job.assert_called_once_with("product_42")


def test_start_sets_running_true():
    """start() 호출 시 _running=True"""
    scheduler = MonitoringScheduler(MagicMock(), MagicMock(), MagicMock())

    with patch.object(scheduler.scheduler, "start"):
        scheduler.start()
        assert scheduler._running is True


def test_stop_sets_running_false():
    """stop() 호출 시 _running=False"""
    scheduler = MonitoringScheduler(MagicMock(), MagicMock(), MagicMock())
    scheduler._running = True

    with patch.object(scheduler.scheduler, "shutdown"):
        scheduler.stop()
        assert scheduler._running is False


@pytest.mark.asyncio
async def test_monitor_product_price_change():
    """가격 변동 감지 시 MarketSyncService.sync_price_change 호출"""
    mock_session = AsyncMock()
    mock_session_factory = MagicMock()
    # context manager 지원
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session_factory.return_value = mock_ctx

    mock_crawler = AsyncMock()
    mock_adapter = MagicMock()

    # 크롤링 결과: 원가 변동 (기존 100000 → 90000)
    crawled_product = MagicMock()
    crawled_product.original_price = 90000
    crawled_product.stock_status = "in_stock"
    mock_crawler.check_product.return_value = crawled_product

    # 기존 DB 상품: 원가 100000, 재고 있음
    mock_product = MagicMock()
    mock_product.original_price = 100000
    from backend.domain.product.model import StockStatusEnum
    mock_product.stock_status = StockStatusEnum.IN_STOCK

    with (
        patch("backend.services.scheduler.ProductRepository") as MockProductRepo,
        patch("backend.services.scheduler.MarketSyncService") as MockSyncService,
    ):
        mock_repo = AsyncMock()
        MockProductRepo.return_value = mock_repo
        mock_repo.get_async.return_value = mock_product

        mock_sync = AsyncMock()
        MockSyncService.return_value = mock_sync
        mock_sync.sync_price_change.return_value = ["NAVER_123"]
        mock_sync.sync_stock_change.return_value = []

        scheduler = MonitoringScheduler(mock_session_factory, mock_crawler, mock_adapter)
        await scheduler.monitor_product(
            product_id=1,
            source_url="https://www.musinsa.com/app/goods/12345",
        )

        # 가격 변동이므로 sync_price_change 호출 확인
        mock_sync.sync_price_change.assert_called_once_with(
            product_id=1,
            new_price=90000,
            commission_rate=0.05,
            margin_rate=0.20,
        )
        # 재고 상태는 동일하므로 sync_stock_change 미호출
        mock_sync.sync_stock_change.assert_not_called()


@pytest.mark.asyncio
async def test_monitor_product_stock_change():
    """재고 변동 감지 시 MarketSyncService.sync_stock_change 호출"""
    mock_session = AsyncMock()
    mock_session_factory = MagicMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session_factory.return_value = mock_ctx

    mock_crawler = AsyncMock()
    mock_adapter = MagicMock()

    # 크롤링 결과: 품절
    crawled_product = MagicMock()
    crawled_product.original_price = 100000
    crawled_product.stock_status = "out_of_stock"
    mock_crawler.check_product.return_value = crawled_product

    # 기존 DB 상품: 재고 있음
    mock_product = MagicMock()
    mock_product.original_price = 100000
    from backend.domain.product.model import StockStatusEnum
    mock_product.stock_status = StockStatusEnum.IN_STOCK

    with (
        patch("backend.services.scheduler.ProductRepository") as MockProductRepo,
        patch("backend.services.scheduler.MarketSyncService") as MockSyncService,
    ):
        mock_repo = AsyncMock()
        MockProductRepo.return_value = mock_repo
        mock_repo.get_async.return_value = mock_product

        mock_sync = AsyncMock()
        MockSyncService.return_value = mock_sync
        mock_sync.sync_price_change.return_value = []
        mock_sync.sync_stock_change.return_value = ["NAVER_123"]

        scheduler = MonitoringScheduler(mock_session_factory, mock_crawler, mock_adapter)
        await scheduler.monitor_product(
            product_id=1,
            source_url="https://www.musinsa.com/app/goods/12345",
        )

        # 가격 변동 없으므로 sync_price_change 미호출
        mock_sync.sync_price_change.assert_not_called()
        # 재고 변동이므로 sync_stock_change 호출 확인
        mock_sync.sync_stock_change.assert_called_once_with(
            product_id=1,
            in_stock=False,
        )


@pytest.mark.asyncio
async def test_monitor_product_crawl_failure_marks_out_of_stock():
    """크롤링 3회 실패 → 품절 처리"""
    mock_session = AsyncMock()
    mock_session_factory = MagicMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session_factory.return_value = mock_ctx

    mock_crawler = AsyncMock()
    mock_adapter = MagicMock()

    # 3회 모두 크롤링 실패 (None 반환)
    mock_crawler.check_product.return_value = None

    # 기존 DB 상품: 재고 있음
    mock_product = MagicMock()
    mock_product.original_price = 100000
    from backend.domain.product.model import StockStatusEnum
    mock_product.stock_status = StockStatusEnum.IN_STOCK

    with (
        patch("backend.services.scheduler.ProductRepository") as MockProductRepo,
        patch("backend.services.scheduler.MarketSyncService") as MockSyncService,
    ):
        mock_repo = AsyncMock()
        MockProductRepo.return_value = mock_repo
        mock_repo.get_async.return_value = mock_product

        mock_sync = AsyncMock()
        MockSyncService.return_value = mock_sync
        mock_sync.sync_stock_change.return_value = ["NAVER_123"]

        scheduler = MonitoringScheduler(mock_session_factory, mock_crawler, mock_adapter)
        await scheduler.monitor_product(
            product_id=1,
            source_url="https://www.musinsa.com/app/goods/12345",
        )

        # 크롤러가 정확히 3회 호출되었는지 확인
        assert mock_crawler.check_product.call_count == 3

        # 3회 실패 → 품절 처리 확인
        mock_sync.sync_stock_change.assert_called_once_with(
            product_id=1,
            in_stock=False,
        )


@pytest.mark.asyncio
async def test_monitor_product_not_found_returns_early():
    """DB에서 상품 조회 실패 시 조기 반환 (에러 없음)"""
    mock_session = AsyncMock()
    mock_session_factory = MagicMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session_factory.return_value = mock_ctx

    mock_crawler = AsyncMock()
    mock_crawler.check_product.return_value = MagicMock(
        original_price=100000,
        stock_status="in_stock",
    )
    mock_adapter = MagicMock()

    with (
        patch("backend.services.scheduler.ProductRepository") as MockProductRepo,
        patch("backend.services.scheduler.MarketSyncService") as MockSyncService,
    ):
        mock_repo = AsyncMock()
        MockProductRepo.return_value = mock_repo
        # DB에 상품 없음
        mock_repo.get_async.return_value = None

        mock_sync = AsyncMock()
        MockSyncService.return_value = mock_sync

        scheduler = MonitoringScheduler(mock_session_factory, mock_crawler, mock_adapter)
        # 예외 없이 정상 종료 확인
        await scheduler.monitor_product(product_id=999, source_url="https://example.com/goods/999")

        # sync 메서드 미호출 확인
        mock_sync.sync_price_change.assert_not_called()
        mock_sync.sync_stock_change.assert_not_called()
