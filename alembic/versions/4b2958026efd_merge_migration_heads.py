"""merge migration heads

Revision ID: 4b2958026efd
Revises: add_fin_oidc_identity, make_chainlit_user_nullable
Create Date: 2026-01-19 21:41:28.797286

"""

# revision identifiers, used by Alembic.
revision: str = "4b2958026efd"  # pragma: allowlist secret
down_revision: str | None = ("add_fin_oidc_identity", "make_chainlit_user_nullable")
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
