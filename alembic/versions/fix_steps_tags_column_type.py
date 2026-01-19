"""Fix steps tags column to use jsonb instead of text

Revision ID: fix_tags_jsonb
Revises: add_defaultopen_steps
Create Date: 2026-01-19 21:35:00.000000

The steps.tags column was TEXT but Chainlit sends Python lists.
This causes: "invalid input for query argument: ['tag'] (expected str, got list)"

Fix: Convert to JSONB to properly store JSON arrays.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'fix_tags_jsonb'
down_revision: Union[str, Sequence[str], None] = 'add_defaultopen_steps'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert steps.tags from TEXT to JSONB."""
    # Convert existing text values to valid JSON arrays
    # Empty strings → '[]'
    # NULL → NULL (stays null)
    op.execute("""
        UPDATE steps 
        SET tags = '[]'::jsonb 
        WHERE tags = '' OR tags IS NULL
    """)
    
    # Try to parse any existing non-empty text as JSON
    # If it fails, wrap in array
    op.execute("""
        UPDATE steps 
        SET tags = CASE 
            WHEN tags::text ~ '^\\[.*\\]$' THEN tags::jsonb
            ELSE ('["' || tags || '"]')::jsonb
        END
        WHERE tags IS NOT NULL AND tags != ''
    """)
    
    # Now alter column type to JSONB
    op.alter_column(
        'steps',
        'tags',
        existing_type=sa.Text(),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=True,
        postgresql_using='tags::jsonb',
    )


def downgrade() -> None:
    """Convert steps.tags back from JSONB to TEXT."""
    # Convert JSONB back to text representation
    op.alter_column(
        'steps',
        'tags',
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=sa.Text(),
        existing_nullable=True,
        postgresql_using='tags::text',
    )
