"""add product_seo table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-20 00:01:00.000000
"""
from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "product_seo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("market_type", sa.String(50), nullable=False, server_default="naver"),
        sa.Column("optimized_name", sa.String(200), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("naver_category_id", sa.String(100), nullable=True),
        sa.Column("brand", sa.String(200), nullable=False),
        sa.Column("material", sa.String(500), nullable=True),
        sa.Column("color", sa.String(200), nullable=True),
        sa.Column("gender", sa.String(50), nullable=True),
        sa.Column("age_group", sa.String(50), nullable=False, server_default="성인"),
        sa.Column("origin", sa.String(100), nullable=False, server_default="해외"),
        sa.Column("status", sa.String(20), nullable=False, server_default="generated"),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "market_type", name="uq_product_market_seo"),
    )
    op.create_index("ix_product_seo_product_id", "product_seo", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_product_seo_product_id", table_name="product_seo")
    op.drop_table("product_seo")
