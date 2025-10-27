"""merge_migration_heads

Revision ID: 59b94fe0c885
Revises: 05e4745ca94b, aafea908fc67, d06a44e4d43c, f5a8b9c3d2e1
Create Date: 2025-10-26 22:57:09.043990

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '59b94fe0c885'
down_revision: Union[str, None] = ('05e4745ca94b', 'aafea908fc67', 'd06a44e4d43c', 'f5a8b9c3d2e1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
