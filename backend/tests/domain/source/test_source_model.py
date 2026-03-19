"""
소싱처(Source) 및 브랜드(Brand) 모델 단위 테스트.

DB 연결 없이 모델 인스턴스 생성만 검증합니다.
"""
from backend.domain.source.model import Source, SourceBrand
from backend.domain.brand.model import Brand


def test_source_model_exists():
    """Source 모델 인스턴스 생성 및 필드 검증"""
    source = Source(
        name="무신사",
        base_url="https://www.musinsa.com",
        crawler_type="musinsa"
    )
    assert source.name == "무신사"
    assert source.crawler_type == "musinsa"


def test_brand_model_exists():
    """Brand 모델 인스턴스 생성 및 필드 검증"""
    brand = Brand(name="나이키")
    assert brand.name == "나이키"


def test_source_brand_model_exists():
    """SourceBrand 모델 인스턴스 생성 및 필드 검증"""
    sb = SourceBrand(brand_id=1, source_id=1, display_name="NIKE")
    assert sb.display_name == "NIKE"
