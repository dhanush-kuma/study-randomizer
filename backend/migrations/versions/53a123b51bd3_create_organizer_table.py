"""create_organizer_table

Revision ID: 53a123b51bd3
Revises: 937fc07f8529
Create Date: 2026-08-30 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '53a123b51bd3'
down_revision: Union[str, Sequence[str], None] = '937fc07f8529'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the organizer table."""
    op.create_table(
        'organizer',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint('username', name='uq_organizer_username'),
    )


def downgrade() -> None:
    """Drop the organizer table."""
    op.drop_table('organizer')
