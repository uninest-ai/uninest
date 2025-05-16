"""initial

Revision ID: aafea908fc67
Revises: 66cba5212184
Create Date: 2025-04-10 13:44:13.909456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aafea908fc67'
down_revision: Union[str, None] = '66cba5212184'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
