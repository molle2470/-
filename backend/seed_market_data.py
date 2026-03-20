"""마켓 등록 파이프라인 초기 DB 데이터 삽입 스크립트.

실행 방법:
  cd backend
  .venv/Scripts/activate
  python seed_market_data.py

삽입 대상:
  1. common_templates - A/S 전화번호 포함 공통 템플릿
  2. markets - 네이버 스마트스토어
  3. business_groups - 기본 사업자 그룹
  4. market_accounts - 네이버 계정
  5. market_templates - 수수료 8%, 반품 5000원
"""
import asyncio
import os
import sys
from datetime import datetime, timezone

# backend 패키지 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

from backend.core.config import settings
from backend.domain.market.model import (
    BusinessGroup,
    Market,
    MarketAccount,
    MarketTemplate,
    CommonTemplate,
)


def get_write_db_url() -> str:
    ssl = "?ssl=require" if settings.use_db_ssl else ""
    return (
        f"postgresql+asyncpg://{settings.write_db_user}:{settings.write_db_password}"
        f"@{settings.write_db_host}:{settings.write_db_port}/{settings.write_db_name}{ssl}"
    )


async def seed():
    engine = create_async_engine(get_write_db_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 1. 공통 템플릿
        result = await session.execute(select(CommonTemplate).limit(1))
        existing_template = result.scalar_one_or_none()

        if not existing_template:
            common_template = CommonTemplate(
                shipping_origin="서울 강남구",
                return_address="서울 강남구",
                courier="CJ대한통운",
                as_phone="02-0000-0000",
                as_description="소비자분쟁해결기준에 의거 교환 및 환불",
                origin_country="기타",
                updated_at=datetime.now(tz=timezone.utc),
            )
            session.add(common_template)
            await session.flush()
            print(f"✅ CommonTemplate 생성 (id={common_template.id})")
        else:
            common_template = existing_template
            print(f"ℹ️  CommonTemplate 이미 존재 (id={common_template.id})")

        # 2. 네이버 스마트스토어 마켓
        result = await session.execute(
            select(Market).where(Market.name == "네이버 스마트스토어")
        )
        existing_market = result.scalar_one_or_none()

        if not existing_market:
            market = Market(
                name="네이버 스마트스토어",
                created_at=datetime.now(tz=timezone.utc),
            )
            session.add(market)
            await session.flush()
            print(f"✅ Market 생성 (id={market.id})")
        else:
            market = existing_market
            print(f"ℹ️  Market 이미 존재 (id={market.id})")

        # 3. 사업자 그룹
        result = await session.execute(select(BusinessGroup).limit(1))
        existing_group = result.scalar_one_or_none()

        if not existing_group:
            group = BusinessGroup(
                name="기본 사업자",
                created_at=datetime.now(tz=timezone.utc),
            )
            session.add(group)
            await session.flush()
            print(f"✅ BusinessGroup 생성 (id={group.id})")
        else:
            group = existing_group
            print(f"ℹ️  BusinessGroup 이미 존재 (id={group.id})")

        # 4. 마켓 계정
        result = await session.execute(
            select(MarketAccount).where(
                MarketAccount.market_id == market.id,
                MarketAccount.business_group_id == group.id,
            )
        )
        existing_account = result.scalar_one_or_none()

        if not existing_account:
            account = MarketAccount(
                business_group_id=group.id,
                market_id=market.id,
                account_id="스마트스토어_판매자_아이디",
                is_active=True,
                created_at=datetime.now(tz=timezone.utc),
                updated_at=datetime.now(tz=timezone.utc),
            )
            session.add(account)
            await session.flush()
            print(f"✅ MarketAccount 생성 (id={account.id})")
        else:
            account = existing_account
            print(f"ℹ️  MarketAccount 이미 존재 (id={account.id})")

        # 5. 마켓 템플릿 (수수료 8%, 반품 5000원)
        result = await session.execute(
            select(MarketTemplate).where(
                MarketTemplate.market_id == market.id,
                MarketTemplate.common_template_id == common_template.id,
            )
        )
        existing_mt = result.scalar_one_or_none()

        if not existing_mt:
            mt = MarketTemplate(
                market_id=market.id,
                common_template_id=common_template.id,
                commission_rate=0.08,
                margin_rate=0.20,
                shipping_fee=0,
                return_fee=5000,
                updated_at=datetime.now(tz=timezone.utc),
            )
            session.add(mt)
            await session.flush()
            print(f"✅ MarketTemplate 생성 (id={mt.id})")
        else:
            mt = existing_mt
            print(f"ℹ️  MarketTemplate 이미 존재 (id={mt.id})")

        await session.commit()

        print()
        print("=" * 50)
        print("📌 프론트엔드 상수 설정 값:")
        print(f"   NAVER_MARKET_ACCOUNT_ID = {account.id}")
        print(f"   NAVER_MARKET_ID = {market.id}")
        print(f"   COMMON_TEMPLATE_ID = {common_template.id}")
        print("=" * 50)
        print()
        print("✅ ProductsTable.tsx에서 위 상수를 업데이트하세요.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
