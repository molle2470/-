"""SEO 규칙 테이블 테스트."""
import pytest
from backend.domain.product.seo_rules import (
    get_naver_category_id,
    extract_color,
    infer_gender,
    infer_origin,
    get_material_default,
)


def test_category_mapping_sneakers():
    """스니커즈 카테고리 매핑"""
    result = get_naver_category_id("스니커즈")
    assert result == "50000803"


def test_category_mapping_unknown_returns_none():
    """알 수 없는 카테고리는 None 반환"""
    result = get_naver_category_id("없는카테고리")
    assert result is None


def test_extract_color_white():
    """상품명에서 화이트 추출"""
    result = extract_color("나이키 에어맥스 화이트 / BQ1234")
    assert result == "화이트"


def test_extract_color_multiple_returns_first():
    """여러 색상 있으면 첫 번째 반환"""
    result = extract_color("나이키 블랙 화이트")
    assert result == "블랙"


def test_extract_color_none_when_no_match():
    """색상 키워드 없으면 None"""
    result = extract_color("나이키 에어맥스 90")
    assert result is None


def test_infer_gender_unisex():
    """기본값은 남녀공용"""
    result = infer_gender("나이키", "에어맥스 90")
    assert result == "남녀공용"


def test_infer_origin_global_brand():
    """나이키는 해외"""
    result = infer_origin("NIKE")
    assert result == "해외"


def test_get_material_default_shoes():
    """신발 기본 소재"""
    result = get_material_default("스니커즈")
    assert result == "합성섬유/합성피혁"


def test_get_material_default_clothing():
    """의류 기본 소재"""
    result = get_material_default("반소매 티셔츠")
    assert result == "면혼합"


def test_infer_gender_women():
    """우먼 키워드가 있으면 여성 반환"""
    result = infer_gender("나이키", "우먼 에어맥스")
    assert result == "여성"


def test_infer_gender_men():
    """MENS 키워드가 있으면 남성 반환"""
    result = infer_gender("나이키", "MENS 에어맥스")
    assert result == "남성"
