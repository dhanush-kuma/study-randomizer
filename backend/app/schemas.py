from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128


def validate_new_password(v: str) -> str:
    if len(v) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
    if len(v) > PASSWORD_MAX_LENGTH:
        raise ValueError(f"Password must be at most {PASSWORD_MAX_LENGTH} characters")
    return v


def validate_login_password(v: str) -> str:
    if len(v) > PASSWORD_MAX_LENGTH:
        raise ValueError("Password is too long")
    return v


class SetupRequest(BaseModel):
    setup_token: str = ""
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
    def password_strength(cls, v: str) -> str:
        return validate_new_password(v)


class StatusResponse(BaseModel):
    initialized: bool
    message: str


class HealthResponse(BaseModel):
    status: str
    message: str


class SetupResponse(BaseModel):
    success: bool
    message: str


class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("password")
    @classmethod
    def password_bounds(cls, v: str) -> str:
        return validate_login_password(v)


class DoctorLoginRequest(LoginRequest):
    trial_id: str

    @field_validator("trial_id")
    @classmethod
    def trial_id_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Trial ID cannot be empty")
        return v



class AdminInfo(BaseModel):
    username: str


class MessageResponse(BaseModel):
    message: str


class LoginResponse(BaseModel):
    message: str
    csrf_token: str


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
    def password_strength(cls, v: str) -> str:
        return validate_new_password(v)


class OrganizerOut(BaseModel):
    id: int
    username: str
    is_active: bool

    model_config = {"from_attributes": True}


class OrganizerInfo(BaseModel):
    username: str


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


class StudyCreate(BaseModel):
    title: str
    protocol_code: str
    description: Optional[str] = None
    blinding_type: str = "Double-Blind"
    target_sample_size: Optional[int] = None
    randomization_method: str = "Permuted Block"
    block_size_min: Optional[int] = None
    block_size_max: Optional[int] = None
    emergency_unblinding_allowed: bool = True
    treatment_arms: list[TreatmentArmCreate] = []

    @field_validator("title", "protocol_code")
    @classmethod
    def not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty")
        return v

    @field_validator("block_size_min", "block_size_max")
    @classmethod
    def positive_block_size(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1:
            raise ValueError("Block size must be at least 1")
        return v


class StudyUpdate(BaseModel):
    title: Optional[str] = None
    protocol_code: Optional[str] = None
    description: Optional[str] = None
    blinding_type: Optional[str] = None
    target_sample_size: Optional[int] = None
    randomization_method: Optional[str] = None
    block_size_min: Optional[int] = None
    block_size_max: Optional[int] = None
    emergency_unblinding_allowed: Optional[bool] = None
    status: Optional[str] = None

    @field_validator("block_size_min", "block_size_max")
    @classmethod
    def positive_block_size(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1:
            raise ValueError("Block size must be at least 1")
        return v


class StudyOut(BaseModel):
    id: int
    organizer_id: int
    title: str
    protocol_code: str
    description: Optional[str] = None
    blinding_type: str
    target_sample_size: Optional[int] = None
    randomization_method: str
    block_size_min: Optional[int] = None
    block_size_max: Optional[int] = None
    emergency_unblinding_allowed: bool
    status: str
    created_at: datetime
    updated_at: datetime
    treatment_arms: list[TreatmentArmOut] = []

    model_config = {"from_attributes": True}


class InviteDoctorRequest(BaseModel):
    email: str
    full_name: Optional[str] = None

    @field_validator("email")
    @classmethod
    def email_normalized(cls, v: str) -> str:
        v = v.strip().lower()
        if not v or "@" not in v:
            raise ValueError("A valid email address is required")
        return v


class InvitationOut(BaseModel):
    id: int
    study_id: int
    email: str
    full_name: Optional[str] = None
    status: str
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class InvitationPreview(BaseModel):
    email: str
    full_name: Optional[str] = None
    study_title: str
    protocol_code: str
    expires_at: datetime
    account_exists: bool


class DoctorSignupRequest(BaseModel):
    token: str
    username: str
    password: str
    full_name: Optional[str] = None

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Username cannot be empty")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return validate_new_password(v)


class DoctorInfo(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None


class DoctorStudyOut(BaseModel):
    id: int
    title: str
    protocol_code: str
    status: str
    blinding_type: str
    joined_at: datetime

    model_config = {"from_attributes": True}
