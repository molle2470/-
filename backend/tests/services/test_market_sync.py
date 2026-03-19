"""
마켓 동기화 서비스 테스트.

원가/재고 변동 → 마켓 자동 반영 로직 검증.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# MarketSyncService import는 구현 후 활성화
from backend.services.market_sync import MarketSyncService


@pytest.mark.asyncio
async def test_sync_price_change_updates_listings():
    """가격 변동 시 마켓 등록 상품 가격 업데이트"""
    session = AsyncMock()
    adapter = AsyncMock()
    adapter.update_price.return_value = True

    with patch("backend.services.market_sync.MarketListingRepository") as MockRepo:
        mock_listing = MagicMock()
        mock_listing.product_id = 1
        mock_listing.market_product_id = "NAVER_123"
        mock_listing.selling_price = 100000

        mock_repo = AsyncMock()
        MockRepo.return_value = mock_repo
        mock_repo.filter_by_async.return_value = [mock_listing]

        service = MarketSyncService(session, adapter)
        updated = await service.sync_price_change(
            product_id=1,
            new_price=90000,
            commission_rate=0.05,
            margin_rate=0.20,
        )

        assert len(updated) == 1
        assert updated[0] == "NAVER_123"
        adapter.update_price.assert_called_once_with("NAVER_123", 120000)


@pytest.mark.asyncio
async def test_sync_price_change_no_listings():
    """마켓 등록 없으면 빈 리스트 반환"""
    session = AsyncMock()
    adapter = AsyncMock()

    with patch("backend.services.market_sync.MarketListingRepository") as MockRepo:
        mock_repo = AsyncMock()
        MockRepo.return_value = mock_repo
        mock_repo.filter_by_async.return_value = []

        service = MarketSyncService(session, adapter)
        updated = await service.sync_price_change(
            product_id=999,
            new_price=50000,
            commission_rate=0.05,
            margin_rate=0.20,
        )

        assert updated == []
        adapter.update_price.assert_not_called()


@pytest.mark.asyncio
async def test_sync_price_change_skips_listing_without_market_product_id():
    """market_product_id 없는 리스팅은 건너뜀"""
    session = AsyncMock()
    adapter = AsyncMock()

    with patch("backend.services.market_sync.MarketListingRepository") as MockRepo:
        # market_product_id가 None인 리스팅
        mock_listing = MagicMock()
        mock_listing.market_product_id = None

        mock_repo = AsyncMock()
        MockRepo.return_value = mock_repo
        mock_repo.filter_by_async.return_value = [mock_listing]

        service = MarketSyncService(session, adapter)
        updated = await service.sync_price_change(
            product_id=1,
            new_price=80000,
            commission_rate=0.05,
            margin_rate=0.20,
        )

        assert updated == []
        adapter.update_price.assert_not_called()


@pytest.mark.asyncio
async def test_sync_stock_change_out_of_stock():
    """재고 없음 처리 - 품절 동기화"""
    session = AsyncMock()
    adapter = AsyncMock()
    adapter.update_stock.return_value = True

    with patch("backend.services.market_sync.MarketListingRepository") as MockRepo:
        mock_listing = MagicMock()
        mock_listing.market_product_id = "NAVER_456"

        mock_repo = AsyncMock()
        MockRepo.return_value = mock_repo
        mock_repo.filter_by_async.return_value = [mock_listing]

        service = MarketSyncService(session, adapter)
        updated = await service.sync_stock_change(product_id=1, in_stock=False)

        assert len(updated) == 1
        assert updated[0] == "NAVER_456"
        # 품절 처리 호출 확인
        adapter.update_stock.assert_called_once_with("NAVER_456", False)


@pytest.mark.asyncio
async def test_sync_stock_change_back_in_stock():
    """재고 복구 처리 - 재활성화 동기화"""
    session = AsyncMock()
    adapter = AsyncMock()
    adapter.update_stock.return_value = True

    with patch("backend.services.market_sync.MarketListingRepository") as MockRepo:
        mock_listing = MagicMock()
        mock_listing.market_product_id = "NAVER_789"

        mock_repo = AsyncMock()
        MockRepo.return_value = mock_repo
        mock_repo.filter_by_async.return_value = [mock_listing]

        service = MarketSyncService(session, adapter)
        updated = await service.sync_stock_change(product_id=1, in_stock=True)

        assert updated == ["NAVER_789"]
        adapter.update_stock.assert_called_once_with("NAVER_789", True)


@pytest.mark.asyncio
async def test_sync_stock_change_adapter_failure():
    """어댑터 실패 시 해당 항목 제외"""
    session = AsyncMock()
    adapter = AsyncMock()
    # 첫 번째는 성공, 두 번째는 실패
    adapter.update_stock.side_effect = [True, False]

    with patch("backend.services.market_sync.MarketListingRepository") as MockRepo:
        mock_listing1 = MagicMock()
        mock_listing1.market_product_id = "NAVER_001"
        mock_listing2 = MagicMock()
        mock_listing2.market_product_id = "NAVER_002"

        mock_repo = AsyncMock()
        MockRepo.return_value = mock_repo
        mock_repo.filter_by_async.return_value = [mock_listing1, mock_listing2]

        service = MarketSyncService(session, adapter)
        updated = await service.sync_stock_change(product_id=1, in_stock=False)

        # 성공한 항목만 반환
        assert updated == ["NAVER_001"]
        assert len(updated) == 1


@pytest.mark.asyncio
async def test_sync_price_change_commits_on_success():
    """가격 업데이트 성공 시 session.commit 호출"""
    session = AsyncMock()
    adapter = AsyncMock()
    adapter.update_price.return_value = True

    with patch("backend.services.market_sync.MarketListingRepository") as MockRepo:
        mock_listing = MagicMock()
        mock_listing.market_product_id = "NAVER_123"
        mock_listing.selling_price = 100000

        mock_repo = AsyncMock()
        MockRepo.return_value = mock_repo
        mock_repo.filter_by_async.return_value = [mock_listing]

        service = MarketSyncService(session, adapter)
        await service.sync_price_change(
            product_id=1,
            new_price=90000,
            commission_rate=0.05,
            margin_rate=0.20,
        )

        session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_sync_price_change_no_commit_when_no_updates():
    """업데이트 없으면 commit 호출 안 함"""
    session = AsyncMock()
    adapter = AsyncMock()

    with patch("backend.services.market_sync.MarketListingRepository") as MockRepo:
        mock_repo = AsyncMock()
        MockRepo.return_value = mock_repo
        mock_repo.filter_by_async.return_value = []

        service = MarketSyncService(session, adapter)
        await service.sync_price_change(
            product_id=1,
            new_price=90000,
            commission_rate=0.05,
            margin_rate=0.20,
        )

        session.commit.assert_not_called()
