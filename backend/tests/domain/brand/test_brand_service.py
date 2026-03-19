"""
BrandService 단위 테스트.

DB 세션과 Repository를 AsyncMock으로 모킹하여
서비스 비즈니스 로직만 검증합니다.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.domain.brand.model import Brand
from backend.domain.brand.service import BrandService


@pytest.mark.asyncio
async def test_find_or_create_brand_new():
    """새 브랜드 생성: 존재하지 않는 브랜드명이면 생성"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.brand.service.BrandRepository") as MockRepo:
        mock_repo = AsyncMock()
        MockRepo.return_value = mock_repo
        mock_repo.find_by_name.return_value = None

        service = BrandService(session)
        result = await service.find_or_create("나이키")

        session.add.assert_called_once()
        session.commit.assert_called_once()
        session.refresh.assert_called_once()

        assert isinstance(result, Brand)
        assert result.name == "나이키"


@pytest.mark.asyncio
async def test_find_or_create_brand_existing():
    """기존 브랜드 반환: 이미 존재하는 브랜드명이면 기존 것 반환"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.brand.service.BrandRepository") as MockRepo:
        mock_repo = AsyncMock()
        MockRepo.return_value = mock_repo

        existing_brand = Brand(id=5, name="나이키", is_ip_approved=True)
        mock_repo.find_by_name.return_value = existing_brand

        service = BrandService(session)
        result = await service.find_or_create("나이키")

        # 기존 브랜드 반환
        assert result.id == 5
        # DB 저장 없어야 함
        session.add.assert_not_called()
        session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_list_brands():
    """브랜드 목록 조회"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.brand.service.BrandRepository") as MockRepo:
        mock_repo = AsyncMock()
        MockRepo.return_value = mock_repo

        expected = [
            Brand(id=1, name="나이키"),
            Brand(id=2, name="아디다스"),
        ]
        mock_repo.list_async.return_value = expected

        service = BrandService(session)
        result = await service.list_brands(skip=0, limit=20)

        mock_repo.list_async.assert_called_once_with(skip=0, limit=20)
        assert len(result) == 2
        assert result[0].name == "나이키"


@pytest.mark.asyncio
async def test_get_approved_brands():
    """IP 승인된 브랜드만 반환"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.brand.service.BrandRepository") as MockRepo:
        mock_repo = AsyncMock()
        MockRepo.return_value = mock_repo

        expected = [
            Brand(id=1, name="나이키", is_ip_approved=True),
        ]
        mock_repo.find_approved_brands.return_value = expected

        service = BrandService(session)
        result = await service.get_approved_brands()

        mock_repo.find_approved_brands.assert_called_once()
        assert len(result) == 1
        assert result[0].is_ip_approved is True


@pytest.mark.asyncio
async def test_get_approved_brands_empty():
    """승인된 브랜드가 없을 때 빈 리스트 반환"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.brand.service.BrandRepository") as MockRepo:
        mock_repo = AsyncMock()
        MockRepo.return_value = mock_repo
        mock_repo.find_approved_brands.return_value = []

        service = BrandService(session)
        result = await service.get_approved_brands()

        assert result == []
