"""update_search_vector_trigger_include_extended_description

Revision ID: 38e7ee9e6267
Revises: 59b94fe0c885
Create Date: 2025-10-26 22:57:28.816387

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38e7ee9e6267'
down_revision: Union[str, None] = '59b94fe0c885'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update properties_search_vector trigger to include extended fields."""
    # Drop existing trigger and function if they exist
    op.execute("DROP TRIGGER IF EXISTS properties_search_vector_update ON properties;")
    op.execute("DROP FUNCTION IF EXISTS properties_search_vector_trigger();")

    # Recreate function with extended fields
    op.execute("""
        CREATE OR REPLACE FUNCTION properties_search_vector_trigger()
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(NEW.extended_description, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(NEW.address, '')), 'C') ||
                setweight(to_tsvector('english', coalesce(NEW.city, '')), 'C');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)

    # Recreate trigger
    op.execute("""
        CREATE TRIGGER properties_search_vector_update
        BEFORE INSERT OR UPDATE ON properties
        FOR EACH ROW
        EXECUTE FUNCTION properties_search_vector_trigger();
    """)

    # Backfill existing rows so new fields are reflected in search_vector
    op.execute("""
        UPDATE properties
        SET search_vector =
            setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(extended_description, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(address, '')), 'C') ||
            setweight(to_tsvector('english', coalesce(city, '')), 'C');
    """)


def downgrade() -> None:
    """Revert search_vector trigger to original title+description behavior."""
    op.execute("DROP TRIGGER IF EXISTS properties_search_vector_update ON properties;")
    op.execute("DROP FUNCTION IF EXISTS properties_search_vector_trigger();")

    op.execute("""
        CREATE OR REPLACE FUNCTION properties_search_vector_trigger()
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B');
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

    # Rebuild vectors using the reduced field set
    op.execute("""
        UPDATE properties
        SET search_vector =
            setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(description, '')), 'B');
    """)
