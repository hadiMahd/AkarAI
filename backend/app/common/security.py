import uuid
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from jose import jwt

from app.common.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, extra_claims: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_ttl_minutes),
        "jti": str(uuid.uuid4()),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_access_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str, extra_claims: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(days=settings.jwt_refresh_ttl_days),
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_refresh_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_access_secret, algorithms=[settings.jwt_algorithm])


def decode_refresh_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_refresh_secret, algorithms=[settings.jwt_algorithm])
