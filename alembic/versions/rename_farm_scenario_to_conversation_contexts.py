"""Rename farm_scenario_plans to conversation_contexts

Revision ID: rename_farm_scenario
Revises: 4b2958026efd
Create Date: 2026-01-21 12:00:00.000000

This migration renames the farm_scenario_plans table to conversation_contexts
to better reflect its actual purpose: storing conversation parameters and
agent session profiles rather than physical farm plans.

Backward compatibility is maintained via a database view.
"""


from alembic import op

# revision identifiers, used by Alembic.
revision: str = "rename_farm_scenario"
down_revision: str | None = "fix_steps_tags_001"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = "add_farm_scenario_plans"


def upgrade() -> None:
    """Rename table with backward compatibility view."""

    # Rename the table
    op.rename_table("farm_scenario_plans", "conversation_contexts")

    # Rename indexes
    op.execute(
        "ALTER INDEX ix_farm_scenario_plans_user_id RENAME TO ix_conversation_contexts_user_id"
    )
    op.execute(
        "ALTER INDEX ix_farm_scenario_plans_thread_id RENAME TO ix_conversation_contexts_thread_id"
    )
    op.execute(
        "ALTER INDEX ix_farm_scenario_plans_conversation_stage RENAME TO ix_conversation_contexts_conversation_stage"
    )

    # Rename trigger function
    op.execute(
        """
        ALTER FUNCTION update_farm_scenario_plans_updated_at()
        RENAME TO update_conversation_contexts_updated_at
    """
    )

    # Drop old trigger and create new one
    op.execute(
        "DROP TRIGGER IF EXISTS farm_scenario_plans_updated_at_trigger ON conversation_contexts"
    )
    op.execute(
        """
        CREATE TRIGGER conversation_contexts_updated_at_trigger
        BEFORE UPDATE ON conversation_contexts
        FOR EACH ROW
        EXECUTE FUNCTION update_conversation_contexts_updated_at()
    """
    )

    # Create backward compatibility view for old code
    op.execute(
        """
        CREATE OR REPLACE VIEW farm_scenario_plans AS
        SELECT * FROM conversation_contexts
    """
    )

    # Add comment to explain the table's purpose
    op.execute(
        """
        COMMENT ON TABLE conversation_contexts IS
        'Stores conversation parameters and agent session profiles.
        These are NOT physical farm plans but rather the contextual parameters
        that define agent behavior (crop type, region, expertise level, etc.)
        for role-play and hypothetical reasoning in conversations.'
    """
    )


def downgrade() -> None:
    """Restore original table name."""

    # Drop the view
    op.execute("DROP VIEW IF EXISTS farm_scenario_plans")

    # Rename trigger
    op.execute(
        "DROP TRIGGER IF EXISTS conversation_contexts_updated_at_trigger ON conversation_contexts"
    )
    op.execute(
        """
        CREATE TRIGGER farm_scenario_plans_updated_at_trigger
        BEFORE UPDATE ON farm_scenario_plans
        FOR EACH ROW
        EXECUTE FUNCTION update_farm_scenario_plans_updated_at()
    """
    )

    # Rename function back
    op.execute(
        """
        ALTER FUNCTION update_conversation_contexts_updated_at()
        RENAME TO update_farm_scenario_plans_updated_at
    """
    )

    # Rename indexes back
    op.execute(
        "ALTER INDEX ix_conversation_contexts_user_id RENAME TO ix_farm_scenario_plans_user_id"
    )
    op.execute(
        "ALTER INDEX ix_conversation_contexts_thread_id RENAME TO ix_farm_scenario_plans_thread_id"
    )
    op.execute(
        "ALTER INDEX ix_conversation_contexts_conversation_stage RENAME TO ix_farm_scenario_plans_conversation_stage"
    )

    # Rename table back
    op.rename_table("conversation_contexts", "farm_scenario_plans")
