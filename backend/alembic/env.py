"""Alembic 환경 설정 — SQLModel 메타데이터 연동."""
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
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


def run_migrations_offline() -> None:
    """오프라인 모드 — DB 연결 없이 SQL 스크립트만 생성."""
    url = config.get_main_option("sqlalchemy.url")
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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
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
