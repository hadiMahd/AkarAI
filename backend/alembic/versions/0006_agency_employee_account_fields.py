"""Add employee account profile fields to agency memberships

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-11
"""

from alembic import op
import sqlalchemy as sa


revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agency_employee_memberships",
        sa.Column("display_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "agency_employee_memberships",
        sa.Column("work_email", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("agency_employee_memberships", "work_email")
    op.drop_column("agency_employee_memberships", "display_name")
