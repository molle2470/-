"""
BaseCrawler 단위 테스트.
"""
from typing import List, Optional

import pytest
from backend.domain.crawling.base_crawler import (
    BaseCrawler, BrandInfo, CategoryInfo, CrawledProduct, USER_AGENTS
)


class ConcreteCrawler(BaseCrawler):
    """테스트용 구체 크롤러"""
    async def scan_brands(self, category_url: str) -> List[BrandInfo]:
        return [BrandInfo(name="나이키", product_count=100)]

    async def scan_categories(self, category_url: str, brand_name: str) -> List[CategoryInfo]:
        return [CategoryInfo(name="스니커즈", product_count=50)]

    async def crawl_products(
        self,
        category_url: str,
        brand_name: str,
        categories: Optional[List[str]] = None,
        max_count: int = 20,
    ) -> List[CrawledProduct]:
        return []

    async def check_product(self, source_url: str) -> Optional[CrawledProduct]:
        return None


def test_base_crawler_can_be_instantiated():
    """BaseCrawler 기본 초기화 확인"""
    crawler = ConcreteCrawler()
    assert crawler.max_retries == 3
    assert crawler.min_delay == 1.0
    assert crawler.max_delay == 3.0


def test_random_user_agent_from_list():
    """랜덤 User-Agent가 목록에 포함되는지 확인"""
    crawler = ConcreteCrawler()
    ua = crawler._get_random_user_agent()
    assert ua in USER_AGENTS


@pytest.mark.asyncio
async def test_scan_brands():
    """브랜드 스캔 결과 확인"""
    crawler = ConcreteCrawler()
    brands = await crawler.scan_brands("https://example.com")
    assert len(brands) == 1
    assert brands[0].name == "나이키"


def test_crawled_product_dataclass():
    """CrawledProduct 데이터클래스 기본값 확인"""
    p = CrawledProduct(
        name="나이키 에어맥스",
        original_price=139000,
        source_url="https://musinsa.com/goods/1",
        source_product_id="1",
        brand_name="나이키",
        stock_status="in_stock",
    )
    assert p.name == "나이키 에어맥스"
    assert p.stock_status == "in_stock"
    assert p.image_urls == []
    assert p.options == []


def test_brand_info_dataclass():
    """BrandInfo 데이터클래스 확인"""
    brand = BrandInfo(name="나이키", product_count=100)
    assert brand.name == "나이키"
    assert brand.product_count == 100


def test_category_info_dataclass():
    """CategoryInfo 데이터클래스 확인"""
    category = CategoryInfo(name="스니커즈", product_count=50)
    assert category.name == "스니커즈"
    assert category.product_count == 50


@pytest.mark.asyncio
async def test_scan_categories():
    """카테고리 스캔 결과 확인"""
    crawler = ConcreteCrawler()
    categories = await crawler.scan_categories("https://example.com", "나이키")
    assert len(categories) == 1
    assert categories[0].name == "스니커즈"


@pytest.mark.asyncio
async def test_check_product_returns_none():
    """단일 상품 체크 반환값 확인"""
    crawler = ConcreteCrawler()
    result = await crawler.check_product("https://example.com/goods/1")
    assert result is None


@pytest.mark.asyncio
async def test_crawl_products_returns_empty():
    """상품 수집이 빈 리스트 반환 확인"""
    crawler = ConcreteCrawler()
    result = await crawler.crawl_products(
        category_url="https://example.com",
        brand_name="나이키",
        max_count=10,
    )
    assert isinstance(result, list)
    assert len(result) == 0
