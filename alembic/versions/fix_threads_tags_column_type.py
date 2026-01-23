"""Fix threads tags column to use jsonb instead of text

Revision ID: fix_threads_tags_jsonb
Revises: fix_steps_tags_001
Create Date: 2026-01-22 04:30:00.000000

The threads.tags column was TEXT but Chainlit sends Python lists.
This causes: "invalid input for query argument $3: ['tag'] (expected str, got list)"

Fix: Convert to JSONB to properly store JSON arrays, matching steps.tags pattern.
"""
# pylint: disable=invalid-name,no-member

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "fix_threads_tags_jsonb"
down_revision = ("rename_farm_scenario", "add_chainlit_files_table")
branch_labels = None
depends_on = None


def upgrade():
    """Convert threads.tags from TEXT to JSONB."""
    # First, clean up invalid data
    op.execute(
        sa.text(
            """
            UPDATE threads
            SET tags = '[]'::jsonb
            WHERE tags = '' OR tags IS NULL
        """
        )
    )

    # Convert remaining valid JSON text to JSONB
    op.execute(
        sa.text(
            """
            UPDATE threads
            SET tags = tags::jsonb
            WHERE tags IS NOT NULL AND tags != ''
        """
        )
    )

    # Now alter column type to JSONB
    op.alter_column(
        "threads",
        "tags",
        existing_type=sa.Text(),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=True,
        postgresql_using="tags::jsonb",
    )


def downgrade():
    """Convert threads.tags back from JSONB to TEXT."""
    # Convert JSONB back to text representation
    op.alter_column(
        "threads",
        "tags",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=sa.Text(),
        existing_nullable=True,
        postgresql_using="tags::text",
    )
