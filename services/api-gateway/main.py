from __future__ import annotations

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.common.audit import record_audit
from libs.common.database import get_async_session, init_db
from libs.common.dependencies import get_bearer_token, get_current_user
from libs.common.models import AuditLog, GovernmentRequest, Response, User
from libs.schemas.contracts import (
    AuditLogRead,
    HealthResponse,
    RequestPipelineResponse,
    ResponseRead,
    WorkflowDecisionRequest,
    WorkflowEditRequest,
)
from clients import ServiceClients
from service import get_request_detail, process_request


app = FastAPI(title="API Gateway", version="1.0.0")


@app.on_event("startup")
async def startup() -> None:
    await init_db()


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@app.post("/v1/requests", response_model=RequestPipelineResponse)
async def create_request(
    file: UploadFile = File(...),
    subject: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> RequestPipelineResponse:
    if current_user.role not in {"admin", "legal_operator"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    return await process_request(session, file=file, subject=subject, current_user_id=current_user.id)


@app.get("/v1/requests/{request_id}")
async def read_request(
    request_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in {"admin", "legal_operator", "auditor"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    return await get_request_detail(session, request_id)


@app.post("/v1/responses/{response_id}/approve", response_model=ResponseRead)
async def approve_response(
    response_id: str,
    payload: WorkflowDecisionRequest,
    token: str = Depends(get_bearer_token),
    current_user: User = Depends(get_current_user),
) -> ResponseRead:
    if current_user.role not in {"admin", "legal_operator"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    clients = ServiceClients()
    result = await clients.workflow_action(f"/workflow/{response_id}/approve", payload.model_dump(), token=token)
    return ResponseRead.model_validate(result)


@app.post("/v1/responses/{response_id}/reject", response_model=ResponseRead)
async def reject_response(
    response_id: str,
    payload: WorkflowDecisionRequest,
    token: str = Depends(get_bearer_token),
    current_user: User = Depends(get_current_user),
) -> ResponseRead:
    if current_user.role not in {"admin", "legal_operator"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    clients = ServiceClients()
    result = await clients.workflow_action(f"/workflow/{response_id}/reject", payload.model_dump(), token=token)
    return ResponseRead.model_validate(result)


@app.post("/v1/responses/{response_id}/edit", response_model=ResponseRead)
async def edit_response(
    response_id: str,
    payload: WorkflowEditRequest,
    token: str = Depends(get_bearer_token),
    current_user: User = Depends(get_current_user),
) -> ResponseRead:
    if current_user.role not in {"admin", "legal_operator"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    clients = ServiceClients()
    result = await clients.workflow_action(f"/workflow/{response_id}/edit", payload.model_dump(), token=token)
    return ResponseRead.model_validate(result)


@app.get("/v1/audit", response_model=list[AuditLogRead])
async def audit_logs(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> list[AuditLogRead]:
    if current_user.role not in {"admin", "auditor"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    result = await session.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(1000))
    return [AuditLogRead.model_validate(row) for row in result.scalars().all()]
