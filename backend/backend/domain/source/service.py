"""
소싱처(Source) 도메인 서비스 레이어.

활성 소싱처 목록 조회, 소싱처별 브랜드 목록 조회, 소싱처 생성 등
소싱처 도메인 핵심 비즈니스 로직을 담당합니다.
"""
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.source.model import Source, SourceBrand
from backend.domain.source.repository import SourceBrandRepository, SourceRepository


class SourceService:
    """소싱처 도메인 서비스"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SourceRepository(session)
        self.source_brand_repo = SourceBrandRepository(session)

    async def get_active_sources(self) -> List[Source]:
        """
        활성 소싱처 목록 조회.

        Returns:
            is_active=True인 소싱처 목록
        """
        return await self.repo.find_active_sources()

    async def get_source_brands(self, source_id: int) -> List[SourceBrand]:
        """
        소싱처의 브랜드 목록 조회.

        Args:
            source_id: 소싱처 ID

        Returns:
            해당 소싱처에 등록된 SourceBrand 목록
        """
        return await self.source_brand_repo.find_by_source(source_id=source_id)

    async def create_source(
        self,
        name: str,
        base_url: str,
        crawler_type: str = "generic",
    ) -> Source:
        """
        소싱처 생성.

        Args:
            name: 소싱처 이름 (예: 무신사)
            base_url: 소싱처 기본 URL
            crawler_type: 크롤러 타입 식별자 (기본값: generic)

        Returns:
            생성된 Source 객체
        """
        source = Source(
            name=name,
            base_url=base_url,
            crawler_type=crawler_type,
        )
        self.session.add(source)
        await self.session.commit()
        await self.session.refresh(source)
        return source
