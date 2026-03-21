import asyncio
import backend.domain.source.model  # noqa
import backend.domain.brand.model  # noqa
import backend.domain.product.model  # noqa
import backend.domain.market.model  # noqa
import backend.domain.monitoring.model  # noqa
import backend.domain.collection.model  # noqa
import backend.domain.user.model  # noqa
import backend.domain.product.seo_model  # noqa

from backend.db.orm import get_write_session
from sqlalchemy import text

async def test():
    async with get_write_session() as session:
        # 기존 수집된 상품 확인
        r = await session.execute(text(
            "SELECT id, name, source_product_id, status FROM products ORDER BY id DESC LIMIT 10"
        ))
        products = r.fetchall()
        print("최근 수집 상품:")
        for p in products:
            print(f"  id={p[0]}, name={p[1][:30]}, source_product_id={p[2]}, status={p[3]}")

        # product_seo 확인
        r2 = await session.execute(text(
            "SELECT product_id, status FROM product_seo ORDER BY id DESC LIMIT 10"
        ))
        seos = r2.fetchall()
        print("\nproduct_seo 목록:")
        for s in seos:
            print(f"  product_id={s[0]}, status={s[1]}")

asyncio.run(test())
