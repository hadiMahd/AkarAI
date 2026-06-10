import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshSession, AccessRevocation
from app.auth.repository import AuthRepository
from app.common.config import settings
from app.common.rls import apply_rls_context_to_session
from app.common.redis import redis_delete, redis_get, redis_set
from app.common.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)


async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    key = f"blacklist:jti:{jti}"
    await redis_set(key, "1", ttl=ttl_seconds)


async def is_token_blacklisted(jti: str) -> bool:
    key = f"blacklist:jti:{jti}"
    return await redis_get(key) is not None


def _session_invalidation_key(user_id: str) -> str:
    return f"session_invalidated:{user_id}"


async def invalidate_user_sessions(user_id: str) -> None:
    key = _session_invalidation_key(user_id)
    ts = datetime.now(timezone.utc).timestamp()
    await redis_set(key, str(ts), ttl=86400 * 7)


async def get_session_invalidation_timestamp(user_id: str) -> float | None:
    key = _session_invalidation_key(user_id)
    val = await redis_get(key)
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


async def revoke_user_all_sessions(
    repo: AuthRepository,
    user_id: str,
    reason: str,
) -> int:
    await _apply_refresh_session_rls(repo.session, user_id)
    sessions = await repo.get_active_sessions_for_user(user_id)
    now = datetime.now(timezone.utc)
    count = 0
    for session in sessions:
        session.revoked_at = now
        session.revocation_reason = reason
        await repo.update_refresh_session(session)
        await blacklist_token(str(session.id), settings.jwt_refresh_ttl_days * 86400)
        count += 1
    await invalidate_user_sessions(user_id)
    return count


class AuthService:
    def __init__(self, repository: AuthRepository):
        self._repo = repository

    async def login(
        self,
        email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict | None:
        user = await self._repo.get_user_by_email(email)
        if user is None:
            return None
        if not user.is_active or user.status not in ("active",):
            return None
        if not verify_password(password, user.password_hash):
            return None

        from app.users.service import UsersService
        from app.users.repository import UsersRepository

        users_svc = UsersService(UsersRepository(self._repo.session, self._repo._tenant))
        await users_svc.update_last_login(user)

        role_slug = await self._lookup_role_slug(user.role_id)
        access_token, refresh_token, session = await self._issue_session(
            str(user.id), role=role_slug, ip_address=ip_address, user_agent=user_agent
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_access_ttl_minutes * 60,
            "user": user,
            "session": session,
        }

    async def register(
        self,
        email: str,
        password: str,
        name: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict | None:
        existing_user = await self._repo.get_user_by_email(email)
        if existing_user is not None:
            return None

        from app.users.models import User
        from app.auth.models import Role
        from sqlalchemy import select

        role_result = await self._repo.session.execute(
            select(Role).where(Role.slug == "user")
        )
        user_role = role_result.scalar_one_or_none()

        password_hash = hash_password(password)
        new_user = User(
            email=email,
            name=name,
            password_hash=password_hash,
            role_id=user_role.id if user_role else None,
            is_active=True,
            status="active",
        )
        self._repo.session.add(new_user)
        await self._repo.session.flush()

        role_slug = await self._lookup_role_slug(new_user.role_id)
        access_token, refresh_token, session = await self._issue_session(
            str(new_user.id), role=role_slug, ip_address=ip_address, user_agent=user_agent
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_access_ttl_minutes * 60,
            "user": new_user,
            "session": session,
        }

    async def refresh(
        self,
        refresh_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict | None:
        try:
            payload = decode_refresh_token(refresh_token)
        except Exception:
            return None

        jti = payload.get("jti")
        user_id = payload.get("sub")
        if not user_id or not jti:
            return None

        await _apply_refresh_session_rls(self._repo.session, user_id)

        if await is_token_blacklisted(jti):
            return None

        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        session = await self._repo.get_refresh_session_by_token_hash(token_hash)

        if session is None:
            return None
        if session.revoked_at is not None:
            await self._revoke_family(session.user_id, session.family_id, "refresh_rotation")
            return None
        if session.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return None

        now = datetime.now(timezone.utc)
        session.revoked_at = now
        session.revocation_reason = "refresh_rotation"
        await self._repo.update_refresh_session(session)
        await blacklist_token(jti, settings.jwt_refresh_ttl_days * 86400)

        user = await self._repo.get_user_by_id(str(session.user_id))
        if user is None or not user.is_active or user.status not in ("active",):
            return None

        role_slug = await self._lookup_role_slug(user.role_id)
        new_access, new_refresh, new_session = await self._issue_session(
            str(user.id), role=role_slug, family_id=session.family_id, ip_address=ip_address, user_agent=user_agent
        )
        session.replaced_by_session_id = new_session.id
        await self._repo.update_refresh_session(session)

        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
            "expires_in": settings.jwt_access_ttl_minutes * 60,
            "user": user,
            "session": new_session,
        }

    async def logout(self, user_id: str, refresh_token: str | None = None) -> None:
        await _apply_refresh_session_rls(self._repo.session, user_id)
        if refresh_token:
            try:
                payload = decode_refresh_token(refresh_token)
                jti = payload.get("jti", "")
                await blacklist_token(jti, settings.jwt_refresh_ttl_days * 86400)

                token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
                session = await self._repo.get_refresh_session_by_token_hash(token_hash)
                if session and session.revoked_at is None:
                    now = datetime.now(timezone.utc)
                    session.revoked_at = now
                    session.revocation_reason = "logout"
                    await self._repo.update_refresh_session(session)
            except Exception:
                pass

        await invalidate_user_sessions(user_id)

    async def reset_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> bool:
        user = await self._repo.get_user_by_id(user_id)
        if user is None:
            return False
        if not verify_password(current_password, user.password_hash):
            return False

        new_hash = hash_password(new_password)
        from app.users.service import UsersService
        from app.users.repository import UsersRepository

        users_svc = UsersService(UsersRepository(self._repo.session, self._repo._tenant))
        await users_svc.update_password(user, new_hash)

        await revoke_user_all_sessions(self._repo, user_id, "password_reset")
        return True

    async def revoke_session(
        self,
        session_id: str,
        reason: str,
        revoker_user_id: str,
    ) -> bool:
        await _apply_refresh_session_rls(self._repo.session, revoker_user_id)
        target = await self._repo.get_refresh_session_by_id(session_id)
        if target is None:
            return False

        now = datetime.now(timezone.utc)
        target.revoked_at = now
        target.revocation_reason = reason
        await self._repo.update_refresh_session(target)
        await blacklist_token(str(target.id), settings.jwt_refresh_ttl_days * 86400)
        return True

    async def _lookup_role_slug(self, role_id) -> str | None:
        if role_id is None:
            return None
        from app.auth.models import Role as RoleModel
        from sqlalchemy import select
        result = await self._repo.session.execute(
            select(RoleModel.slug).where(RoleModel.id == role_id)
        )
        row = result.scalar_one_or_none()
        return row if row else None

    async def _issue_session(
        self,
        user_id: str,
        role: str | None = None,
        family_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[str, str, RefreshSession]:
        now = datetime.now(timezone.utc)
        fam_id = family_id or str(uuid.uuid4())

        access_claims = {}
        if role:
            access_claims["role"] = role
        access_token = create_access_token(user_id, extra_claims=access_claims)
        refresh_token = create_refresh_token(user_id)

        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        session = RefreshSession(
            user_id=user_id,
            token_hash=token_hash,
            family_id=fam_id,
            issued_at=now,
            expires_at=now + timedelta(days=settings.jwt_refresh_ttl_days),
            last_used_at=now,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self._repo.create_refresh_session(session)
        return access_token, refresh_token, session

    async def _revoke_family(self, user_id: uuid.UUID, family_id: str, reason: str) -> None:
        await _apply_refresh_session_rls(self._repo.session, str(user_id))
        sessions = await self._repo.get_active_sessions_for_user(str(user_id))
        now = datetime.now(timezone.utc)
        for session in sessions:
            if session.family_id == family_id and session.revoked_at is None:
                session.revoked_at = now
                session.revocation_reason = reason
                await self._repo.update_refresh_session(session)
        await invalidate_user_sessions(str(user_id))


async def _apply_refresh_session_rls(session: AsyncSession, user_id: str) -> None:
    await apply_rls_context_to_session(session, user_id=UUID(user_id))
