"""replace_doctor_with_investigator

Drops the old doctor / study_invitations / study_doctors tables and their
dependency in randomization_records, then creates the new investigator table.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop the FK column that referenced doctor.id in randomization_records,
    #    then re-add it pointing at the new investigator table.
    op.drop_column("randomization_records", "assigned_by_doctor_id")

    # 2. Drop join / invitation tables first (they reference doctor.id)
    op.drop_table("study_doctors")
    op.drop_table("study_invitations")

    # 3. Drop the doctor table itself
    op.drop_table("doctor")

    # 4. Create the new investigator table
    op.create_table(
        "investigator",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "study_id",
            sa.Integer(),
            sa.ForeignKey("studies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        # Zero-padded sequential number, unique within a study (e.g. "000001")
        sa.Column("username", sa.String(length=10), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        # inactive → active (first login) → revoked
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="inactive",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # Username is only unique *within* a study
        sa.UniqueConstraint("study_id", "username", name="uq_investigator_study_username"),
    )

    # 5. Add the new FK column in randomization_records pointing at investigator
    op.add_column(
        "randomization_records",
        sa.Column(
            "assigned_by_investigator_id",
            sa.Integer(),
            sa.ForeignKey("investigator.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    # Reverse order
    op.drop_column("randomization_records", "assigned_by_investigator_id")
    op.drop_table("investigator")

    op.create_table(
        "doctor",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("email", name="uq_doctor_email"),
        sa.UniqueConstraint("username", name="uq_doctor_username"),
    )

    op.create_table(
        "study_invitations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("study_id", sa.Integer(), sa.ForeignKey("studies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("invited_by_organizer_id", sa.Integer(), sa.ForeignKey("organizer.id"), nullable=False),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("doctor.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("token", name="uq_study_invitations_token"),
    )

    op.create_table(
        "study_doctors",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("study_id", sa.Integer(), sa.ForeignKey("studies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("doctor.id", ondelete="CASCADE"), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("study_id", "doctor_id", name="uq_study_doctors_study_doctor"),
    )

    op.add_column(
        "randomization_records",
        sa.Column(
            "assigned_by_doctor_id",
            sa.Integer(),
            sa.ForeignKey("doctor.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
