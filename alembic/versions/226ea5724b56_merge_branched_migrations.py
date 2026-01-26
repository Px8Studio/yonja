"""merge_branched_migrations

Revision ID: 226ea5724b56
Revises: add_conversation_contexts, fix_threads_tags_jsonb
Create Date: 2026-01-25 02:48:49.480194

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "226ea5724b56"
down_revision: str | Sequence[str] | None = (
    "add_conversation_contexts",
    "fix_threads_tags_jsonb",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
