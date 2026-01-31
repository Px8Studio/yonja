"""Add conversation_contexts table for ALEM scenario tracking

Revision ID: add_conversation_contexts
Revises: chainlit_tables_001
Create Date: 2026-01-22 04:35:00.000000

Stores conversation stage, farm context, and scenario parameters
for intelligent conversation routing and context preservation.
"""


from alembic import op

revision: str = "add_conversation_contexts"
down_revision: str | None = "chainlit_tables_001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create conversation_contexts table.

    NOTE: Superseded by rename_farm_scenario_to_conversation_contexts.py
    This migration previously created a duplicate table locally.
    Disabling it to allow the rename migration to handle the table.
    """
    pass

    # Original code disabled:
    # op.create_table(
    #     "conversation_contexts",
    # ...


def downgrade() -> None:
    """Drop conversation_contexts table."""
    op.drop_index("ix_conversation_contexts_updated_at", table_name="conversation_contexts")
    op.drop_index("ix_conversation_contexts_thread_id", table_name="conversation_contexts")
    op.drop_index("ix_conversation_contexts_user_id", table_name="conversation_contexts")
    op.drop_table("conversation_contexts")
