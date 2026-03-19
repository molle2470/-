"""수집 도메인 서비스."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from backend.dtos.extension import ExtensionProductData
    from backend.dtos.collection import (
        CollectionSettingCreateRequest,
        CollectionSettingUpdateRequest,
    )

from backend.domain.collection.model import (
    CollectionSetting,
    CollectionLog,
    ExtensionCommand,
    CommandTypeEnum,
    CommandStatusEnum,
    LogStatusEnum,
)
from backend.domain.collection.repository import (
    CollectionSettingRepository,
    CollectionLogRepository,
    ExtensionCommandRepository,
)
from backend.domain.product.service import ProductService
from backend.domain.brand.repository import BrandRepository
from backend.services.price_calculator import PriceCalculator
from backend.services.seo_generator import SeoGenerator
from backend.utils.logger import logger


class ExtensionCommandService:
    """익스텐션 명령 큐 관리"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ExtensionCommandRepository(session)

    async def get_pending_commands(self) -> List[ExtensionCommand]:
        """대기 중인 명령 조회 (익스텐션 폴링)"""
        return await self.repo.find_pending_commands()

    async def create_monitor_command(
        self,
        product_id: int,
        source_url: str,
        grade: str = "normal",
    ) -> ExtensionCommand:
        """모니터링 등록 명령 생성"""
        payload = json.dumps({
            "product_id": product_id,
            "source_url": source_url,
            "grade": grade,
        })
        return await self.repo.create_async(
            command_type=CommandTypeEnum.MONITOR_REGISTER,
            payload=payload,
        )

    async def create_unmonitor_command(self, product_id: int) -> ExtensionCommand:
        """모니터링 해제 명령 생성"""
        payload = json.dumps({"product_id": product_id})
        return await self.repo.create_async(
            command_type=CommandTypeEnum.MONITOR_UNREGISTER,
            payload=payload,
        )

    async def ack_command(
        self,
        command_id: int,
        status: str = "done",
        message: Optional[str] = None,
    ) -> Optional[ExtensionCommand]:
        """명령 처리 완료/실패 보고"""
        cmd = await self.repo.get_async(command_id)
        if not cmd:
            return None
        new_status = (
            CommandStatusEnum.DONE if status == "done"
            else CommandStatusEnum.FAILED
        )
        return await self.repo.update_async(
            command_id,
            status=new_status,
            processed_at=datetime.now(tz=timezone.utc),
        )


class CollectionService:
    """수집 비즈니스 로직"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.setting_repo = CollectionSettingRepository(session)
        self.log_repo = CollectionLogRepository(session)
        self.product_service = ProductService(session)
        self.brand_repo = BrandRepository(session)
        self.price_calculator = PriceCalculator()
        self.seo_generator = SeoGenerator()

    async def create_setting(
        self, data: CollectionSettingCreateRequest,
    ) -> CollectionSetting:
        """수집 설정 생성"""
        return await self.setting_repo.create_async(
            name=data.name,
            source_id=data.source_id,
            brand_name=data.brand_name,
            category_url=data.category_url,
            max_count=data.max_count,
        )

    async def list_settings(self) -> List[CollectionSetting]:
        """수집 설정 목록"""
        return await self.setting_repo.list_async()

    async def get_setting(self, setting_id: int) -> Optional[CollectionSetting]:
        """수집 설정 조회"""
        return await self.setting_repo.get_async(setting_id)

    async def update_setting(
        self, setting_id: int, data: CollectionSettingUpdateRequest,
    ) -> Optional[CollectionSetting]:
        """수집 설정 수정"""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.setting_repo.get_async(setting_id)
        return await self.setting_repo.update_async(setting_id, **update_data)

    async def delete_setting(self, setting_id: int) -> bool:
        """수집 설정 삭제"""
        return await self.setting_repo.delete_async(setting_id)

    async def process_collected_product(
        self,
        source: str,
        product_data: ExtensionProductData,
        source_id: int,
        setting_id: Optional[int] = None,
    ) -> Dict:
        """
        수집된 상품 데이터 처리 (DB 저장 + 브랜드 IP 체크 + 가격 계산 + 로그).

        Returns:
            {"product": Product, "ip_warning": str | None}
        """
        # 1. 브랜드 지재권 확인 (경고만, 수집은 허용)
        ip_warning = None
        brand = await self.brand_repo.find_by_name(product_data.brand_name)
        if brand and not brand.is_ip_approved:
            ip_warning = f"브랜드 '{product_data.brand_name}'의 지재권이 미승인 상태입니다"
            logger.warning(ip_warning)

        # 2. 상품 저장
        product = await self.product_service.create_from_extension(
            source=source,
            data=product_data,
            source_id=source_id,
        )

        # 3. PriceCalculator로 판매가 계산 (Phase 1: 기본 계산만)
        try:
            selling_price = self.price_calculator.calculate(
                original_price=product_data.original_price,
                commission_rate=0.05,  # TODO: MarketTemplate에서 조회
                margin_rate=0.20,  # TODO: MarketTemplate에서 조회
            )
            logger.info(f"판매가 계산: {product_data.original_price}원 → {selling_price}원")
        except ValueError as e:
            logger.warning(f"판매가 계산 실패: {e}")

        # 4. SeoGenerator로 태그 생성
        tags = self.seo_generator.generate_tags(
            brand=product_data.brand_name,
            category="",
            product_name=product_data.name,
        )
        logger.info(f"SEO 태그 생성: {tags[:5]}...")

        # 5. 수집 로그 기록
        log_message = ip_warning if ip_warning else None
        await self.log_repo.create_async(
            setting_id=setting_id,
            product_name=product_data.name,
            status=LogStatusEnum.SUCCESS,
            message=log_message,
        )

        return {"product": product, "ip_warning": ip_warning}

    async def list_logs(
        self, limit: int = 50, skip: int = 0,
    ) -> List[CollectionLog]:
        """수집 로그 목록"""
        return await self.log_repo.list_async(skip=skip, limit=limit)
