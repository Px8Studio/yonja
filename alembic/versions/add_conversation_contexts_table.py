"""Add conversation_contexts table for ALEM scenario tracking

Revision ID: add_conversation_contexts
Revises: chainlit_tables_001
Create Date: 2026-01-22 04:35:00.000000

Stores conversation stage, farm context, and scenario parameters
for intelligent conversation routing and context preservation.
"""

import sqlalchemy as sa

from alembic import op

revision: str = "add_conversation_contexts"
down_revision: str | None = "chainlit_tables_001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create conversation_contexts table."""
    op.create_table(
        "conversation_contexts",
        sa.Column("scenario_id", sa.String(length=255), primary_key=True),
        sa.Column("user_id", sa.String(length=255), nullable=False, index=True),
        sa.Column("thread_id", sa.String(length=255), nullable=False, index=True),
        sa.Column(
            "crop_category",
            sa.String(length=100),
            nullable=True,
            comment="Crop category (e.g., Danli, Meyvə)",
        ),
        sa.Column(
            "specific_crop",
            sa.String(length=100),
            nullable=True,
            comment="Specific crop type (e.g., Buğda, Alma)",
        ),
        sa.Column("region", sa.String(length=100), nullable=True, comment="Agricultural region"),
        sa.Column("farm_size_ha", sa.Float(), nullable=True, comment="Farm size in hectares"),
        sa.Column(
            "experience_level",
            sa.String(length=50),
            nullable=True,
            comment="Farmer experience: novice, intermediate, expert",
        ),
        sa.Column("soil_type", sa.String(length=100), nullable=True, comment="Soil type"),
        sa.Column(
            "irrigation_type",
            sa.String(length=100),
            nullable=True,
            comment="Irrigation method",
        ),
        sa.Column(
            "current_month",
            sa.String(length=20),
            nullable=True,
            comment="Current planning month",
        ),
        sa.Column(
            "action_categories",
            sa.Text(),
            nullable=True,
            comment="JSON array of action categories",
        ),
        sa.Column(
            "expertise_areas",
            sa.Text(),
            nullable=True,
            comment="JSON array of expertise areas",
        ),
        sa.Column(
            "smart_question",
            sa.Text(),
            nullable=True,
            comment="Current SMART question to guide user",
        ),
        sa.Column("user_confirmed", sa.Boolean(), default=False, nullable=True),
        sa.Column(
            "conversation_stage",
            sa.String(length=50),
            nullable=True,
            comment="Current stage: profile_setup, planning, execution",
        ),
        sa.Column("settings_version", sa.Integer(), default=1),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            comment="Creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            comment="Last update timestamp",
        ),
        sa.UniqueConstraint("user_id", "thread_id", name="uq_conversation_user_thread"),
    )

    op.create_index("ix_conversation_contexts_user_id", "conversation_contexts", ["user_id"])
    op.create_index("ix_conversation_contexts_thread_id", "conversation_contexts", ["thread_id"])
    op.create_index("ix_conversation_contexts_updated_at", "conversation_contexts", ["updated_at"])


def downgrade() -> None:
    """Drop conversation_contexts table."""
    op.drop_index("ix_conversation_contexts_updated_at", table_name="conversation_contexts")
    op.drop_index("ix_conversation_contexts_thread_id", table_name="conversation_contexts")
    op.drop_index("ix_conversation_contexts_user_id", table_name="conversation_contexts")
    op.drop_table("conversation_contexts")
