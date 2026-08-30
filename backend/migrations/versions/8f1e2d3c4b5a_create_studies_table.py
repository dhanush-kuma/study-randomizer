"""create_studies_table

Revision ID: 8f1e2d3c4b5a
Revises: 53a123b51bd3
Create Date: 2026-08-30 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f1e2d3c4b5a'
down_revision: Union[str, Sequence[str], None] = '53a123b51bd3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the studies table."""
    op.create_table(
        'studies',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            'organizer_id',
            sa.Integer(),
            sa.ForeignKey('organizer.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('protocol_code', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'blinding_type',
            sa.String(length=50),
            nullable=False,
            server_default='Double-Blind',
        ),
        sa.Column('target_sample_size', sa.Integer(), nullable=True),
        sa.Column(
            'randomization_method',
            sa.String(length=50),
            nullable=False,
            server_default='Permuted Block',
        ),
        sa.Column('random_seed', sa.String(length=100), nullable=True),
        sa.Column('block_size_rules', sa.String(length=255), nullable=True),
        sa.Column(
            'emergency_unblinding_allowed',
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            'status',
            sa.String(length=50),
            nullable=False,
            server_default='Draft',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint('protocol_code', name='uq_studies_protocol_code'),
    )


def downgrade() -> None:
    """Drop the studies table."""
    op.drop_table('studies')
