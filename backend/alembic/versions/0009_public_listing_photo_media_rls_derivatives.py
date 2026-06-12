"""Allow public read access to listing photo rows that have public-safe derivatives.

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-12
"""

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


DROP_PUBLIC_POLICY = """
DROP POLICY IF EXISTS listing_photo_metadata_public_read ON listing_photo_metadata;
"""

CREATE_PUBLIC_POLICY = """
CREATE POLICY listing_photo_metadata_public_read ON listing_photo_metadata
FOR SELECT
USING (
    EXISTS (
        SELECT 1
        FROM listings l
        WHERE l.id = listing_photo_metadata.listing_id
          AND l.status = 'active'
    )
    AND (
        listing_photo_metadata.status IN ('accepted', 'warning')
        OR EXISTS (
            SELECT 1
            FROM listing_photo_derivatives d
            WHERE d.listing_photo_metadata_id = listing_photo_metadata.id
              AND d.is_public_safe = true
        )
    )
);
"""


def upgrade() -> None:
    op.execute(DROP_PUBLIC_POLICY)
    op.execute(CREATE_PUBLIC_POLICY)


def downgrade() -> None:
    op.execute(DROP_PUBLIC_POLICY)
