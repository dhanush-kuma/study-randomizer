"""replace_block_size_rules_with_min_max

Revision ID: f1a2b3c4d5e6
Revises: e5f6a7b8c9d0
Create Date: 2026-09-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the old free-text column
    op.drop_column("studies", "block_size_rules")

    # Add structured integer columns
    op.add_column("studies", sa.Column("block_size_min", sa.Integer(), nullable=True))
    op.add_column("studies", sa.Column("block_size_max", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("studies", "block_size_max")
    op.drop_column("studies", "block_size_min")

    op.add_column(
        "studies",
        sa.Column("block_size_rules", sa.String(length=255), nullable=True),
    )
