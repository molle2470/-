"""
브랜드(Brand) 도메인 Repository.
"""
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.shared.base_repository import BaseRepository
from backend.domain.brand.model import Brand


class BrandRepository(BaseRepository[Brand]):
    """브랜드 마스터 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Brand)

    async def find_by_name(self, name: str) -> Optional[Brand]:
        """브랜드명으로 조회"""
        return await self.find_by_async(name=name)

    async def find_approved_brands(self) -> List[Brand]:
        """지재권 승인된 브랜드 목록"""
        return await self.filter_by_async(is_ip_approved=True)
