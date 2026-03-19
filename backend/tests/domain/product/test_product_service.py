"""
ProductService 단위 테스트.

DB 세션과 Repository를 AsyncMock으로 모킹하여
서비스 비즈니스 로직만 검증합니다.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.domain.product.model import (
    Product,
    ProductStatusEnum,
    StockStatusEnum,
)
from backend.domain.product.service import ProductService


@pytest.mark.asyncio
async def test_create_from_crawled_new_product():
    """새 상품 생성: 중복 없을 때 Product 객체 생성 및 DB 저장 확인"""
    session = AsyncMock()
    session.add = MagicMock()  # add는 동기 메서드

    with patch("backend.domain.product.service.ProductRepository") as MockRepo:
        mock_repo = AsyncMock()
        MockRepo.return_value = mock_repo
        # 중복 없음
        mock_repo.find_by_source_product_id.return_value = None

        service = ProductService(session)
        crawled_data = {
            "name": "나이키 에어맥스 90",
            "original_price": 150000,
            "source_url": "https://musinsa.com/p/1",
            "source_product_id": "musinsa_1",
        }

        result = await service.create_from_crawled(
            crawled_data, source_id=1, brand_id=1
        )

        # session.add 호출 확인
        session.add.assert_called_once()
        session.commit.assert_called_once()
        session.refresh.assert_called_once()

        # 반환값이 Product 인스턴스인지 확인
        assert isinstance(result, Product)
        assert result.name == "나이키 에어맥스 90"
        assert result.original_price == 150000
        assert result.source_id == 1
        assert result.brand_id == 1


@pytest.mark.asyncio
async def test_create_from_crawled_existing_product():
    """이미 있는 상품은 기존 것 반환"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.product.service.ProductRepository") as MockRepo:
        mock_repo = AsyncMock()
        MockRepo.return_value = mock_repo

        # 기존 상품 존재
        existing_product = Product(
            id=10,
            source_id=1,
            brand_id=1,
            name="나이키 에어맥스 90",
            original_price=150000,
            source_url="https://musinsa.com/p/1",
            source_product_id="musinsa_1",
        )
        mock_repo.find_by_source_product_id.return_value = existing_product

        service = ProductService(session)
        crawled_data = {
            "name": "나이키 에어맥스 90",
            "original_price": 150000,
            "source_url": "https://musinsa.com/p/1",
            "source_product_id": "musinsa_1",
        }

        result = await service.create_from_crawled(
            crawled_data, source_id=1, brand_id=1
        )

        # 기존 상품 반환 확인
        assert result.id == 10
        # DB 저장 없어야 함
        session.add.assert_not_called()
        session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_price_and_stock_price_changed():
    """가격 변동 감지 및 업데이트"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.product.service.ProductRepository") as MockRepo:
        mock_repo = AsyncMock()
        MockRepo.return_value = mock_repo

        product = Product(
            id=1,
            source_id=1,
            brand_id=1,
            name="테스트 상품",
            original_price=100000,
            source_url="https://example.com/p/1",
            source_product_id="test_1",
            stock_status=StockStatusEnum.IN_STOCK,
        )
        mock_repo.get_async.return_value = product

        service = ProductService(session)
        changes = await service.update_price_and_stock(
            product_id=1,
            new_price=120000,
            new_stock_status=StockStatusEnum.IN_STOCK,
        )

        # 가격 변동만 감지되어야 함
        assert len(changes) == 1
        change_type, old_val, new_val = changes[0]
        assert change_type == "price_change"
        assert old_val == 100000
        assert new_val == 120000

        # 업데이트 후 DB 저장 확인
        session.add.assert_called_once()
        session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_price_and_stock_stock_changed():
    """재고 변동 감지 및 업데이트"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.product.service.ProductRepository") as MockRepo:
        mock_repo = AsyncMock()
        MockRepo.return_value = mock_repo

        product = Product(
            id=1,
            source_id=1,
            brand_id=1,
            name="테스트 상품",
            original_price=100000,
            source_url="https://example.com/p/1",
            source_product_id="test_1",
            stock_status=StockStatusEnum.IN_STOCK,
        )
        mock_repo.get_async.return_value = product

        service = ProductService(session)
        changes = await service.update_price_and_stock(
            product_id=1,
            new_price=100000,
            new_stock_status=StockStatusEnum.OUT_OF_STOCK,
        )

        # 재고 변동만 감지
        assert len(changes) == 1
        change_type, old_val, new_val = changes[0]
        assert change_type == "stock_change"
        assert old_val == StockStatusEnum.IN_STOCK
        assert new_val == StockStatusEnum.OUT_OF_STOCK


@pytest.mark.asyncio
async def test_update_price_and_stock_no_change():
    """변동 없을 때 빈 리스트 반환 및 DB 저장 없음"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.product.service.ProductRepository") as MockRepo:
        mock_repo = AsyncMock()
        MockRepo.return_value = mock_repo

        product = Product(
            id=1,
            source_id=1,
            brand_id=1,
            name="테스트 상품",
            original_price=100000,
            source_url="https://example.com/p/1",
            source_product_id="test_1",
            stock_status=StockStatusEnum.IN_STOCK,
        )
        mock_repo.get_async.return_value = product

        service = ProductService(session)
        changes = await service.update_price_and_stock(
            product_id=1,
            new_price=100000,
            new_stock_status=StockStatusEnum.IN_STOCK,
        )

        assert changes == []
        session.add.assert_not_called()
        session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_price_and_stock_product_not_found():
    """존재하지 않는 상품: 빈 리스트 반환"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.product.service.ProductRepository") as MockRepo:
        mock_repo = AsyncMock()
        MockRepo.return_value = mock_repo
        mock_repo.get_async.return_value = None

        service = ProductService(session)
        changes = await service.update_price_and_stock(
            product_id=999,
            new_price=100000,
            new_stock_status=StockStatusEnum.IN_STOCK,
        )

        assert changes == []


@pytest.mark.asyncio
async def test_list_products_with_filters():
    """필터 기반 상품 목록 조회"""
    session = AsyncMock()
    session.add = MagicMock()

    with patch("backend.domain.product.service.ProductRepository") as MockRepo:
        mock_repo = AsyncMock()
        MockRepo.return_value = mock_repo

        expected = [
            Product(
                id=1,
                source_id=1,
                brand_id=1,
                name="상품 A",
                original_price=50000,
                source_url="https://example.com/1",
                source_product_id="p1",
            )
        ]
        mock_repo.find_by_filters.return_value = expected

        service = ProductService(session)
        result = await service.list_products(
            source_id=1,
            brand_id=1,
            status=ProductStatusEnum.COLLECTED,
            skip=0,
            limit=10,
        )

        mock_repo.find_by_filters.assert_called_once_with(
            source_id=1,
            brand_id=1,
            status=ProductStatusEnum.COLLECTED,
            skip=0,
            limit=10,
        )
        assert len(result) == 1
        assert result[0].name == "상품 A"
