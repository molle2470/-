from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.api.v1.routers.auth import router as auth_router
from backend.api.v1.routers.collection_logs import router as collection_logs_router
from backend.api.v1.routers.collection_settings import router as collection_settings_router
from backend.api.v1.routers.extension import router as extension_router
from backend.api.v1.routers.products import router as products_router
from backend.api.v1.routers.user import router as user_router
from backend.middleware.error_handler import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown validation."""
    # Startup validation
    if settings.mock_auth_enabled and settings.environment == "production":
        raise RuntimeError(
            "CRITICAL: Mock authentication cannot be enabled in production. "
            "Set MOCK_AUTH_ENABLED=false or ENVIRONMENT to non-production value."
        )

    if settings.mock_auth_enabled:
        import logging

        logging.warning(
            "Mock authentication is ENABLED. "
            "This should only be used for development/testing."
        )

    # TODO: 실제 크롤러/어댑터 연동 후 스케줄러 활성화
    # from backend.services.scheduler import MonitoringScheduler
    # from backend.db.orm import get_write_session
    # from backend.domain.crawling.musinsa_crawler import MusinsaCrawler
    # scheduler = MonitoringScheduler(
    #     session_factory=get_write_session,
    #     crawler=MusinsaCrawler(),
    #     sync_adapter=...,  # 실제 마켓 어댑터 주입
    # )
    # scheduler.start()

    yield

    # TODO: 스케줄러 종료
    # scheduler.stop()


def create_application() -> FastAPI:
    """Create and configure FastAPI application with API routes."""

    app = FastAPI(
        title="Backend API",
        version="1.0.0",
        description="Backend API",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_origin_regex=settings.cors_origin_regex,
    )

    # Register routers
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(user_router, prefix="/api/v1")
    app.include_router(extension_router, prefix="/api/v1")
    app.include_router(collection_settings_router, prefix="/api/v1")
    app.include_router(collection_logs_router, prefix="/api/v1")
    app.include_router(products_router, prefix="/api/v1")

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "name": "Backend API",
            "version": "1.0.0",
        }

    @app.get("/api/v1/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy"}

    return app


# Create the app instance
app = create_application()
