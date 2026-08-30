from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator



class SetupRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Username cannot be empty")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class StatusResponse(BaseModel):
    initialized: bool
    message: str


class SetupResponse(BaseModel):
    success: bool
    message: str


# ── Admin auth schemas ──────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class AdminInfo(BaseModel):
    username: str


class MessageResponse(BaseModel):
    message: str


# ── Organizer schemas ───────────────────────────────────────────────────────
class CreateOrganizerRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Username cannot be empty")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class OrganizerOut(BaseModel):
    id: int
    username: str
    is_active: bool

    model_config = {"from_attributes": True}


class OrganizerInfo(BaseModel):
    username: str


# ── Treatment Arm schemas ───────────────────────────────────────────────────
class TreatmentArmCreate(BaseModel):
    name: str
    short_code: str
    allocation_ratio: int = 1
    description: Optional[str] = None

    @field_validator("name", "short_code")
    @classmethod
    def not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty")
        return v

    @field_validator("allocation_ratio")
    @classmethod
    def positive_ratio(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Allocation ratio must be at least 1")
        return v


class TreatmentArmOut(BaseModel):
    id: int
    study_id: int
    name: str
    short_code: str
    allocation_ratio: int
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Study schemas ───────────────────────────────────────────────────────────
class StudyCreate(BaseModel):
    title: str
    protocol_code: str
    description: Optional[str] = None
    blinding_type: str = "Double-Blind"
    target_sample_size: Optional[int] = None
    randomization_method: str = "Permuted Block"
    random_seed: Optional[str] = None
    block_size_rules: Optional[str] = None
    emergency_unblinding_allowed: bool = True
    treatment_arms: list[TreatmentArmCreate] = []

    @field_validator("title", "protocol_code")
    @classmethod
    def not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty")
        return v


class StudyUpdate(BaseModel):
    title: Optional[str] = None
    protocol_code: Optional[str] = None
    description: Optional[str] = None
    blinding_type: Optional[str] = None
    target_sample_size: Optional[int] = None
    randomization_method: Optional[str] = None
    random_seed: Optional[str] = None
    block_size_rules: Optional[str] = None
    emergency_unblinding_allowed: Optional[bool] = None
    status: Optional[str] = None


class StudyOut(BaseModel):
    id: int
    organizer_id: int
    title: str
    protocol_code: str
    description: Optional[str] = None
    blinding_type: str
    target_sample_size: Optional[int] = None
    randomization_method: str
    random_seed: Optional[str] = None
    block_size_rules: Optional[str] = None
    emergency_unblinding_allowed: bool
    status: str
    created_at: datetime
    updated_at: datetime
    treatment_arms: list[TreatmentArmOut] = []

    model_config = {"from_attributes": True}



