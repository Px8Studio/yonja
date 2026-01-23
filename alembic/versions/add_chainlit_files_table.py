"""Add chainlit_files table for PostgreSQL file storage

Revision ID: add_chainlit_files_table
Revises: rename_farm_scenario, add_farm_scenario_plans
Create Date: 2026-01-22 12:00:00.000000

This table stores all file uploads (audio, video, images, documents) directly
in PostgreSQL using BYTEA columns. This ensures full data residency without
relying on external blob storage services (S3, Azure, GCS).

Benefits:
- Complete data sovereignty - all data stays in your database
- Single backup includes all files
- ACID compliance for file operations
- No external service dependencies
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_chainlit_files_table"
down_revision: tuple[str, ...] = ("rename_farm_scenario", "add_farm_scenario_plans")
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create chainlit_files table for PostgreSQL-based file storage."""

    op.create_table(
        "chainlit_files",
        # Primary key
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False,
            comment="UUID primary key",
        ),
        # Unique path-like identifier (e.g., "threads/123/files/456/document.pdf")
        sa.Column(
            "object_key",
            sa.String(length=500),
            nullable=False,
            unique=True,
            comment="Unique path-like key for file retrieval",
        ),
        # File content stored as binary
        sa.Column(
            "data",
            sa.LargeBinary(),
            nullable=False,
            comment="File content (BYTEA)",
        ),
        # MIME type for proper content-type headers
        sa.Column(
            "mime_type",
            sa.String(length=100),
            nullable=False,
            server_default="application/octet-stream",
            comment="MIME type (e.g., image/png, audio/wav)",
        ),
        # File size for quick lookup without loading data
        sa.Column(
            "size_bytes",
            sa.BigInteger(),
            nullable=False,
            comment="File size in bytes",
        ),
        # SHA-256 checksum for integrity verification
        sa.Column(
            "checksum",
            sa.String(length=64),
            nullable=True,
            comment="SHA-256 hash of file content",
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="Upload timestamp",
        ),
        # Optional expiry for temporary files
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Optional TTL for temporary files",
        ),
        # Additional metadata (JSON)
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=True,
            comment="Additional metadata (content_disposition, etc.)",
        ),
        # Primary key constraint
        sa.PrimaryKeyConstraint("id"),
    )

    # Index on object_key for fast lookups
    op.create_index(
        "ix_chainlit_files_object_key",
        "chainlit_files",
        ["object_key"],
        unique=True,
    )

    # Index on expires_at for cleanup queries
    op.create_index(
        "ix_chainlit_files_expires_at",
        "chainlit_files",
        ["expires_at"],
        postgresql_where=sa.text("expires_at IS NOT NULL"),
    )

    # Index on created_at for time-based queries
    op.create_index(
        "ix_chainlit_files_created_at",
        "chainlit_files",
        ["created_at"],
    )


def downgrade() -> None:
    """Drop chainlit_files table."""
    op.drop_index("ix_chainlit_files_created_at", table_name="chainlit_files")
    op.drop_index("ix_chainlit_files_expires_at", table_name="chainlit_files")
    op.drop_index("ix_chainlit_files_object_key", table_name="chainlit_files")
    op.drop_table("chainlit_files")
