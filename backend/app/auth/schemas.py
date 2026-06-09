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


class RefreshRequest(BaseModel):
    refresh_token: str


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
    role: str
    permissions: list[str]
    tenant_id: str | None = None
    is_active: bool


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
