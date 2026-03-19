from backend.domain.product.model import (
    Product, ProductOptionGroup, ProductOptionValue, ProductVariant,
    ProductStatusEnum, MonitoringGradeEnum, StockStatusEnum,
)


def test_product_model():
    p = Product(
        source_id=1, brand_id=1, name="나이키 에어맥스 90",
        original_price=139000, source_url="https://musinsa.com/123",
        source_product_id="musinsa_123",
    )
    assert p.status == ProductStatusEnum.COLLECTED
    assert p.monitoring_grade == MonitoringGradeEnum.NORMAL
    assert p.stock_status == StockStatusEnum.IN_STOCK
    assert p.created_at is not None


def test_product_variant():
    v = ProductVariant(
        product_id=1,
        option_combination={"색상": "블랙", "사이즈": "M"},
        stock_status=StockStatusEnum.IN_STOCK,
    )
    assert v.option_combination["색상"] == "블랙"
    assert v.additional_price == 0


def test_product_option_group():
    og = ProductOptionGroup(product_id=1, group_name="색상")
    assert og.group_name == "색상"


def test_product_option_value():
    ov = ProductOptionValue(group_id=1, value="블랙")
    assert ov.value == "블랙"


def test_product_status_enum():
    assert ProductStatusEnum.COLLECTED == "collected"
    assert ProductStatusEnum.REGISTERED == "registered"
    assert ProductStatusEnum.INACTIVE == "inactive"
