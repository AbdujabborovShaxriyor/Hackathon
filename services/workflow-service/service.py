from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.common.audit import record_audit
from libs.common.models import Response, GovernmentRequest
from libs.schemas.contracts import ResponseRead, WorkflowDecisionRequest, WorkflowEditRequest


async def get_response(session: AsyncSession, response_id: str) -> Response | None:
    result = await session.execute(select(Response).where(Response.id == response_id))
    return result.scalar_one_or_none()


async def approve_response(session: AsyncSession, response_id: str, actor_id: str | None, comment: str | None = None) -> ResponseRead:
    response = await get_response(session, response_id)
    if response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Response not found")
    before = response.__dict__.copy()
    response.status = "approved"
    response.approved_by = actor_id
    response.approved_at = datetime.now(timezone.utc)
    response.final_text = response.final_text or response.draft_text
    request = await session.get(GovernmentRequest, response.request_id)
    if request is not None:
        request.status = "approved"
    await record_audit(
        session,
        action="approve",
        entity_type="response",
        actor_id=actor_id,
        request_id=response.request_id,
        response_id=response.id,
        before_state={"status": before.get("status")},
        after_state={"status": response.status},
        metadata={"comment": comment or ""},
    )
    await session.commit()
    await session.refresh(response)
    return ResponseRead.model_validate(response)


async def reject_response(session: AsyncSession, response_id: str, actor_id: str | None, comment: str | None = None) -> ResponseRead:
    response = await get_response(session, response_id)
    if response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Response not found")
    before = response.__dict__.copy()
    response.status = "rejected"
    request = await session.get(GovernmentRequest, response.request_id)
    if request is not None:
        request.status = "rejected"
    await record_audit(
        session,
        action="reject",
        entity_type="response",
        actor_id=actor_id,
        request_id=response.request_id,
        response_id=response.id,
        before_state={"status": before.get("status")},
        after_state={"status": response.status},
        metadata={"comment": comment or ""},
    )
    await session.commit()
    await session.refresh(response)
    return ResponseRead.model_validate(response)


async def edit_response(session: AsyncSession, response_id: str, actor_id: str | None, payload: WorkflowEditRequest) -> ResponseRead:
    response = await get_response(session, response_id)
    if response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Response not found")
    before = response.__dict__.copy()
    response.final_text = payload.final_text
    response.status = "revised"
    response.version += 1
    request = await session.get(GovernmentRequest, response.request_id)
    if request is not None:
        request.status = "needs_revision"
    await record_audit(
        session,
        action="edit",
        entity_type="response",
        actor_id=actor_id,
        request_id=response.request_id,
        response_id=response.id,
        before_state={"final_text": before.get("final_text"), "status": before.get("status")},
        after_state={"final_text": response.final_text, "status": response.status},
        metadata={"comment": payload.comment or ""},
    )
    await session.commit()
    await session.refresh(response)
    return ResponseRead.model_validate(response)

