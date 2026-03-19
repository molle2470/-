"""
모니터링(Monitoring) 도메인 Repository.
"""
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.shared.base_repository import BaseRepository
from backend.domain.monitoring.model import (
    CategoryMapping,
    CrawlJob,
    CrawlJobStatusEnum,
    Notification,
    PriceStockHistory,
)


class PriceStockHistoryRepository(BaseRepository[PriceStockHistory]):
    """가격/재고 변동 이력 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, PriceStockHistory)

    async def find_by_product(
        self, product_id: int, limit: int = 50
    ) -> List[PriceStockHistory]:
        """상품별 변동 이력 조회 (최신순)"""
        return await self.filter_by_async(
            product_id=product_id,
            limit=limit,
            order_by="created_at",
            order_by_desc=True,
        )


class CrawlJobRepository(BaseRepository[CrawlJob]):
    """크롤링 작업 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, CrawlJob)

    async def find_pending_jobs(self) -> List[CrawlJob]:
        """대기 중인 크롤링 작업 목록"""
        return await self.filter_by_async(status=CrawlJobStatusEnum.PENDING)

    async def find_in_progress_jobs(self) -> List[CrawlJob]:
        """진행 중인 크롤링 작업 목록"""
        return await self.filter_by_async(status=CrawlJobStatusEnum.IN_PROGRESS)


class NotificationRepository(BaseRepository[Notification]):
    """알림 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Notification)

    async def find_unread(self, limit: int = 20) -> List[Notification]:
        """읽지 않은 알림 목록 (최신순)"""
        return await self.filter_by_async(
            is_read=False,
            limit=limit,
            order_by="created_at",
            order_by_desc=True,
        )


class CategoryMappingRepository(BaseRepository[CategoryMapping]):
    """소싱처-마켓 카테고리 매핑 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, CategoryMapping)

    async def find_by_source_category(
        self, source_id: int, source_category: str
    ) -> Optional[CategoryMapping]:
        """소싱처 + 원본 카테고리로 매핑 조회"""
        return await self.find_by_async(
            source_id=source_id, source_category=source_category
        )

    async def find_confirmed_mappings(self, source_id: int) -> List[CategoryMapping]:
        """수동 확인된 카테고리 매핑 목록"""
        return await self.filter_by_async(source_id=source_id, is_confirmed=True)
