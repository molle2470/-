"""마켓 등록 라우터 import + prefix 테스트."""
import sys
from unittest.mock import MagicMock, AsyncMock

_mock_orm = MagicMock()
_mock_orm.get_read_session_dependency = MagicMock(return_value=AsyncMock())
_mock_orm.get_write_session_dependency = MagicMock(return_value=AsyncMock())
if "backend.db.orm" not in sys.modules:
    sys.modules["backend.db.orm"] = _mock_orm

_mock_config = MagicMock()
_mock_config.settings = MagicMock(
    naver_client_id="test_id",
    naver_client_secret="test_secret",
    naver_channel_id="test_channel",
)
if "backend.core.config" not in sys.modules:
    sys.modules["backend.core.config"] = _mock_config


def test_market_listings_router_imports():
    from backend.api.v1.routers.market_listings import router
    assert router is not None


def test_router_has_correct_prefix():
    from backend.api.v1.routers.market_listings import router
    assert router.prefix == "/market-listings"
