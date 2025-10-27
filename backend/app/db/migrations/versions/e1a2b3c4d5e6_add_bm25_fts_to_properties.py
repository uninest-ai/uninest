"""Add BM25 full-text search to properties table

Revision ID: e1a2b3c4d5e6
Revises: b801fad29677
Create Date: 2025-10-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic. ##??
revision: str = 'e1a2b3c4d5e6'
down_revision: Union[str, None] = 'c901ad58e34a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add tsvector column and GIN index for BM25 full-text search."""
    # Add tsvector column
    op.execute("""
        ALTER TABLE properties
        ADD COLUMN search_vector tsvector;
    """)

    # Populate tsvector column with title + description + extended_description
    op.execute("""
        UPDATE properties
        SET search_vector =
            setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(extended_description, '')), 'B');
    """)

    # Create GIN index for fast full-text search
    op.execute("""
        CREATE INDEX idx_properties_search_vector
        ON properties USING gin(search_vector);
    """)

    # Create trigger to auto-update tsvector on INSERT/UPDATE
    # Includes extended_description for AI-generated keywords
    op.execute("""
        CREATE OR REPLACE FUNCTION properties_search_vector_trigger()
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(NEW.extended_description, '')), 'B');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER properties_search_vector_update
        BEFORE INSERT OR UPDATE ON properties
        FOR EACH ROW
        EXECUTE FUNCTION properties_search_vector_trigger();
    """)


def downgrade() -> None:
    """Remove tsvector column and GIN index."""
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS properties_search_vector_update ON properties;")
    op.execute("DROP FUNCTION IF EXISTS properties_search_vector_trigger();")

    # Drop index
    op.execute("DROP INDEX IF EXISTS idx_properties_search_vector;")

    # Drop column
    op.execute("ALTER TABLE properties DROP COLUMN IF EXISTS search_vector;")
