"""네이버 카테고리 + 상품정보제공고시 매핑 테스트."""
from backend.adapters.naver_category_map import get_naver_category_info, DEFAULT_NAVER_INFO


def test_shoes_category_returns_shoes_notice_type():
    """스니커즈 → SHOES 유형 반환"""
    info = get_naver_category_info("스니커즈")
    assert info.leaf_category_id == "50000803"
    assert info.product_info_notice_type == "SHOES"


def test_wear_category_returns_wear_notice_type():
    """티셔츠 → WEAR 유형 반환"""
    info = get_naver_category_info("무신사 티셔츠 카테고리")
    assert info.product_info_notice_type == "WEAR"


def test_bag_category_returns_bag_notice_type():
    """백팩 → BAG 유형 반환"""
    info = get_naver_category_info("백팩")
    assert info.product_info_notice_type == "BAG"


def test_none_returns_default():
    """None 입력 시 기본 카테고리 반환"""
    assert get_naver_category_info(None) == DEFAULT_NAVER_INFO


def test_unknown_category_returns_default():
    """알 수 없는 카테고리 → 기본값 반환"""
    assert get_naver_category_info("알수없는카테고리XYZ") == DEFAULT_NAVER_INFO
