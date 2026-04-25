from __future__ import annotations

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.common.audit import record_audit
from libs.common.models import AuditLog, GovernmentRequest, Response
from libs.schemas.contracts import RequestPipelineResponse, ResponseRead, GovernmentRequestRead
from clients import ServiceClients


async def process_request(
    session: AsyncSession,
    *,
    file: UploadFile,
    subject: str,
    current_user_id: str,
) -> RequestPipelineResponse:
    clients = ServiceClients()
    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    ingestion = await clients.ingest(file.filename or "upload.bin", content)
    classification_input = f"{subject}\n\n{ingestion['text']}"
    classification = await clients.classify(classification_input)

    request_row = GovernmentRequest(
        source_filename=ingestion["file_name"],
        source_hash=ingestion["file_hash"],
        raw_text=ingestion["text"],
        authority=classification["authority"],
        subject=subject,
        risk_score=classification["risk_score"],
        classification={"rationale": classification["rationale"], "labels": classification["labels"]},
        status="classified",
        created_by=current_user_id,
    )
    session.add(request_row)
    await session.flush()
    await record_audit(
        session,
        action="request_received",
        entity_type="request",
        actor_id=current_user_id,
        request_id=request_row.id,
        after_state={"subject": subject, "authority": classification["authority"]},
        metadata={"source_filename": ingestion["file_name"], "method": ingestion["method"]},
    )

    generation = await clients.generate(
        {
            "query": f"{subject}\n\n{ingestion['text'][:4000]}",
            "authority": classification["authority"],
            "risk_score": classification["risk_score"],
            "request_id": request_row.id,
            "top_k": 5,
        }
    )
    compliance = await clients.compliance({"text": generation["answer"], "authority": classification["authority"]})

    response_row = Response(
        request_id=request_row.id,
        draft_text=generation["answer"],
        final_text=None,
        citations=generation["citations"],
        compliance_result=compliance,
        status="under_review" if compliance["passed"] else "revised",
        version=1,
        created_by=current_user_id,
    )
    session.add(response_row)
    await session.flush()
    request_row.status = "draft_ready" if compliance["passed"] else "needs_revision"
    await record_audit(
        session,
        action="response_generated",
        entity_type="response",
        actor_id=current_user_id,
        request_id=request_row.id,
        response_id=response_row.id,
        after_state={"status": response_row.status, "compliance": compliance},
    )
    await session.commit()
    await session.refresh(request_row)
    await session.refresh(response_row)

    return RequestPipelineResponse(
        request=GovernmentRequestRead.model_validate(request_row),
        response=ResponseRead.model_validate(response_row),
        classification=classification,
        ingestion=ingestion,
        compliance=compliance,
    )


async def get_request_detail(session: AsyncSession, request_id: str) -> dict:
    request_result = await session.execute(select(GovernmentRequest).where(GovernmentRequest.id == request_id))
    request_row = request_result.scalar_one_or_none()
    if request_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    response_result = await session.execute(select(Response).where(Response.request_id == request_id).order_by(Response.created_at.desc()))
    response_row = response_result.scalars().first()
    return {
        "request": GovernmentRequestRead.model_validate(request_row),
        "response": ResponseRead.model_validate(response_row) if response_row else None,
    }
