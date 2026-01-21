"""Add FIN and OIDC identity fields to user_profiles

Revision ID: add_fin_oidc_identity
Revises: add_chainlit_data_layer_tables
Create Date: 2026-01-19 19:30:00

This migration adds critical identity fields for EKTİS integration:
- FIN (Financial Identification Number) - 7-character unique ID from mygov
- OIDC provider_sub - Unique identifier from OAuth token
- Birth date, verified phone, and name components for mygov ID claims

These fields enable:
1. Linking ALEM personas to real government IDs
2. Fetching land ownership data from EKTİS API via FIN
3. OAuth authentication via ASAN Login / mygov ID
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_fin_oidc_identity"
down_revision: str | None = "make_chainlit_user_nullable"  # After all Chainlit tables setup
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add FIN and OIDC identity fields to user_profiles."""

    # Add FIN (Financial Identification Number) - primary government ID
    op.add_column(
        "user_profiles",
        sa.Column(
            "fin_code",
            sa.String(length=7),
            nullable=True,  # Nullable for backward compatibility with synthetic data
            comment="FIN (Financial Identification Number) from mygov ID - 7 characters",
        ),
    )

    # Add OIDC provider subject (unique OAuth identifier)
    op.add_column(
        "user_profiles",
        sa.Column(
            "provider_sub",
            sa.String(length=255),
            nullable=True,
            comment="OIDC sub claim from OAuth provider (ASAN Login / mygov ID)",
        ),
    )

    # Add OAuth provider name
    op.add_column(
        "user_profiles",
        sa.Column(
            "provider_name",
            sa.String(length=50),
            nullable=True,
            comment='OAuth provider name (e.g., "mygov", "asan_login", "google")',
        ),
    )

    # Add authentication level (from mygov)
    op.add_column(
        "user_profiles",
        sa.Column(
            "auth_level",
            sa.String(length=20),
            nullable=True,
            comment='Authentication level: "SIMA" (simple), "ASAN_IMZA" (signature)',
        ),
    )

    # Add birth date (from mygov ID token)
    op.add_column(
        "user_profiles",
        sa.Column(
            "birth_date",
            sa.Date(),
            nullable=True,
            comment="Date of birth from mygov ID claim",
        ),
    )

    # Add verified phone (plaintext for OTP, not hashed)
    op.add_column(
        "user_profiles",
        sa.Column(
            "phone_verified",
            sa.String(length=20),
            nullable=True,
            comment="Verified phone number from mygov ID (plaintext for OTP)",
        ),
    )

    # Add name components (as per mygov ID structure)
    op.add_column(
        "user_profiles",
        sa.Column(
            "first_name",
            sa.String(length=100),
            nullable=True,
            comment="First name from mygov ID token",
        ),
    )

    op.add_column(
        "user_profiles",
        sa.Column(
            "last_name",
            sa.String(length=100),
            nullable=True,
            comment="Last name from mygov ID token",
        ),
    )

    op.add_column(
        "user_profiles",
        sa.Column(
            "father_name",
            sa.String(length=100),
            nullable=True,
            comment="Patronymic (father name) from mygov ID token",
        ),
    )

    # Add subsidy tracking fields
    op.add_column(
        "user_profiles",
        sa.Column(
            "subsidy_balance_azn",
            sa.Float(),
            nullable=True,
            comment="Current subsidy balance in AZN (from EKTİS API)",
        ),
    )

    op.add_column(
        "user_profiles",
        sa.Column(
            "last_payment_date",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Last subsidy payment received date",
        ),
    )

    # Add EKTİS farmer ID (different from user_id, this is ministry ID)
    op.add_column(
        "user_profiles",
        sa.Column(
            "ektis_farmer_id",
            sa.String(length=30),
            nullable=True,
            comment="Farmer ID in EKTİS system (linked to FIN)",
        ),
    )

    # Create unique indexes on FIN and provider_sub (for fast lookups)
    op.create_index("idx_user_profiles_fin", "user_profiles", ["fin_code"], unique=True)
    op.create_index(
        "idx_user_profiles_provider_sub", "user_profiles", ["provider_sub"], unique=True
    )
    op.create_index(
        "idx_user_profiles_ektis_farmer_id", "user_profiles", ["ektis_farmer_id"], unique=False
    )


def downgrade() -> None:
    """Remove FIN and OIDC identity fields."""

    # Drop indexes
    op.drop_index("idx_user_profiles_ektis_farmer_id", table_name="user_profiles")
    op.drop_index("idx_user_profiles_provider_sub", table_name="user_profiles")
    op.drop_index("idx_user_profiles_fin", table_name="user_profiles")

    # Drop columns
    op.drop_column("user_profiles", "ektis_farmer_id")
    op.drop_column("user_profiles", "last_payment_date")
    op.drop_column("user_profiles", "subsidy_balance_azn")
    op.drop_column("user_profiles", "father_name")
    op.drop_column("user_profiles", "last_name")
    op.drop_column("user_profiles", "first_name")
    op.drop_column("user_profiles", "phone_verified")
    op.drop_column("user_profiles", "birth_date")
    op.drop_column("user_profiles", "auth_level")
    op.drop_column("user_profiles", "provider_name")
    op.drop_column("user_profiles", "provider_sub")
    op.drop_column("user_profiles", "fin_code")
