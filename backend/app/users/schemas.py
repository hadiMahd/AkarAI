from pydantic import BaseModel, field_validator


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


class UserProfileResponse(BaseModel):
    id: str
    email: str
    name: str | None = None
    phone: str | None = None
    is_complete_for_leads: bool
    missing_fields: list[str]


class UserProfileUpdateRequest(BaseModel):
    name: str | None = None
    phone: str | None = None

    @field_validator("name", "phone")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)
