"""Manual migration description

Revision ID: f9ad743112d0
Revises: 29e54a53aaea
Create Date: 2025-03-19 15:49:53.476178

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9ad743112d0'
down_revision: Union[str, None] = '29e54a53aaea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
