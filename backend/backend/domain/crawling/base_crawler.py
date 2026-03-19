"""
크롤러 공통 인터페이스.

모든 소싱처 크롤러의 기반이 되는 추상 클래스.
봇 감지 회피를 위한 랜덤 딜레이, User-Agent 로테이션 포함.
"""
import asyncio
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


@dataclass
class CrawledProduct:
    """크롤링된 상품 데이터"""
    name: str
    original_price: int
    source_url: str
    source_product_id: str
    brand_name: str
    stock_status: str  # "in_stock" | "out_of_stock"
    thumbnail_url: Optional[str] = None
    image_urls: List[str] = field(default_factory=list)
    category: Optional[str] = None
    options: List[Dict] = field(default_factory=list)  # [{"group": "색상", "values": ["블랙"]}]


@dataclass
class BrandInfo:
    """소싱처 브랜드 정보"""
    name: str
    product_count: int


@dataclass
class CategoryInfo:
    """소싱처 카테고리 정보"""
    name: str
    product_count: int


class BaseCrawler(ABC):
    """크롤러 공통 인터페이스"""

    def __init__(self):
        self.max_retries: int = 3
        self.min_delay: float = 1.0  # 최소 딜레이 (초)
        self.max_delay: float = 3.0  # 최대 딜레이 (초)

    async def _random_delay(self) -> None:
        """랜덤 딜레이 (봇 감지 회피)"""
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)

    def _get_random_user_agent(self) -> str:
        """랜덤 User-Agent 반환"""
        return random.choice(USER_AGENTS)

    async def _request_with_retry(self, fetch_func, *args, **kwargs):
        """자동 재시도 (최대 3회, 지수 백오프)"""
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                await self._random_delay()
                return await fetch_func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # 1초, 2초, 4초
        raise last_error  # type: ignore[misc]

    @abstractmethod
    async def scan_brands(self, category_url: str) -> List[BrandInfo]:
        """카테고리 페이지에서 브랜드 목록 + 상품 갯수 스캔"""
        ...

    @abstractmethod
    async def scan_categories(self, category_url: str, brand_name: str) -> List[CategoryInfo]:
        """브랜드 선택 후 카테고리 목록 스캔"""
        ...

    @abstractmethod
    async def crawl_products(
        self,
        category_url: str,
        brand_name: str,
        categories: Optional[List[str]] = None,
        max_count: int = 20,
    ) -> List[CrawledProduct]:
        """상품 수집 (최대 max_count개)"""
        ...

    @abstractmethod
    async def check_product(self, source_url: str) -> Optional[CrawledProduct]:
        """단일 상품 가격/재고 체크 (모니터링용)"""
        ...
