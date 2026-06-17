from pydantic import BaseModel, field_validator


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_not_empty(cls, v: str) -> str:
        if not v or "@" not in v:
            raise ValueError("Invalid email address")
        return v.lower().strip()


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

    @field_validator("email")
    @classmethod
    def email_not_empty(cls, v: str) -> str:
        if not v or "@" not in v:
            raise ValueError("Invalid email address")
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class PasswordResetRequest(BaseModel):
    current_password: str
    new_password: str


class SessionRevocationRequest(BaseModel):
    reason: str


class EmployeeDeactivationRequest(BaseModel):
    reason: str


class ActorSummary(BaseModel):
    id: str
    email: str
    name: str | None = None
    role: str
    permissions: list[str]
    tenant_id: str | None = None
    is_active: bool


class SessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    actor: ActorSummary


class AuthSessionResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    actor: ActorSummary


class CurrentActorResponse(BaseModel):
    actor: ActorSummary


class TenantContextResponse(BaseModel):
    actor_id: str
    role: str
    permissions: list[str]
    tenant_id: str | None
    membership_id: str | None
    is_platform_actor: bool


class CsrfTokenResponse(BaseModel):
    csrf_token: str
