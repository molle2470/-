"""수집 서비스 단위 테스트."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.domain.collection.service import (
    CollectionService,
    ExtensionCommandService,
)
from backend.domain.collection.model import CommandTypeEnum, CommandStatusEnum
from backend.dtos.extension import ExtensionProductData


def test_extension_command_service_init():
    """ExtensionCommandService 초기화"""
    session = AsyncMock()
    service = ExtensionCommandService(session)
    assert service.session is session


@pytest.mark.asyncio
async def test_create_monitor_register_command():
    """모니터링 등록 명령 생성"""
    session = AsyncMock()
    service = ExtensionCommandService(session)

    with patch.object(service, "repo") as mock_repo:
        mock_repo.create_async = AsyncMock()
        await service.create_monitor_command(
            product_id=42,
            source_url="https://www.musinsa.com/app/goods/12345",
            grade="high",
        )
        mock_repo.create_async.assert_called_once()
        call_kwargs = mock_repo.create_async.call_args[1]
        assert call_kwargs["command_type"] == CommandTypeEnum.MONITOR_REGISTER
        payload = json.loads(call_kwargs["payload"])
        assert payload["product_id"] == 42


@pytest.mark.asyncio
async def test_ack_command_done():
    """명령 처리 완료"""
    session = AsyncMock()
    service = ExtensionCommandService(session)

    mock_cmd = MagicMock()
    mock_cmd.id = 1
    mock_cmd.status = CommandStatusEnum.PENDING

    with patch.object(service, "repo") as mock_repo:
        mock_repo.get_async = AsyncMock(return_value=mock_cmd)
        mock_repo.update_async = AsyncMock(return_value=mock_cmd)
        await service.ack_command(command_id=1, status="done")
        # update_async(id, **kwargs) 패턴 검증
        mock_repo.update_async.assert_called_once()
        call_args = mock_repo.update_async.call_args
        assert call_args[0][0] == 1  # first positional arg = id


@pytest.mark.asyncio
async def test_collection_service_process_product():
    """수집 상품 처리 (DB 저장 + 로그 기록 + 브랜드 IP 경고)"""
    session = AsyncMock()
    service = CollectionService(session)

    product_data = ExtensionProductData(
        name="나이키 에어맥스 90",
        original_price=169000,
        source_url="https://www.musinsa.com/app/goods/12345",
        source_product_id="12345",
        brand_name="나이키",
        stock_status="in_stock",
    )

    with (
        patch.object(service, "product_service") as mock_product_svc,
        patch.object(service, "log_repo") as mock_log_repo,
        patch.object(service, "brand_repo") as mock_brand_repo,
    ):
        mock_product_svc.create_from_extension = AsyncMock(return_value=MagicMock(id=1))
        mock_log_repo.create_async = AsyncMock()
        # 브랜드 지재권 미승인 시뮬레이션
        mock_brand = MagicMock()
        mock_brand.is_ip_approved = False
        mock_brand_repo.find_by_name = AsyncMock(return_value=mock_brand)

        result = await service.process_collected_product(
            source="musinsa",
            product_data=product_data,
            source_id=1,
        )
        # 수집은 허용되되 경고 포함
        assert result["ip_warning"] is not None
        mock_product_svc.create_from_extension.assert_called_once()
        mock_log_repo.create_async.assert_called_once()
