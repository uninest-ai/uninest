"""Add 3rd party API fields to properties and landlords

Revision ID: c901ad58e34a
Revises: b801fad29677
Create Date: 2025-01-16 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c901ad58e34a'
down_revision: Union[str, None] = 'b801fad29677'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add 3rd party API fields to properties table
    op.add_column('properties', sa.Column('original_listing_url', sa.String(), nullable=True))
    op.add_column('properties', sa.Column('api_source', sa.String(), nullable=True))
    op.add_column('properties', sa.Column('api_property_id', sa.String(), nullable=True))
    op.add_column('properties', sa.Column('api_images', sa.JSON(), nullable=True))
    op.add_column('properties', sa.Column('extended_description', sa.Text(), nullable=True))
    op.add_column('properties', sa.Column('api_amenities', sa.JSON(), nullable=True))
    op.add_column('properties', sa.Column('api_metadata', sa.JSON(), nullable=True))
    
    # Add 3rd party API fields to landlord_profiles table
    op.add_column('landlord_profiles', sa.Column('profile_image_url', sa.String(), nullable=True))
    op.add_column('landlord_profiles', sa.Column('website_url', sa.String(), nullable=True))
    op.add_column('landlord_profiles', sa.Column('email', sa.String(), nullable=True))
    op.add_column('landlord_profiles', sa.Column('office_address', sa.String(), nullable=True))
    op.add_column('landlord_profiles', sa.Column('api_source', sa.String(), nullable=True))
    op.add_column('landlord_profiles', sa.Column('api_metadata', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove 3rd party API fields from landlord_profiles table
    op.drop_column('landlord_profiles', 'api_metadata')
    op.drop_column('landlord_profiles', 'api_source')
    op.drop_column('landlord_profiles', 'office_address')
    op.drop_column('landlord_profiles', 'email')
    op.drop_column('landlord_profiles', 'website_url')
    op.drop_column('landlord_profiles', 'profile_image_url')
    
    # Remove 3rd party API fields from properties table
    op.drop_column('properties', 'api_metadata')
    op.drop_column('properties', 'api_amenities')
    op.drop_column('properties', 'extended_description')
    op.drop_column('properties', 'api_images')
    op.drop_column('properties', 'api_property_id')
    op.drop_column('properties', 'api_source')
    op.drop_column('properties', 'original_listing_url')