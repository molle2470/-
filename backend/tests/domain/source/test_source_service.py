"""
SourceService 단위 테스트.

DB 세션과 Repository를 AsyncMock으로 모킹하여
서비스 비즈니스 로직만 검증합니다.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.domain.source.model import Source, SourceBrand
from backend.domain.source.service import SourceService


@pytest.mark.asyncio
async def test_get_active_sources():
    """활성 소싱처 목록 반환"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.source.service.SourceRepository") as MockSourceRepo, \
         patch("backend.domain.source.service.SourceBrandRepository"):

        mock_repo = AsyncMock()
        MockSourceRepo.return_value = mock_repo

        expected = [
            Source(id=1, name="무신사", base_url="https://musinsa.com", crawler_type="musinsa"),
            Source(id=2, name="SSG", base_url="https://ssg.com", crawler_type="ssg"),
        ]
        mock_repo.find_active_sources.return_value = expected

        service = SourceService(session)
        result = await service.get_active_sources()

        mock_repo.find_active_sources.assert_called_once()
        assert len(result) == 2
        assert result[0].name == "무신사"


@pytest.mark.asyncio
async def test_get_source_brands():
    """소싱처의 브랜드 목록 반환"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.source.service.SourceRepository"), \
         patch("backend.domain.source.service.SourceBrandRepository") as MockBrandRepo:

        mock_brand_repo = AsyncMock()
        MockBrandRepo.return_value = mock_brand_repo

        expected = [
            SourceBrand(id=1, brand_id=1, source_id=1, display_name="NIKE"),
            SourceBrand(id=2, brand_id=2, source_id=1, display_name="ADIDAS"),
        ]
        mock_brand_repo.find_by_source.return_value = expected

        service = SourceService(session)
        result = await service.get_source_brands(source_id=1)

        mock_brand_repo.find_by_source.assert_called_once_with(source_id=1)
        assert len(result) == 2
        assert result[0].display_name == "NIKE"


@pytest.mark.asyncio
async def test_create_source():
    """소싱처 생성 및 DB 저장 확인"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.source.service.SourceRepository"), \
         patch("backend.domain.source.service.SourceBrandRepository"):

        service = SourceService(session)
        result = await service.create_source(
            name="무신사",
            base_url="https://musinsa.com",
            crawler_type="musinsa",
        )

        session.add.assert_called_once()
        session.commit.assert_called_once()
        session.refresh.assert_called_once()

        assert isinstance(result, Source)
        assert result.name == "무신사"
        assert result.base_url == "https://musinsa.com"
        assert result.crawler_type == "musinsa"


@pytest.mark.asyncio
async def test_create_source_default_crawler_type():
    """크롤러 타입 기본값(generic) 확인"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.source.service.SourceRepository"), \
         patch("backend.domain.source.service.SourceBrandRepository"):

        service = SourceService(session)
        result = await service.create_source(
            name="테스트소싱처",
            base_url="https://test.com",
        )

        assert result.crawler_type == "generic"
