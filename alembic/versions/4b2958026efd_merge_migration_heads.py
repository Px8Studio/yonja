"""merge migration heads

Revision ID: 4b2958026efd
Revises: add_fin_oidc_identity, fix_tags_jsonb
Create Date: 2026-01-19 21:41:28.797286

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b2958026efd'
down_revision: Union[str, Sequence[str], None] = ('add_fin_oidc_identity', 'fix_tags_jsonb')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
