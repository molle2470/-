"""add collection_settings, collection_logs, extension_commands tables

Revision ID: a1b2c3d4e5f6
Revises: None
Create Date: 2026-03-19 00:00:00.000000

"""
from typing import Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    # collection_settings 테이블 생성
    op.create_table(
        "collection_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("brand_name", sa.String(200), nullable=False),
        sa.Column("category_url", sa.Text(), nullable=False),
        sa.Column("max_count", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_collection_settings_source_id",
        "collection_settings",
        ["source_id"],
    )
    op.create_index(
        "ix_collection_settings_is_active",
        "collection_settings",
        ["is_active"],
    )

    # collection_logs 테이블 생성
    op.create_table(
        "collection_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "setting_id",
            sa.Integer(),
            sa.ForeignKey("collection_settings.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("product_name", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_collection_logs_created_at",
        "collection_logs",
        ["created_at"],
    )

    # extension_commands 테이블 생성 (Task 2에서 message 컬럼 추가됨)
    op.create_table(
        "extension_commands",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("command_type", sa.String(50), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("message", sa.Text(), nullable=True),  # Task 2에서 추가된 필드
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_extension_commands_status",
        "extension_commands",
        ["status"],
    )

    # Product.brand_id를 nullable로 변경 (기존 DB 호환 — products 테이블이 있을 때만 실행)
    bind = op.get_bind()
    inspector = inspect(bind)
    if "products" in inspector.get_table_names():
        op.alter_column("products", "brand_id", nullable=True)


def downgrade() -> None:
    # Product.brand_id를 다시 non-nullable로 되돌림 (products 테이블이 있을 때만 실행)
    bind = op.get_bind()
    inspector = inspect(bind)
    if "products" in inspector.get_table_names():
        op.alter_column("products", "brand_id", nullable=False)

    # extension_commands 테이블 삭제
    op.drop_index("ix_extension_commands_status", table_name="extension_commands")
    op.drop_table("extension_commands")

    # collection_logs 테이블 삭제
    op.drop_index("ix_collection_logs_created_at", table_name="collection_logs")
    op.drop_table("collection_logs")

    # collection_settings 테이블 삭제
    op.drop_index("ix_collection_settings_is_active", table_name="collection_settings")
    op.drop_index(
        "ix_collection_settings_source_id", table_name="collection_settings"
    )
    op.drop_table("collection_settings")
