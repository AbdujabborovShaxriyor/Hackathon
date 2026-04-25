from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from libs.common.database import get_async_session, init_db
from libs.common.dependencies import get_current_user
from libs.common.models import User
from libs.schemas.contracts import HealthResponse, ResponseRead, WorkflowEditRequest, WorkflowDecisionRequest
from service import approve_response, edit_response, get_response, reject_response


app = FastAPI(title="Workflow Service", version="1.0.0")


@app.on_event("startup")
async def startup() -> None:
    await init_db()


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@app.get("/workflow/{response_id}", response_model=ResponseRead)
async def read_response(response_id: str, session: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)) -> ResponseRead:
    if current_user.role not in {"admin", "legal_operator", "auditor"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    response = await get_response(session, response_id)
    if response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Response not found")
    return ResponseRead.model_validate(response)


@app.post("/workflow/{response_id}/approve", response_model=ResponseRead)
async def approve(
    response_id: str,
    payload: WorkflowDecisionRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> ResponseRead:
    if current_user.role not in {"admin", "legal_operator"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    return await approve_response(session, response_id, current_user.id, payload.comment)


@app.post("/workflow/{response_id}/reject", response_model=ResponseRead)
async def reject(
    response_id: str,
    payload: WorkflowDecisionRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> ResponseRead:
    if current_user.role not in {"admin", "legal_operator"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    return await reject_response(session, response_id, current_user.id, payload.comment)


@app.post("/workflow/{response_id}/edit", response_model=ResponseRead)
async def edit(
    response_id: str,
    payload: WorkflowEditRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> ResponseRead:
    if current_user.role not in {"admin", "legal_operator"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    return await edit_response(session, response_id, current_user.id, payload)
