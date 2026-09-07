"""investigator session_version and unique patient per study

Revision ID: a3b4c5d6e7f8
Revises: f9a0b1c2d3e4
Create Date: 2026-09-07 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, Sequence[str], None] = "f9a0b1c2d3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "investigator",
        sa.Column("session_version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        "uq_randomization_records_study_patient",
        "randomization_records",
        ["study_id", sa.text("lower(assigned_patient_id)")],
        unique=True,
        postgresql_where=sa.text("assigned_patient_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_randomization_records_study_patient",
        table_name="randomization_records",
    )
    op.drop_column("investigator", "session_version")
