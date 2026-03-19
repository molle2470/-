# backend/tests/domain/collection/test_collection_model.py
"""수집 도메인 모델 단위 테스트."""
from backend.domain.collection.model import (
    CollectionSetting,
    CollectionLog,
    ExtensionCommand,
    CommandStatusEnum,
    CommandTypeEnum,
    LogStatusEnum,
)


def test_collection_setting_creation():
    """CollectionSetting 인스턴스 생성 및 기본값"""
    setting = CollectionSetting(
        name="나이키_신발",
        source_id=1,
        brand_name="나이키",
        category_url="https://www.musinsa.com/categories/shoes",
    )
    assert setting.name == "나이키_신발"
    assert setting.max_count == 500
    assert setting.is_active is True
    assert setting.collected_count == 0


def test_collection_log_creation():
    """CollectionLog 인스턴스 생성"""
    log = CollectionLog(
        product_name="나이키 에어맥스 90",
        status=LogStatusEnum.SUCCESS,
    )
    assert log.status == "success"
    assert log.setting_id is None  # 개별 수집 시 null


def test_extension_command_creation():
    """ExtensionCommand 인스턴스 생성 및 기본값"""
    cmd = ExtensionCommand(
        command_type=CommandTypeEnum.MONITOR_REGISTER,
        payload='{"product_id": 42, "source_url": "https://..."}',
    )
    assert cmd.status == "pending"
    assert cmd.processed_at is None


def test_command_type_enum_values():
    """CommandTypeEnum 값 확인"""
    assert CommandTypeEnum.MONITOR_REGISTER == "monitor_register"
    assert CommandTypeEnum.MONITOR_UNREGISTER == "monitor_unregister"


def test_command_status_enum_values():
    """CommandStatusEnum 값 확인"""
    assert CommandStatusEnum.PENDING == "pending"
    assert CommandStatusEnum.PROCESSING == "processing"
    assert CommandStatusEnum.DONE == "done"
    assert CommandStatusEnum.FAILED == "failed"
