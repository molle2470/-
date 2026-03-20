"""SEO 자동 생성 서비스 (규칙 기반 + Claude API)."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

from backend.domain.product.seo_rules import (
    extract_color,
    get_material_default,
    get_naver_category_id,
    infer_gender,
    infer_origin,
)
from backend.services.seo_generator import SeoGenerator  # 기존 규칙 기반 태그 생성기

if TYPE_CHECKING:
    from backend.dtos.extension import ExtensionProductData

logger = logging.getLogger(__name__)


class SeoGeneratorService:
    """규칙 기반 + Claude API 하이브리드 SEO 생성 서비스"""

    def __init__(self, api_key: Optional[str], model: str = "claude-haiku-4-5-20251001"):
        self.api_key = api_key
        self.model = model
        self._rule_generator = SeoGenerator()

    async def generate(
        self,
        product_data: "ExtensionProductData",
        product_id: int,
        market_type: str = "naver",
    ) -> Dict[str, Any]:
        """
        SEO 데이터 생성.

        1. 규칙 기반으로 즉시 처리 가능한 필드 생성
        2. Claude API로 상품명 최적화, 태그, 소재 생성 (api_key 있을 때)
        3. Claude 실패 시 규칙 기반 fallback

        Returns:
            product_seo 테이블에 저장할 데이터 dict
        """
        brand = product_data.brand_name or ""
        name = product_data.name or ""
        source_category = getattr(product_data, "source_category", None) or ""

        # 규칙 기반 필드 (항상 실행)
        color = extract_color(name)
        gender = infer_gender(brand, name)
        origin = infer_origin(brand)
        naver_category_id = get_naver_category_id(source_category)
        material_default = get_material_default(source_category)

        # 태그 fallback (규칙 기반)
        fallback_tags = self._rule_generator.generate_tags(
            brand=brand,
            category=source_category,
            product_name=name,
            max_tags=10,
        )
        # 이름 fallback
        fallback_name = name[:100] if name else f"{brand} {source_category}".strip()

        # Claude API 시도
        claude_result = None
        if self.api_key:
            try:
                claude_result = await asyncio.wait_for(
                    self._call_claude_api(
                        name=name,
                        brand=brand,
                        source_category=source_category,
                        original_price=product_data.original_price,
                    ),
                    timeout=5.0,
                )
            except Exception as e:
                logger.warning(f"[SEO] Claude API 실패 (product_id={product_id}): {e}")

        status = "generated" if claude_result else "fallback"

        return {
            "product_id": product_id,
            "market_type": market_type,
            "optimized_name": (claude_result or {}).get("optimized_name") or fallback_name,
            "tags": (claude_result or {}).get("tags") or fallback_tags,
            "naver_category_id": naver_category_id,
            "brand": brand,
            "material": (claude_result or {}).get("material") or material_default,
            "color": color,
            "gender": gender,
            "age_group": "성인",
            "origin": origin,
            "status": status,
        }

    async def _call_claude_api(
        self,
        name: str,
        brand: str,
        source_category: str,
        original_price: int,
    ) -> Dict[str, Any]:
        """Claude API 호출하여 SEO 필드 생성"""
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        prompt = f"""네이버 스마트스토어 SEO 최적화 전문가로서 아래 패션 상품의 SEO 데이터를 JSON으로 생성해주세요.

상품 정보:
- 원본 상품명: {name}
- 브랜드: {brand}
- 카테고리: {source_category}
- 가격: {original_price}원

규칙:
1. optimized_name: 100자 이하, 핵심 키워드(브랜드+카테고리+색상+품번) 앞에 배치
2. tags: 검색량 높은 키워드 10개 이하, 각 15자 이하, 브랜드/스타일/색상/소재 포함
3. material: 실제 소재 추론 (예: "메쉬/합성피혁", "면100%")

반드시 JSON만 반환 (다른 텍스트 없이):
{{"optimized_name": "...", "tags": ["...", ...], "material": "..."}}"""

        message = await client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        # JSON 파싱 (코드 블록 제거)
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
