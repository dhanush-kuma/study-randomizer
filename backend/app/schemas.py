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
