"""
MusinsaCrawler 단위 테스트.

실제 HTTP 요청 없이 목업으로 테스트.
"""
import pytest
from unittest.mock import AsyncMock, patch
from backend.domain.crawling.musinsa_crawler import MusinsaCrawler
from backend.domain.crawling.base_crawler import CrawledProduct


def test_musinsa_crawler_init():
    """MusinsaCrawler 초기화 확인"""
    crawler = MusinsaCrawler()
    assert crawler.min_delay == 1.5
    assert crawler.max_delay == 4.0
    assert crawler.max_retries == 3


def test_get_headers():
    """요청 헤더 구조 확인"""
    crawler = MusinsaCrawler()
    headers = crawler._get_headers()
    assert "User-Agent" in headers
    assert "Referer" in headers
    assert "Accept" in headers
    assert "Accept-Language" in headers


@pytest.mark.asyncio
async def test_crawl_products_returns_list():
    """crawl_products가 리스트 반환하는지 확인"""
    crawler = MusinsaCrawler()
    result = await crawler.crawl_products(
        category_url="https://musinsa.com/category/001",
        brand_name="나이키",
        max_count=10,
    )
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_check_product_returns_none_for_stub():
    """스텁 구현은 None 반환 확인"""
    crawler = MusinsaCrawler()
    result = await crawler.check_product("https://musinsa.com/goods/1")
    assert result is None


@pytest.mark.asyncio
async def test_scan_brands_returns_list():
    """scan_brands가 리스트 반환 확인"""
    crawler = MusinsaCrawler()
    result = await crawler.scan_brands("https://musinsa.com/category/001")
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_scan_categories_returns_list():
    """scan_categories가 리스트 반환 확인"""
    crawler = MusinsaCrawler()
    result = await crawler.scan_categories("https://musinsa.com/category/001", "나이키")
    assert isinstance(result, list)


def test_parse_product_from_api():
    """API 응답에서 상품 파싱 확인"""
    crawler = MusinsaCrawler()
    item = {
        "goodsNo": "12345",
        "goodsName": "나이키 에어맥스 90",
        "normalPrice": 139000,
        "brandName": "나이키",
        "isSoldOut": False,
        "thumbnailImageUrl": "https://example.com/thumb.jpg",
    }
    product = crawler._parse_product_from_api(item)
    assert product is not None
    assert product.source_product_id == "12345"
    assert product.original_price == 139000
    assert product.stock_status == "in_stock"


def test_parse_product_handles_missing_fields():
    """필드 누락 시 안전하게 처리 확인"""
    crawler = MusinsaCrawler()
    product = crawler._parse_product_from_api({})
    assert product is not None
    assert product.original_price == 0
    assert product.brand_name == ""


def test_parse_product_sold_out():
    """품절 상태 파싱 확인"""
    crawler = MusinsaCrawler()
    item = {
        "goodsNo": "99999",
        "goodsName": "품절 상품",
        "normalPrice": 50000,
        "brandName": "테스트",
        "isSoldOut": True,
    }
    product = crawler._parse_product_from_api(item)
    assert product is not None
    assert product.stock_status == "out_of_stock"


def test_parse_product_source_url_format():
    """상품 URL 형식 확인"""
    crawler = MusinsaCrawler()
    item = {"goodsNo": "12345", "normalPrice": 10000}
    product = crawler._parse_product_from_api(item)
    assert product is not None
    assert "12345" in product.source_url
    assert "musinsa.com" in product.source_url
