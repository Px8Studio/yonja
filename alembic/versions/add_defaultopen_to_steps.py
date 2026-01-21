"""🌿 Add defaultOpen column to steps table for Chainlit 2.9.x compatibility.

Chainlit 2.9.x added a 'defaultOpen' field to the Step class that controls
whether step details are expanded by default in the UI. This migration adds
the missing column to existing databases.

Revision ID: add_defaultopen_steps
Revises: chainlit_tables_001
Create Date: 2026-01-19

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_defaultopen_steps"
down_revision = "chainlit_tables_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add defaultOpen column to steps table for Chainlit 2.9.x."""
    # Check if column exists (safe for re-runs)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("steps")]

    if "defaultOpen" not in columns:
        op.add_column(
            "steps",
            sa.Column(
                "defaultOpen",
                sa.Boolean(),
                nullable=True,
                server_default="false",
                comment="Whether step is expanded by default (Chainlit 2.9+)",
            ),
        )


def downgrade() -> None:
    """Remove defaultOpen column from steps table."""
    op.drop_column("steps", "defaultOpen")
