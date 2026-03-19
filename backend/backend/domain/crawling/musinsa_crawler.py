"""
무신사 전용 크롤러.

무신사는 CSR 기반이므로 내부 API 엔드포인트를 직접 호출.
API 호출 불가 시 httpx + BeautifulSoup으로 HTML 파싱 폴백.
"""
import json
from typing import Dict, List, Optional

import httpx

from backend.domain.crawling.base_crawler import BaseCrawler, BrandInfo, CategoryInfo, CrawledProduct
from backend.utils.logger import logger


# 무신사 내부 API 엔드포인트
MUSINSA_API_BASE = "https://api.musinsa.com"
MUSINSA_WEB_BASE = "https://www.musinsa.com"


class MusinsaCrawler(BaseCrawler):
    """무신사 전용 크롤러"""

    def __init__(self):
        super().__init__()
        self.min_delay = 1.5  # 무신사는 약간 더 긴 딜레이
        self.max_delay = 4.0

    def _get_headers(self) -> Dict[str, str]:
        """요청 헤더"""
        return {
            "User-Agent": self._get_random_user_agent(),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": MUSINSA_WEB_BASE,
        }

    async def _fetch_json(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """JSON API 호출"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=self._get_headers(), params=params)
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, json.JSONDecodeError) as e:
            logger.warning(f"무신사 API 호출 실패: {url} - {e}")
            return None

    async def scan_brands(self, category_url: str) -> List[BrandInfo]:
        """
        카테고리 페이지에서 브랜드 목록 스캔.

        Note: 실제 운영 시 무신사 내부 API 분석 필요.
        현재는 구조를 갖춘 스텁 구현.
        """
        logger.info(f"무신사 브랜드 스캔: {category_url}")
        # TODO: 무신사 내부 API 엔드포인트 분석 후 구현
        # 예: GET /api/category/brands?categoryCode=001
        return []

    async def scan_categories(self, category_url: str, brand_name: str) -> List[CategoryInfo]:
        """
        브랜드 선택 후 카테고리 목록 스캔.

        Note: 실제 운영 시 무신사 내부 API 분석 필요.
        """
        logger.info(f"무신사 카테고리 스캔: {category_url}, 브랜드: {brand_name}")
        # TODO: 무신사 내부 API 엔드포인트 분석 후 구현
        return []

    async def crawl_products(
        self,
        category_url: str,
        brand_name: str,
        categories: Optional[List[str]] = None,
        max_count: int = 20,
    ) -> List[CrawledProduct]:
        """
        상품 수집 (최대 max_count개).

        Note: 실제 운영 시 무신사 내부 API 분석 후 구현.
        현재는 구조를 갖춘 스텁 구현.
        """
        logger.info(f"무신사 상품 수집 시작: 브랜드={brand_name}, 최대={max_count}개")
        # TODO: 무신사 API 또는 HTML 파싱으로 구현
        return []

    async def check_product(self, source_url: str) -> Optional[CrawledProduct]:
        """
        단일 상품 가격/재고 체크 (모니터링용).

        Note: 실제 운영 시 무신사 내부 API 분석 후 구현.
        """
        logger.info(f"무신사 상품 체크: {source_url}")
        # TODO: 무신사 상품 상세 API 분석 후 구현
        return None

    def _parse_product_from_api(self, item: Dict) -> Optional[CrawledProduct]:
        """
        무신사 API 응답에서 CrawledProduct 파싱.

        실제 API 응답 구조 분석 후 필드명 매핑 필요.
        """
        try:
            return CrawledProduct(
                name=item.get("goodsName", ""),
                original_price=int(item.get("normalPrice", 0)),
                source_url=f"{MUSINSA_WEB_BASE}/app/goods/{item.get('goodsNo', '')}",
                source_product_id=str(item.get("goodsNo", "")),
                brand_name=item.get("brandName", ""),
                stock_status="in_stock" if item.get("isSoldOut", False) is False else "out_of_stock",
                thumbnail_url=item.get("thumbnailImageUrl"),
                image_urls=item.get("imageUrls", []),
                category=item.get("category", {}).get("name"),
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"상품 파싱 실패: {e}")
            return None
