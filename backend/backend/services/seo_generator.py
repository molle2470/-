"""
마켓별 SEO 자동 생성 서비스.

태그, 타이틀, 메타설명을 브랜드/카테고리/상품명에서 자동 생성.
"""
import re
from typing import List


class SeoGenerator:
    """마켓별 SEO 자동 생성 서비스"""

    def generate_tags(
        self,
        brand: str,
        category: str,
        product_name: str,
        max_tags: int = 10,
    ) -> List[str]:
        """
        태그 자동 생성.

        브랜드, 카테고리, 상품명 키워드를 조합하여 태그 목록 생성.
        2글자 이상의 고유 키워드만 포함.

        Args:
            brand: 브랜드명
            category: 카테고리명
            product_name: 상품명
            max_tags: 최대 태그 수 (기본 10개)

        Returns:
            태그 목록 (중복 없음, max_tags 이하)
        """
        seen: set[str] = set()
        tags: List[str] = []

        def add_tag(word: str) -> None:
            # 2글자 이상이고 중복되지 않은 태그만 추가
            if len(word) >= 2 and word not in seen:
                seen.add(word)
                tags.append(word)

        # 1. 브랜드 먼저
        add_tag(brand)
        # 2. 카테고리
        add_tag(category)
        # 3. 브랜드+카테고리 조합 태그
        combo = f"{brand}{category}"
        if len(combo) <= 20:
            add_tag(combo)
        # 4. 상품명에서 키워드 추출 (공백/특수문자 기준 분리)
        words = re.split(r'[\s\-_/]+', product_name)
        for word in words:
            word = word.strip()
            # 브랜드/카테고리와 중복되는 단어는 별도 add_tag에서 중복 처리됨
            if word:
                add_tag(word)
            if len(tags) >= max_tags:
                break

        return tags[:max_tags]

    def generate_title(
        self,
        pattern: str,
        brand: str,
        product_name: str,
        max_length: int = 100,
    ) -> str:
        """
        패턴 기반 타이틀 생성.

        Args:
            pattern: 타이틀 패턴 (예: "{brand} {product_name}")
            brand: 브랜드명
            product_name: 상품명
            max_length: 최대 길이 (기본 100자)

        Returns:
            생성된 타이틀 (max_length 이하)
        """
        title = pattern.replace("{brand}", brand).replace("{product_name}", product_name)
        if len(title) > max_length:
            title = title[:max_length]
        return title

    def generate_meta_description(
        self,
        pattern: str,
        brand: str,
        product_name: str,
        category: str,
        max_length: int = 160,
    ) -> str:
        """
        메타 설명 생성.

        Args:
            pattern: 설명 패턴
            brand: 브랜드명
            product_name: 상품명
            category: 카테고리명
            max_length: 최대 길이 (기본 160자)

        Returns:
            생성된 메타 설명
        """
        description = (
            pattern
            .replace("{brand}", brand)
            .replace("{product_name}", product_name)
            .replace("{category}", category)
        )
        if len(description) > max_length:
            description = description[:max_length]
        return description
