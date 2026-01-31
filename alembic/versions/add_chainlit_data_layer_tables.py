"""Add Chainlit data layer tables for user/thread/step persistence

Revision ID: chainlit_tables_001
Revises: 3fe49b8713dd
Create Date: 2026-01-19 00:40:00.000000

These tables are required by Chainlit's SQLAlchemyDataLayer to persist:
- users: OAuth user accounts (linked to Google OAuth identity)
- threads: Conversation threads/sessions
- steps: Individual messages/steps in a conversation
- elements: File attachments and media
- feedbacks: User feedback on steps (thumbs up/down)

Note: These are SEPARATE from the Yonca domain tables (user_profiles, farms, etc.)
The Chainlit users table stores OAuth identity; user_profiles stores farm/domain data.
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "chainlit_tables_001"  # pragma: allowlist secret
down_revision: str | None = "3fe49b8713dd"  # pragma: allowlist secret
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create Chainlit data layer tables."""

    # ========================================
    # USERS TABLE
    # Stores OAuth user identity for Chainlit
    # ========================================
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False, comment="UUID primary key"),
        sa.Column(
            "identifier",
            sa.String(length=255),
            nullable=False,
            comment="User identifier (email from OAuth)",
        ),
        sa.Column(
            "createdAt", sa.String(length=30), nullable=False, comment="ISO timestamp of creation"
        ),
        sa.Column(
            "metadata", sa.Text(), nullable=True, comment="JSON metadata including chat_settings"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_identifier", "users", ["identifier"], unique=True)

    # ========================================
    # THREADS TABLE
    # Stores conversation threads/sessions
    # ========================================
    op.create_table(
        "threads",
        sa.Column("id", sa.String(length=36), nullable=False, comment="UUID primary key"),
        sa.Column(
            "createdAt", sa.String(length=30), nullable=True, comment="ISO timestamp of creation"
        ),
        sa.Column("name", sa.String(length=255), nullable=True, comment="Thread name/title"),
        sa.Column("userId", sa.String(length=36), nullable=True, comment="FK to users.id"),
        sa.Column(
            "userIdentifier",
            sa.String(length=255),
            nullable=True,
            comment="User identifier (denormalized)",
        ),
        sa.Column("tags", sa.Text(), nullable=True, comment="JSON array of tags"),
        sa.Column("metadata", sa.Text(), nullable=True, comment="JSON metadata"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_threads_userId", "threads", ["userId"], unique=False)

    # ========================================
    # STEPS TABLE
    # Stores individual messages/steps in conversations
    # ========================================
    op.create_table(
        "steps",
        sa.Column("id", sa.String(length=36), nullable=False, comment="UUID primary key"),
        sa.Column("name", sa.String(length=255), nullable=True, comment="Step name"),
        sa.Column(
            "type",
            sa.String(length=50),
            nullable=True,
            comment="Step type (user_message, assistant_message, etc)",
        ),
        sa.Column("threadId", sa.String(length=36), nullable=True, comment="FK to threads.id"),
        sa.Column(
            "parentId",
            sa.String(length=36),
            nullable=True,
            comment="Parent step ID for nested steps",
        ),
        sa.Column("streaming", sa.Boolean(), nullable=True, comment="Whether step is streaming"),
        sa.Column(
            "waitForAnswer", sa.Boolean(), nullable=True, comment="Whether waiting for user answer"
        ),
        sa.Column("isError", sa.Boolean(), nullable=True, comment="Whether step resulted in error"),
        sa.Column("metadata", sa.Text(), nullable=True, comment="JSON metadata"),
        sa.Column("tags", sa.Text(), nullable=True, comment="JSON array of tags"),
        sa.Column("input", sa.Text(), nullable=True, comment="Step input content"),
        sa.Column("output", sa.Text(), nullable=True, comment="Step output content"),
        sa.Column(
            "createdAt", sa.String(length=30), nullable=True, comment="ISO timestamp of creation"
        ),
        sa.Column(
            "start", sa.String(length=30), nullable=True, comment="ISO timestamp of step start"
        ),
        sa.Column("end", sa.String(length=30), nullable=True, comment="ISO timestamp of step end"),
        sa.Column(
            "generation",
            sa.Text(),
            nullable=True,
            comment="JSON generation metadata (tokens, model, etc)",
        ),
        sa.Column(
            "showInput", sa.String(length=10), nullable=True, comment="Whether to show input"
        ),
        sa.Column(
            "language", sa.String(length=50), nullable=True, comment="Code language for code steps"
        ),
        sa.Column(
            "defaultOpen",
            sa.Boolean(),
            nullable=True,
            server_default="false",
            comment="Whether step is expanded by default (Chainlit 2.9+)",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_steps_threadId", "steps", ["threadId"], unique=False)

    # ========================================
    # ELEMENTS TABLE
    # Stores file attachments and media
    # ========================================
    op.create_table(
        "elements",
        sa.Column("id", sa.String(length=36), nullable=False, comment="UUID primary key"),
        sa.Column("threadId", sa.String(length=36), nullable=True, comment="FK to threads.id"),
        sa.Column(
            "type", sa.String(length=50), nullable=True, comment="Element type (image, file, etc)"
        ),
        sa.Column(
            "chainlitKey", sa.String(length=255), nullable=True, comment="Chainlit internal key"
        ),
        sa.Column("url", sa.Text(), nullable=True, comment="Element URL"),
        sa.Column("objectKey", sa.String(length=500), nullable=True, comment="Storage object key"),
        sa.Column("name", sa.String(length=255), nullable=True, comment="Element name/filename"),
        sa.Column("display", sa.String(length=50), nullable=True, comment="Display mode"),
        sa.Column("size", sa.String(length=50), nullable=True, comment="Element size"),
        sa.Column("language", sa.String(length=50), nullable=True, comment="Code language"),
        sa.Column("page", sa.Integer(), nullable=True, comment="Page number for PDFs"),
        sa.Column("autoPlay", sa.Boolean(), nullable=True, comment="Auto-play for media"),
        sa.Column("playerConfig", sa.Text(), nullable=True, comment="JSON player configuration"),
        sa.Column("forId", sa.String(length=36), nullable=True, comment="Associated step ID"),
        sa.Column("mime", sa.String(length=100), nullable=True, comment="MIME type"),
        sa.Column("props", sa.Text(), nullable=True, comment="JSON additional properties"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_elements_threadId", "elements", ["threadId"], unique=False)
    op.create_index("ix_elements_forId", "elements", ["forId"], unique=False)

    # ========================================
    # FEEDBACKS TABLE
    # Stores user feedback on steps (thumbs up/down)
    # ========================================
    op.create_table(
        "feedbacks",
        sa.Column("id", sa.String(length=36), nullable=False, comment="UUID primary key"),
        sa.Column(
            "forId", sa.String(length=36), nullable=True, comment="Step ID this feedback is for"
        ),
        sa.Column("threadId", sa.String(length=36), nullable=True, comment="Thread ID"),
        sa.Column(
            "value", sa.Integer(), nullable=True, comment="Feedback value (1=positive, -1=negative)"
        ),
        sa.Column("comment", sa.Text(), nullable=True, comment="Optional feedback comment"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_feedbacks_forId", "feedbacks", ["forId"], unique=False)


def downgrade() -> None:
    """Drop Chainlit data layer tables."""
    op.drop_index("ix_feedbacks_forId", table_name="feedbacks")
    op.drop_table("feedbacks")

    op.drop_index("ix_elements_forId", table_name="elements")
    op.drop_index("ix_elements_threadId", table_name="elements")
    op.drop_table("elements")

    op.drop_index("ix_steps_threadId", table_name="steps")
    op.drop_table("steps")

    op.drop_index("ix_threads_userId", table_name="threads")
    op.drop_table("threads")

    op.drop_index("ix_users_identifier", table_name="users")
    op.drop_table("users")
