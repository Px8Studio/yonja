"""Make chainlit_user_id nullable for standalone demo personas

Revision ID: make_chainlit_user_nullable
Revises: add_alem_personas_001
Create Date: 2026-01-19 19:31:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'make_chainlit_user_nullable'
down_revision = 'add_alem_personas_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make chainlit_user_id nullable and remove unique constraint."""
    # Drop the unique constraint first
    op.drop_constraint('uq_alem_personas_user_id', 'alem_personas', type_='unique')
    
    # Make chainlit_user_id nullable
    op.alter_column('alem_personas', 'chainlit_user_id',
                    existing_type=sa.String(36),
                    nullable=True)


def downgrade() -> None:
    """Reverse the changes."""
    # Make chainlit_user_id not nullable again
    op.alter_column('alem_personas', 'chainlit_user_id',
                    existing_type=sa.String(36),
                    nullable=False)
    
    # Restore the unique constraint
    op.create_unique_constraint('uq_alem_personas_user_id', 'alem_personas', ['chainlit_user_id'])
