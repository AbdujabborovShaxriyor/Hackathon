from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.common.database import get_async_session
from libs.common.models import User
from libs.common.security import decode_access_token, get_bearer_token, role_allowed


async def get_db(session: AsyncSession = Depends(get_async_session)) -> AsyncSession:
    return session


async def get_current_user(
    token: str = Depends(get_bearer_token),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    try:
        payload = decode_access_token(token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    result = await session.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_roles(*roles: str):
    allowed = set(roles)

    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not role_allowed(current_user.role, allowed):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return current_user

    return dependency

