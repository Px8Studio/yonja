"""Add farm_scenario_plans table for dynamic user planning

Revision ID: add_farm_scenario_plans
Revises: 4b2958026efd
Create Date: 2026-01-21 15:30:00.000000

This table stores user-configured farm scenarios from Chainlit chat settings.
It tracks evolving parameters during conversations and enables the rules engine
to generate month-by-month agrotechnological calendar plans.

Strategic Location: Placed in main yonca database alongside user_profiles and
farm_profiles for tight integration with existing user/farm relationships.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_farm_scenario_plans"
down_revision: str | None = "4b2958026efd"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create farm_scenario_plans table."""
    op.create_table(
        "farm_scenario_plans",
        sa.Column(
            "scenario_id",
            sa.String(length=36),
            nullable=False,
            comment="UUID for scenario (e.g., uuid4())",
        ),
        sa.Column(
            "user_id",
            sa.String(length=20),
            nullable=False,
            comment="Links to user_profiles.user_id",
        ),
        sa.Column(
            "thread_id",
            sa.String(length=50),
            nullable=True,
            comment="Links to Chainlit thread for session tracking",
        ),
        # ═══════════════════════════════════════════════════════════════
        # FARM PROFILE PARAMETERS (from chat settings)
        # ═══════════════════════════════════════════════════════════════
        sa.Column(
            "crop_category",
            sa.String(length=20),
            nullable=False,
            comment="Danli, Taravaz, Texniki, Yem, Meyva (Yonca mobile app categories)",
        ),
        sa.Column(
            "specific_crop",
            sa.String(length=30),
            nullable=False,
            comment="Pambiq, Bugda, Kalam, etc.",
        ),
        sa.Column(
            "region",
            sa.String(length=30),
            nullable=False,
            comment="Aran, Quba-Xacmaz, Lenkaran-Astara, etc.",
        ),
        sa.Column(
            "farm_size_ha",
            sa.Float(),
            nullable=False,
            comment="Farm size in hectares (0.5-500)",
        ),
        sa.Column(
            "experience_level",
            sa.String(length=20),
            nullable=False,
            comment="novice, intermediate, expert",
        ),
        sa.Column(
            "soil_type",
            sa.String(length=20),
            nullable=False,
            comment="Gilli/Clay, Qumlu/Sandy, Lopam/Loam, Soranli/Saline",
        ),
        sa.Column(
            "irrigation_type",
            sa.String(length=20),
            nullable=False,
            comment="Damci/Drip, Pivot, Sirim/Flood, Yagis/Rainfed",
        ),
        # ═══════════════════════════════════════════════════════════════
        # PLANNING PARAMETERS
        # ═══════════════════════════════════════════════════════════════
        sa.Column(
            "current_month",
            sa.String(length=10),
            nullable=False,
            comment="January-December (normalized from Yanvar/January)",
        ),
        sa.Column(
            "action_categories",
            postgresql.JSONB(),
            nullable=True,
            comment="Array of selected categories: ['Ekin', 'Suvarma', 'Gubreleme', etc.]",
        ),
        sa.Column(
            "expertise_areas",
            postgresql.JSONB(),
            nullable=True,
            comment="Array of expertise IDs: ['cotton', 'wheat', 'orchard', etc.]",
        ),
        # ═══════════════════════════════════════════════════════════════
        # GENERATED PLAN (from rules engine)
        # ═══════════════════════════════════════════════════════════════
        sa.Column(
            "monthly_plan",
            postgresql.JSONB(),
            nullable=True,
            comment="Generated agrotechnological calendar plan {month: {week1: [...], week2: [...]}}",
        ),
        sa.Column(
            "smart_question",
            sa.Text(),
            nullable=True,
            comment="Last smart yes/no question posed to user to advance conversation",
        ),
        sa.Column(
            "user_confirmed",
            sa.Boolean(),
            nullable=True,
            comment="Whether user accepted the last smart question (null=pending, true=yes, false=no)",
        ),
        # ═══════════════════════════════════════════════════════════════
        # CONVERSATIONAL STATE
        # ═══════════════════════════════════════════════════════════════
        sa.Column(
            "conversation_stage",
            sa.String(length=30),
            nullable=False,
            server_default="profile_setup",
            comment="profile_setup, planning_active, plan_confirmed, executing",
        ),
        sa.Column(
            "language_preference",
            sa.String(length=10),
            nullable=False,
            server_default="az",
            comment="az, en, ru",
        ),
        sa.Column(
            "settings_version",
            sa.Integer(),
            nullable=False,
            server_default="1",
            comment="Increments each time user updates chat settings (tracks evolution)",
        ),
        # ═══════════════════════════════════════════════════════════════
        # TIMESTAMPS
        # ═══════════════════════════════════════════════════════════════
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "last_interaction_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Last time user interacted with this scenario",
        ),
        # ═══════════════════════════════════════════════════════════════
        # CONSTRAINTS
        # ═══════════════════════════════════════════════════════════════
        sa.PrimaryKeyConstraint("scenario_id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user_profiles.user_id"],
            ondelete="CASCADE",
        ),
    )

    # Indexes for efficient queries
    op.create_index(
        op.f("ix_farm_scenario_plans_user_id"),
        "farm_scenario_plans",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_farm_scenario_plans_thread_id"),
        "farm_scenario_plans",
        ["thread_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_farm_scenario_plans_conversation_stage"),
        "farm_scenario_plans",
        ["conversation_stage"],
        unique=False,
    )

    # Trigger to auto-update updated_at timestamp
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_farm_scenario_plans_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER farm_scenario_plans_updated_at_trigger
        BEFORE UPDATE ON farm_scenario_plans
        FOR EACH ROW
        EXECUTE FUNCTION update_farm_scenario_plans_updated_at();
    """
    )


def downgrade() -> None:
    """Drop farm_scenario_plans table."""
    op.execute(
        "DROP TRIGGER IF EXISTS farm_scenario_plans_updated_at_trigger ON farm_scenario_plans"
    )
    op.execute("DROP FUNCTION IF EXISTS update_farm_scenario_plans_updated_at()")
    op.drop_index(
        op.f("ix_farm_scenario_plans_conversation_stage"), table_name="farm_scenario_plans"
    )
    op.drop_index(op.f("ix_farm_scenario_plans_thread_id"), table_name="farm_scenario_plans")
    op.drop_index(op.f("ix_farm_scenario_plans_user_id"), table_name="farm_scenario_plans")
    op.drop_table("farm_scenario_plans")
