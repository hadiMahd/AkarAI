"""Add cities table as authoritative source of city names

Revision ID: 0017
Revises: 0016
Create Date: 2026-06-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | None = None
depends_on: str | None = None

LEBANESE_CITIES = [
    ("Beirut", "Lebanon"),
    ("Jounieh", "Lebanon"),
    ("Tripoli", "Lebanon"),
    ("Sidon", "Lebanon"),
    ("Tyre", "Lebanon"),
    ("Zahle", "Lebanon"),
    ("Byblos", "Lebanon"),
    ("Aley", "Lebanon"),
]


def upgrade() -> None:
    op.create_table(
        "cities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("country", sa.String(128), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_index("ix_cities_name", "cities", ["name"])
    op.create_index("ix_cities_is_active", "cities", ["is_active"])

    cities_table = sa.table(
        "cities",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("country", sa.String),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        cities_table,
        [
            {
                "id": str(__import__("uuid").uuid4()),
                "name": name,
                "country": country,
                "is_active": True,
            }
            for name, country in LEBANESE_CITIES
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_cities_is_active", table_name="cities")
    op.drop_index("ix_cities_name", table_name="cities")
    op.drop_table("cities")
