"""Add ALEM Personas table for JIT persona provisioning and persistence.

This migration creates the alem_personas table to store rich agricultural
identities that are auto-generated on first login (Google OAuth) and will
later be populated from mygov ID integration.

Architecture:
    Google OAuth → Chainlit users table (identity)
         ↓
    ALEM Personas table (agricultural context)
         ↓
    User Profiles table (optional link for real farm data)

Revision ID: add_alem_personas_001
Revises: add_defaultopen_steps
Create Date: 2026-01-19 14:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_alem_personas_001'
down_revision = 'add_defaultopen_steps'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create alem_personas table for persona persistence."""
    
    op.create_table(
        'alem_personas',
        # Primary key
        sa.Column('alem_persona_id', sa.String(36), nullable=False, comment='UUID primary key'),
        
        # Foreign keys
        sa.Column('chainlit_user_id', sa.String(36), nullable=False, comment='FK to users.id (Chainlit OAuth user)'),
        sa.Column('email', sa.String(255), nullable=False, comment='User email (from OAuth, unique)'),
        sa.Column('user_profile_id', sa.String(20), nullable=True, comment='Optional FK to user_profiles.user_id'),
        
        # Persona data (synthetic or from mygov ID)
        sa.Column('full_name', sa.String(100), nullable=False, comment='Full name from OAuth or mygov'),
        sa.Column('fin_code', sa.String(20), nullable=True, comment='FIN code (mock or real from mygov)'),
        sa.Column('phone', sa.String(20), nullable=True, comment='Phone number (mock or real)'),
        sa.Column('region', sa.String(50), nullable=False, comment='Agricultural region (e.g., Sabirabad)'),
        sa.Column('crop_type', sa.String(50), nullable=False, comment='Primary crop (e.g., Pambıq/Cotton)'),
        sa.Column('total_area_ha', sa.Float(), nullable=False, comment='Farm size in hectares'),
        sa.Column('experience_level', sa.String(20), nullable=True, comment='novice/intermediate/expert'),
        sa.Column('ektis_verified', sa.Boolean(), nullable=False, default=False, comment='True if data from EKTIS/mygov'),
        
        # Metadata
        sa.Column('data_source', sa.String(20), nullable=False, default='synthetic', comment='synthetic/mygov/ektis'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True, comment='Last login timestamp'),
        
        # Constraints
        sa.PrimaryKeyConstraint('alem_persona_id'),
        sa.ForeignKeyConstraint(['chainlit_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_profile_id'], ['user_profiles.user_id'], ondelete='SET NULL'),
        sa.UniqueConstraint('email', name='uq_alem_personas_email'),
        sa.UniqueConstraint('chainlit_user_id', name='uq_alem_personas_user_id'),
    )
    
    # Indexes for fast lookups
    op.create_index('idx_alem_personas_email', 'alem_personas', ['email'])
    op.create_index('idx_alem_personas_fin_code', 'alem_personas', ['fin_code'])
    op.create_index('idx_alem_personas_region', 'alem_personas', ['region'])


def downgrade() -> None:
    """Drop alem_personas table."""
    op.drop_index('idx_alem_personas_region', table_name='alem_personas')
    op.drop_index('idx_alem_personas_fin_code', table_name='alem_personas')
    op.drop_index('idx_alem_personas_email', table_name='alem_personas')
    op.drop_table('alem_personas')
