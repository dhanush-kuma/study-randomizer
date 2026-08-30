"""create_admin_table

Revision ID: 937fc07f8529
Revises: 
Create Date: 2026-08-30 13:07:08.962523

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '937fc07f8529'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the admin table."""
    op.create_table(
        'admin',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.UniqueConstraint('username', name='uq_admin_username'),
    )


def downgrade() -> None:
    """Drop the admin table."""
    op.drop_table('admin')
