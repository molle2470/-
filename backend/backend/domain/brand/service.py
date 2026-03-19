"""
브랜드(Brand) 도메인 서비스 레이어.

브랜드 조회/생성, 브랜드 목록, IP 승인 브랜드 조회 등
브랜드 도메인 핵심 비즈니스 로직을 담당합니다.
"""
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.brand.model import Brand
from backend.domain.brand.repository import BrandRepository


class BrandService:
    """브랜드 도메인 서비스"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BrandRepository(session)

    async def find_or_create(self, brand_name: str) -> Brand:
        """
        브랜드명으로 조회하고, 없으면 새로 생성.

        소싱처에서 수집된 브랜드명으로 브랜드 마스터를 조회하고,
        존재하지 않으면 새 브랜드를 생성합니다.

        Args:
            brand_name: 브랜드명

        Returns:
            조회되거나 생성된 Brand 객체
        """
        existing = await self.repo.find_by_name(name=brand_name)
        if existing is not None:
            return existing

        brand = Brand(name=brand_name)
        self.session.add(brand)
        await self.session.commit()
        await self.session.refresh(brand)
        return brand

    async def list_brands(self, skip: int = 0, limit: int = 20) -> List[Brand]:
        """
        브랜드 목록 조회.

        Args:
            skip: 건너뛸 레코드 수
            limit: 최대 반환 수

        Returns:
            브랜드 목록
        """
        return await self.repo.list_async(skip=skip, limit=limit)

    async def get_approved_brands(self) -> List[Brand]:
        """
        IP(지재권) 승인된 브랜드 목록 조회.

        지재권 이슈가 없어 소싱/판매 가능한 브랜드만 반환합니다.

        Returns:
            is_ip_approved=True인 브랜드 목록
        """
        return await self.repo.find_approved_brands()
