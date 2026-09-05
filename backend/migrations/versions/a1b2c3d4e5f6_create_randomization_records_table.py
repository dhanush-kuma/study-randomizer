"""create_randomization_records_table

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-09-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "randomization_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "study_id",
            sa.Integer(),
            sa.ForeignKey("studies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("kit_code", sa.String(length=100), nullable=False),
        sa.Column("treatment_name", sa.String(length=255), nullable=False),
        sa.Column("assigned_patient_id", sa.String(length=255), nullable=True),
        sa.Column(
            "assigned_by_doctor_id",
            sa.Integer(),
            sa.ForeignKey("doctor.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        # A kit code must be globally unique across all studies
        sa.UniqueConstraint("kit_code", name="uq_randomization_records_kit_code"),
        # Sequence number must be unique within a study
        sa.UniqueConstraint(
            "study_id",
            "sequence_number",
            name="uq_randomization_records_study_sequence",
        ),
    )


def downgrade() -> None:
    op.drop_table("randomization_records")
