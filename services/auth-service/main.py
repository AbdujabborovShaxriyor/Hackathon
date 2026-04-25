from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.common.config import get_settings
from libs.common.database import get_async_session, init_db
from libs.common.dependencies import get_current_user
from libs.common.models import User
from libs.schemas.contracts import BootstrapAdminRequest, HealthResponse, LoginRequest, TokenResponse, UserCreate, UserRead
from service import authenticate_user, bootstrap_admin, create_user


settings = get_settings()
app = FastAPI(title="Auth Service", version="1.0.0")


@app.on_event("startup")
async def startup() -> None:
    await init_db()


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@app.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate, session: AsyncSession = Depends(get_async_session)) -> UserRead:
    try:
        return await create_user(session, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@app.post("/auth/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_async_session)) -> TokenResponse:
    try:
        return await authenticate_user(session, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@app.get("/auth/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@app.post("/auth/bootstrap-admin", response_model=UserRead)
async def bootstrap(payload: BootstrapAdminRequest, session: AsyncSession = Depends(get_async_session)) -> UserRead:
    if payload.bootstrap_token != settings.bootstrap_admin_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid bootstrap token")
    return await bootstrap_admin(session, email=payload.email, full_name=payload.full_name, password=payload.password)


@app.get("/auth/users", response_model=list[UserRead])
async def list_users(session: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)) -> list[UserRead]:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    result = await session.execute(select(User).order_by(User.created_at.desc()))
    return [UserRead.model_validate(user) for user in result.scalars().all()]
