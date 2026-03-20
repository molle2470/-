"""상품 SEO 라우터 테스트."""
import sys
from unittest.mock import MagicMock, AsyncMock

# DB/settings mock — 테스트 환경에서 실제 DB 연결 없이 라우터 import 가능하게
_mock_orm = MagicMock()
_mock_orm.get_read_session_dependency = MagicMock(return_value=AsyncMock())
_mock_orm.get_write_session_dependency = MagicMock(return_value=AsyncMock())
if "backend.db.orm" not in sys.modules:
    sys.modules["backend.db.orm"] = _mock_orm


def test_products_router_has_seo_get():
    """GET /products/{id}/seo 라우트 존재 확인"""
    from backend.api.v1.routers.products import router
    paths = [r.path for r in router.routes]
    # prefix 포함(/products/...) 또는 미포함 둘 다 허용
    assert any("/{product_id}/seo" in p for p in paths)


def test_products_router_has_seo_patch():
    """PATCH /products/{id}/seo 라우트 존재 확인"""
    from backend.api.v1.routers.products import router
    routes = {r.path: r.methods for r in router.routes if hasattr(r, "methods")}
    # prefix 포함(/products/...) 또는 미포함 둘 다 허용
    seo_methods = set()
    for path, methods in routes.items():
        if "/{product_id}/seo" in path:
            seo_methods |= methods
    assert "PATCH" in seo_methods
