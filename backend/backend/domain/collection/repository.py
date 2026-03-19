"""수집 도메인 Repository."""
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.shared.base_repository import BaseRepository
from backend.domain.collection.model import (
    CollectionSetting,
    CollectionLog,
    ExtensionCommand,
    CommandStatusEnum,
)


class CollectionSettingRepository(BaseRepository[CollectionSetting]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, CollectionSetting)

    async def find_active_settings(self) -> List[CollectionSetting]:
        """활성 수집 설정 목록"""
        return await self.filter_by_async(is_active=True)


class CollectionLogRepository(BaseRepository[CollectionLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, CollectionLog)


class ExtensionCommandRepository(BaseRepository[ExtensionCommand]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ExtensionCommand)

    async def find_pending_commands(self) -> List[ExtensionCommand]:
        """대기 중인 명령 조회 (익스텐션 폴링용)"""
        return await self.filter_by_async(status=CommandStatusEnum.PENDING)
