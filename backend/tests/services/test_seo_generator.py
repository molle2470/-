from backend.services.seo_generator import SeoGenerator


def test_generate_tags_contains_brand():
    """브랜드가 태그에 포함되어야 함"""
    gen = SeoGenerator()
    tags = gen.generate_tags(
        brand="나이키",
        category="운동화",
        product_name="나이키 에어맥스 90 블랙",
        max_tags=10,
    )
    assert "나이키" in tags
    assert "운동화" in tags


def test_generate_tags_extracts_keywords():
    """상품명에서 키워드 추출"""
    gen = SeoGenerator()
    tags = gen.generate_tags(
        brand="나이키",
        category="운동화",
        product_name="나이키 에어맥스 90 블랙",
        max_tags=10,
    )
    assert "에어맥스" in tags


def test_generate_tags_max_count():
    """태그 최대 개수 제한"""
    gen = SeoGenerator()
    tags = gen.generate_tags(
        brand="나이키",
        category="운동화",
        product_name="나이키 에어맥스 90 블랙 화이트 레드 블루 그린 퍼플 오렌지",
        max_tags=5,
    )
    assert len(tags) <= 5


def test_generate_title_basic():
    """기본 타이틀 생성"""
    gen = SeoGenerator()
    title = gen.generate_title(
        pattern="{brand} {product_name}",
        brand="나이키",
        product_name="에어맥스 90 블랙",
    )
    assert title == "나이키 에어맥스 90 블랙"


def test_generate_title_max_length():
    """타이틀 최대 길이 제한"""
    gen = SeoGenerator()
    title = gen.generate_title(
        pattern="{brand} {product_name}",
        brand="나이키",
        product_name="에어맥스 90 블랙 화이트 레드 블루 " * 5,
        max_length=50,
    )
    assert len(title) <= 50


def test_generate_meta_description():
    """메타 설명 생성"""
    gen = SeoGenerator()
    desc = gen.generate_meta_description(
        pattern="{brand} {category} {product_name}",
        brand="나이키",
        product_name="에어맥스 90",
        category="운동화",
    )
    assert "나이키" in desc
    assert "운동화" in desc
    assert "에어맥스 90" in desc


def test_generate_tags_no_duplicates():
    """태그 중복 없음"""
    gen = SeoGenerator()
    tags = gen.generate_tags(
        brand="나이키",
        category="스니커즈",
        product_name="나이키 에어맥스",
        max_tags=20,
    )
    assert len(tags) == len(set(tags))


def test_generate_tags_filters_short_words():
    """1글자 단어는 태그에서 제외"""
    gen = SeoGenerator()
    tags = gen.generate_tags(
        brand="나이키",
        category="운동화",
        product_name="a b c 에어맥스",
        max_tags=20,
    )
    assert "a" not in tags
    assert "b" not in tags
