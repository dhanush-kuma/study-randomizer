"""create_treatment_arms_table

Revision ID: c7d8e9f0a1b2
Revises: 8f1e2d3c4b5a
Create Date: 2026-08-30 17:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, Sequence[str], None] = '8f1e2d3c4b5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the treatment_arms table."""
    op.create_table(
        'treatment_arms',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            'study_id',
            sa.Integer(),
            sa.ForeignKey('studies.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('short_code', sa.String(length=50), nullable=False),
        sa.Column('allocation_ratio', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    """Drop the treatment_arms table."""
    op.drop_table('treatment_arms')
