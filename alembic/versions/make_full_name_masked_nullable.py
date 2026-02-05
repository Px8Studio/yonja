"""Make full_name_masked nullable for real OAuth users.

The full_name_masked field was originally required for all synthetic users.
However, real users authenticated via mygov ID will have first_name/last_name
populated instead. Making this nullable allows real users to exist without
the legacy masked name field.

Revision ID: make_fullname_nullable
Revises: 226ea5724b56
Create Date: 2026-02-05 10:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "make_fullname_nullable"
down_revision = "226ea5724b56"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make full_name_masked nullable."""
    op.alter_column(
        "user_profiles",
        "full_name_masked",
        existing_type=sa.String(50),
        nullable=True,
        comment="Masked name (e.g., [ŞƏXS_001]) - DEPRECATED: use first_name/last_name",
    )


def downgrade() -> None:
    """Revert to non-nullable (only safe if all rows have values)."""
    # First, fill any NULL values with a placeholder
    op.execute(
        "UPDATE user_profiles SET full_name_masked = '[MIGRATION_PLACEHOLDER]' "
        "WHERE full_name_masked IS NULL"
    )
    op.alter_column(
        "user_profiles",
        "full_name_masked",
        existing_type=sa.String(50),
        nullable=False,
        comment="Masked name (e.g., [ŞƏXS_001]) - DEPRECATED: use first_name/last_name",
    )
