import pytest
from backend.domain.market.model import (
    BusinessGroup, Market, MarketAccount, CommonTemplate,
    MarketTemplate, SeoRule, CoupangBrandClearance, MarketListing,
    ClearanceTypeEnum, ClearanceStatusEnum, ListingStatusEnum,
)


def test_business_group_model():
    bg = BusinessGroup(name="사업자A")
    assert bg.name == "사업자A"
    assert bg.created_at is not None


def test_market_model():
    m = Market(name="쿠팡")
    assert m.name == "쿠팡"
    assert m.header_image_url is None


def test_market_account_model():
    ma = MarketAccount(business_group_id=1, market_id=1, account_id="coupang_user")
    assert ma.account_id == "coupang_user"
    assert ma.is_active is True


def test_common_template_model():
    ct = CommonTemplate()
    assert ct.origin_country == "기타"
    assert ct.shipping_origin is None


def test_market_template_model():
    mt = MarketTemplate(market_id=1, common_template_id=1)
    assert mt.commission_rate == 0.0
    assert mt.margin_rate == 0.0
    assert mt.shipping_fee == 0
    assert mt.jeju_extra_fee == 5000


def test_coupang_brand_clearance_model():
    cbc = CoupangBrandClearance(
        brand_id=1,
        market_account_id=1,
        clearance_type=ClearanceTypeEnum.IP_RIGHT,
    )
    assert cbc.clearance_status == ClearanceStatusEnum.PENDING
    assert cbc.clearance_type == ClearanceTypeEnum.IP_RIGHT


def test_market_listing_model():
    ml = MarketListing(product_id=1, market_account_id=1, selling_price=139000)
    assert ml.selling_price == 139000
    assert ml.listing_status == ListingStatusEnum.PENDING


def test_clearance_status_enum():
    assert ClearanceStatusEnum.COMPLETED == "completed"
    assert ClearanceStatusEnum.PENDING == "pending"
    assert ClearanceStatusEnum.IN_PROGRESS == "in_progress"


def test_listing_status_enum():
    assert ListingStatusEnum.PENDING == "pending"
    assert ListingStatusEnum.REGISTERED == "registered"
    assert ListingStatusEnum.FAILED == "failed"
    assert ListingStatusEnum.DEACTIVATED == "deactivated"


def test_clearance_type_enum():
    assert ClearanceTypeEnum.IP_RIGHT == "ip_right"
    assert ClearanceTypeEnum.COUNTERFEIT == "counterfeit"


def test_seo_rule_model():
    sr = SeoRule(market_id=1)
    assert sr.market_id == 1
    assert sr.tag_pattern is None
    assert sr.title_pattern is None


def test_coupang_brand_clearance_requires_clearance_type():
    """clearance_type은 필수 필드 - model_validate 사용 시 없으면 ValidationError 발생해야 함

    SQLModel + sa_column 조합에서는 생성자 직접 호출 시 None 허용될 수 있으나,
    model_validate (dict 입력) 방식에서는 required 검증이 정상 동작함.
    """
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        CoupangBrandClearance.model_validate({'brand_id': 1, 'market_account_id': 1})
