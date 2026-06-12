"""Allow public read access to media for active listings only.

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-12
"""

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


LISTING_PHOTO_PUBLIC_POLICY = """
CREATE POLICY listing_photo_metadata_public_read ON listing_photo_metadata
FOR SELECT
USING (
    EXISTS (
        SELECT 1
        FROM listings l
        WHERE l.id = listing_photo_metadata.listing_id
          AND l.status = 'active'
          AND listing_photo_metadata.status IN ('accepted', 'warning')
    )
);
"""


DROP_LISTING_PHOTO_PUBLIC_POLICY = """
DROP POLICY IF EXISTS listing_photo_metadata_public_read ON listing_photo_metadata;
"""


def upgrade() -> None:
    op.execute(LISTING_PHOTO_PUBLIC_POLICY)


def downgrade() -> None:
    op.execute(DROP_LISTING_PHOTO_PUBLIC_POLICY)
