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
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
