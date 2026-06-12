"""Add composite indexes on listings for public browse patterns

Revision ID: 0010
Revises: 0009_public_listing_photo_media_rls_derivatives
Create Date: 2026-06-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("SAVEPOINT sp;")

    op.create_index(
        "ix_listings_status_created_at_id",
        "listings",
        [sa.text("status DESC"),
         sa.text("created_at DESC"),
         sa.text("id DESC")],
        postgresql_using="btree",
    )
    op.create_index(
        "ix_listings_status_price_desc_id",
        "listings",
        [sa.text("status DESC"),
         sa.text("price DESC NULLS LAST"),
         sa.text("id DESC")],
        postgresql_using="btree",
    )
    op.create_index(
        "ix_listings_status_price_asc_id",
        "listings",
        [sa.text("status DESC"),
         sa.text("price ASC NULLS LAST"),
         sa.text("id DESC")],
        postgresql_using="btree",
    )
    op.create_index(
        "ix_listings_status_area_size_desc_id",
        "listings",
        [sa.text("status DESC"),
         sa.text("area_size DESC NULLS LAST"),
         sa.text("id DESC")],
        postgresql_using="btree",
    )
    op.create_index(
        "ix_listings_status_area_size_asc_id",
        "listings",
        [sa.text("status DESC"),
         sa.text("area_size ASC NULLS LAST"),
         sa.text("id DESC")],
        postgresql_using="btree",
    )
    op.create_index(
        "ix_listings_status_city",
        "listings",
        ["status", "city"],
        postgresql_using="btree",
    )


def downgrade() -> None:
    op.drop_index("ix_listings_status_created_at_id", table_name="listings")
    op.drop_index("ix_listings_status_price_desc_id", table_name="listings")
    op.drop_index("ix_listings_status_price_asc_id", table_name="listings")
    op.drop_index("ix_listings_status_area_size_desc_id", table_name="listings")
    op.drop_index("ix_listings_status_area_size_asc_id", table_name="listings")
    op.drop_index("ix_listings_status_city", table_name="listings")
