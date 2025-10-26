"""Add property_embeddings table for vector search

Revision ID: f5a8b9c3d2e1
Revises: e1a2b3c4d5e6
Create Date: 2025-10-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f5a8b9c3d2e1'
down_revision: Union[str, None] = 'e1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add property_embeddings table for storing precomputed vector embeddings."""

    # Create property_embeddings table
    op.execute("""
        CREATE TABLE IF NOT EXISTS property_embeddings (
            id BIGINT PRIMARY KEY REFERENCES properties(id) ON DELETE CASCADE,
            embedding JSONB NOT NULL,
            model_name VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Create index on model_name for quick filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_property_embeddings_model
        ON property_embeddings(model_name);
    """)

    # Create trigger to update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_property_embeddings_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER property_embeddings_update_timestamp
        BEFORE UPDATE ON property_embeddings
        FOR EACH ROW
        EXECUTE FUNCTION update_property_embeddings_timestamp();
    """)


def downgrade() -> None:
    """Remove property_embeddings table and related objects."""

    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS property_embeddings_update_timestamp ON property_embeddings;")
    op.execute("DROP FUNCTION IF EXISTS update_property_embeddings_timestamp();")

    # Drop index
    op.execute("DROP INDEX IF EXISTS idx_property_embeddings_model;")

    # Drop table
    op.execute("DROP TABLE IF EXISTS property_embeddings;")