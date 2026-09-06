"""drop_kit_code_global_unique_constraint

kit_code was globally unique, but now same treatment arm kit codes
repeat across sequence rows, so only sequence_number uniqueness
per study is needed.

Revision ID: c8d9e0f1a2b3
Revises: b2c3d4e5f6a7
Create Date: 2026-09-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "c8d9e0f1a2b3"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_randomization_records_kit_code",
        "randomization_records",
        type_="unique",
    )


def downgrade() -> None:
    op.create_unique_constraint(
        "uq_randomization_records_kit_code",
        "randomization_records",
        ["kit_code"],
    )
