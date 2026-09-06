from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Admin(Base):
    __tablename__ = "admin"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)


class Organizer(Base):
    __tablename__ = "organizer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    studies: Mapped[list["Study"]] = relationship("Study", back_populates="organizer")


class Study(Base):
    __tablename__ = "studies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organizer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizer.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    protocol_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    blinding_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Double-Blind"
    )
    target_sample_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    randomization_method: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Permuted Block"
    )
    random_seed: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    block_size_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    block_size_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    emergency_unblinding_allowed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    organizer: Mapped["Organizer"] = relationship("Organizer", back_populates="studies")
    treatment_arms: Mapped[list["TreatmentArm"]] = relationship(
        "TreatmentArm", back_populates="study", cascade="all, delete-orphan"
    )
    investigators: Mapped[list["Investigator"]] = relationship(
        "Investigator", back_populates="study", cascade="all, delete-orphan"
    )
    randomization_records: Mapped[list["RandomizationRecord"]] = relationship(
        "RandomizationRecord", back_populates="study", cascade="all, delete-orphan"
    )


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(String(36), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TreatmentArm(Base):
    __tablename__ = "treatment_arms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    study_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("studies.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_code: Mapped[str] = mapped_column(String(50), nullable=False)
    allocation_ratio: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    study: Mapped["Study"] = relationship("Study", back_populates="treatment_arms")


class Investigator(Base):
    __tablename__ = "investigator"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    study_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("studies.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Zero-padded sequential number unique within a study, e.g. "000001"
    username: Mapped[str] = mapped_column(String(10), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # inactive (just created) → active (first login) → revoked
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="inactive")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    study: Mapped["Study"] = relationship("Study", back_populates="investigators")


class RandomizationRecord(Base):
    __tablename__ = "randomization_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    study_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("studies.id", ondelete="CASCADE"), nullable=False
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    kit_code: Mapped[str] = mapped_column(String(100), nullable=False)
    treatment_name: Mapped[str] = mapped_column(String(255), nullable=False)
    assigned_patient_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    assigned_by_investigator_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("investigator.id", ondelete="SET NULL"), nullable=True
    )
    assigned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    blind: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    study: Mapped["Study"] = relationship("Study", back_populates="randomization_records")
    assigned_by_investigator: Mapped[Optional["Investigator"]] = relationship("Investigator")
