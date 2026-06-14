"""Add public read RLS policy for active viewing slots on active listings.

Revision ID: 0014
Revises: 0013
Create Date: 2026-06-13
"""

from alembic import op


revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE POLICY listing_viewing_slots_public_read
        ON listing_viewing_slots
        FOR SELECT
        USING (
            status = 'active'
            AND EXISTS (
                SELECT 1
                FROM listings
                WHERE listings.id = listing_viewing_slots.listing_id
                  AND listings.status = 'active'
            )
        );
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP POLICY IF EXISTS listing_viewing_slots_public_read
        ON listing_viewing_slots;
        """
    )
