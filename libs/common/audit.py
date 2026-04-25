from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from libs.common.models import AuditLog


async def record_audit(
    session: AsyncSession,
    *,
    action: str,
    entity_type: str,
    actor_id: str | None = None,
    request_id: str | None = None,
    response_id: str | None = None,
    before_state: dict | None = None,
    after_state: dict | None = None,
    metadata: dict | None = None,
) -> AuditLog:
    entry = AuditLog(
        action=action,
        entity_type=entity_type,
        actor_id=actor_id,
        request_id=request_id,
        response_id=response_id,
        before_state=before_state or {},
        after_state=after_state or {},
        details=metadata or {},
    )
    session.add(entry)
    await session.flush()
    return entry
