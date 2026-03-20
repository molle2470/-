"""네이버 SEO 패션 특화 규칙 테이블."""
from typing import Optional

# 무신사 카테고리명 → 네이버 카테고리 ID
MUSINSA_TO_NAVER_CATEGORY: dict[str, str] = {
    "스니커즈": "50000803",
    "슬립온": "50000803",
    "로퍼": "50000795",
    "보트슈즈": "50000795",
    "샌들": "50000801",
    "슬리퍼": "50000801",
    "부츠": "50000797",
    "워커": "50000797",
    "반소매 티셔츠": "50000000",
    "긴소매 티셔츠": "50000000",
    "맨투맨": "50000001",
    "스웨트셔츠": "50000001",
    "후드 티셔츠": "50000002",
    "후디": "50000002",
    "니트": "50000003",
    "스웨터": "50000003",
    "바지": "50000100",
    "팬츠": "50000100",
    "반바지": "50000101",
    "숏팬츠": "50000101",
    "모자": "50000200",
    "캡": "50000200",
    "비니": "50000200",
    "가방": "50000300",
    "백팩": "50000300",
    "토트백": "50000300",
    "양말": "50000400",
    "레깅스": "50000400",
}

# 색상 키워드 (우선순위 순)
COLOR_KEYWORDS: list[str] = [
    "블랙", "화이트", "네이비", "그레이", "베이지", "브라운",
    "레드", "블루", "그린", "옐로우", "핑크", "퍼플", "오렌지",
    "아이보리", "카키", "와인", "민트", "코랄", "라벤더",
    "BLACK", "WHITE", "NAVY", "GRAY", "GREY", "BEIGE", "BROWN",
]

# 국내 브랜드 키워드
DOMESTIC_BRAND_KEYWORDS: list[str] = [
    "MLB", "디스이즈네버댓", "커버낫", "더콰이엇", "아크메드라비",
    "마하그리드", "플리츠마마", "뮬라웨어", "뉴발란스코리아",
]

# 매 호출 시 리스트 재생성 방지: 모듈 레벨에서 대문자 변환 캐싱
_DOMESTIC_BRAND_UPPER: frozenset[str] = frozenset(b.upper() for b in DOMESTIC_BRAND_KEYWORDS)

# 카테고리별 기본 소재 (MUSINSA_TO_NAVER_CATEGORY 키와 일치)
CATEGORY_DEFAULT_MATERIAL: dict[str, str] = {
    "스니커즈": "합성섬유/합성피혁",
    "슬립온": "합성섬유/합성피혁",
    "로퍼": "합성피혁",
    "부츠": "합성피혁",
    "워커": "합성피혁",
    "샌들": "합성소재",
    "슬리퍼": "합성소재",
    "반소매 티셔츠": "면혼합",
    "긴소매 티셔츠": "면혼합",
    "맨투맨": "면폴리혼합",
    "스웨트셔츠": "면폴리혼합",  # 알리아스 추가
    "후드 티셔츠": "면폴리혼합",
    "후디": "면폴리혼합",         # 알리아스 추가
    "니트": "아크릴혼합",
    "스웨터": "아크릴혼합",       # 알리아스 추가
    "바지": "면폴리혼합",
    "팬츠": "면폴리혼합",         # 알리아스 추가
    "반바지": "면폴리혼합",
    "숏팬츠": "면폴리혼합",       # 알리아스 추가
    "모자": "면폴리혼합",
    "캡": "면폴리혼합",           # 알리아스 추가
    "비니": "아크릴혼합",         # 알리아스 추가
    "가방": "합성섬유",
    "백팩": "합성섬유",           # 알리아스 추가
    "토트백": "합성섬유",         # 알리아스 추가
    "양말": "면혼합",
    "레깅스": "나일론혼합",       # 알리아스 추가
}


def get_naver_category_id(source_category: str) -> Optional[str]:
    """무신사 카테고리명 → 네이버 카테고리 ID"""
    if not source_category:
        return None
    if source_category in MUSINSA_TO_NAVER_CATEGORY:
        return MUSINSA_TO_NAVER_CATEGORY[source_category]
    for key, value in MUSINSA_TO_NAVER_CATEGORY.items():
        if key in source_category:
            return value
    return None


def extract_color(product_name: str) -> Optional[str]:
    """상품명에서 첫 번째 색상 키워드 추출"""
    upper_name = product_name.upper()
    for color in COLOR_KEYWORDS:
        if color.upper() in upper_name:
            return color if not color.isupper() else color.capitalize()
    return None


def infer_gender(brand: str, product_name: str) -> str:
    """브랜드/상품명에서 성별 추론 (기본값: 남녀공용)"""
    combined = f"{brand} {product_name}".upper()
    if "우먼" in combined or "WOMEN" in combined or "레이디" in combined:
        return "여성"
    if "맨즈" in combined or "MEN'S" in combined or "MENS" in combined:
        return "남성"
    return "남녀공용"


def infer_origin(brand: str) -> str:
    """브랜드명으로 원산지 추론 (기본값: 해외)"""
    brand_upper = brand.upper()
    if any(domestic in brand_upper for domestic in _DOMESTIC_BRAND_UPPER):
        return "국내"
    return "해외"


def get_material_default(source_category: str) -> str:
    """카테고리별 기본 소재 반환"""
    if not source_category:
        return "혼합소재"
    for key, material in CATEGORY_DEFAULT_MATERIAL.items():
        if key in source_category:
            return material
    return "혼합소재"
