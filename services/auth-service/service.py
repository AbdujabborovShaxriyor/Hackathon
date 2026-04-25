from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.common.models import User
from libs.common.security import create_access_token, hash_password, verify_password
from libs.schemas.contracts import LoginRequest, TokenResponse, UserCreate, UserRead


async def create_user(session: AsyncSession, payload: UserCreate) -> UserRead:
    if payload.role == "admin":
        raise ValueError("Admin users must be created through the bootstrap flow")
    existing = await session.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise ValueError("User already exists")

    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return UserRead.model_validate(user)


async def authenticate_user(session: AsyncSession, payload: LoginRequest) -> TokenResponse:
    result = await session.execute(select(User).where(User.email == payload.email.lower(), User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise ValueError("Invalid credentials")
    token = create_access_token(subject=user.id, role=user.role, extra_claims={"email": user.email})
    return TokenResponse(access_token=token)


async def bootstrap_admin(session: AsyncSession, *, email: str, full_name: str, password: str, role: str = "admin") -> UserRead:
    existing = await session.execute(select(User).where(User.email == email.lower()))
    user = existing.scalar_one_or_none()
    if user is None:
        user = User(
            email=email.lower(),
            full_name=full_name,
            password_hash=hash_password(password),
            role=role,
        )
        session.add(user)
    else:
        user.full_name = full_name
        user.password_hash = hash_password(password)
        user.role = role
        user.is_active = True
    await session.commit()
    await session.refresh(user)
    return UserRead.model_validate(user)
