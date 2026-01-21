"""merge migration heads

Revision ID: 4b2958026efd
Revises: add_fin_oidc_identity, fix_tags_jsonb
Create Date: 2026-01-19 21:41:28.797286

"""

# revision identifiers, used by Alembic.
revision: str = "4b2958026efd"
down_revision: str | None = ("add_fin_oidc_001", "make_chainlit_nullable_001")
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
