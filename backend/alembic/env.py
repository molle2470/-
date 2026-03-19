"""Alembic 환경 설정 — SQLModel 메타데이터 연동."""
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool
from sqlmodel import SQLModel

# backend 패키지를 sys.path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 모든 모델 임포트 (메타데이터 등록을 위해 필요)
import backend.domain.brand.model  # noqa: F401
import backend.domain.source.model  # noqa: F401
import backend.domain.product.model  # noqa: F401
import backend.domain.market.model  # noqa: F401
import backend.domain.monitoring.model  # noqa: F401
import backend.domain.collection.model  # noqa: F401
import backend.domain.user.model  # noqa: F401

# Alembic Config 객체
config = context.config

# 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLModel 메타데이터 사용 (autogenerate 지원)
target_metadata = SQLModel.metadata


def _get_db_url() -> str:
    """settings에서 write DB URL을 읽어 동기 드라이버로 변환하여 반환."""
    from backend.core.config import settings

    # write DB 접속 정보로 URL 직접 조합
    url = (
        f"postgresql://{settings.write_db_user}:{settings.write_db_password}"
        f"@{settings.write_db_host}:{settings.write_db_port}/{settings.write_db_name}"
    )
    # SSL 설정 추가
    if getattr(settings, 'use_db_ssl', False):
        url += "?sslmode=require"
    return url


def run_migrations_offline() -> None:
    """오프라인 모드 — DB 연결 없이 SQL 스크립트만 생성."""
    url = _get_db_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """온라인 모드 — 실제 DB에 마이그레이션 적용."""
    # alembic.ini의 플레이스홀더 대신 settings에서 DB URL을 읽어 사용
    db_url = _get_db_url()

    connectable = create_engine(
        db_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
