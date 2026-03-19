"""
소싱처(Source) 도메인 Repository.
"""
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.shared.base_repository import BaseRepository
from backend.domain.source.model import Source, SourceBrand


class SourceRepository(BaseRepository[Source]):
    """소싱처 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Source)

    async def find_by_name(self, name: str) -> Optional[Source]:
        """소싱처 이름으로 조회"""
        return await self.find_by_async(name=name)

    async def find_active_sources(self) -> List[Source]:
        """활성화된 소싱처 목록"""
        return await self.filter_by_async(is_active=True)


class SourceBrandRepository(BaseRepository[SourceBrand]):
    """소싱처별 브랜드 매핑 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, SourceBrand)

    async def find_by_source_and_brand(
        self, source_id: int, brand_id: int
    ) -> Optional[SourceBrand]:
        """소싱처+브랜드 조합으로 조회"""
        return await self.find_by_async(source_id=source_id, brand_id=brand_id)

    async def find_by_source(self, source_id: int) -> List[SourceBrand]:
        """소싱처별 브랜드 목록"""
        return await self.filter_by_async(source_id=source_id)
