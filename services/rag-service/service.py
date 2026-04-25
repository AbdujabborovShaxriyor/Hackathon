from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.common.models import DocumentChunk
from libs.schemas.contracts import Citation, RagDocumentChunk, RagGenerateResponse, RagIndexRequest
from libs.utils.file_handling import sha256_text
from libs.utils.llm import (
    build_grounded_prompt,
    get_embedding_client,
    get_grounded_llm,
)


def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 100) -> list[str]:
    normalized = text.replace("\r\n", "\n").strip()
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        step_back = min(chunk_overlap, max(0, chunk_size - 1))
        start = max(start + 1, end - step_back)
    return chunks


def _get_embedding_client():
    return get_embedding_client()


def _get_llm_client():
    return get_grounded_llm()


async def index_document(session: AsyncSession, payload: RagIndexRequest) -> int:
    embedding_client = _get_embedding_client()
    chunks = chunk_text(payload.text, chunk_size=payload.chunk_size, chunk_overlap=payload.chunk_overlap)
    if not chunks:
        return 0

    for index, chunk in enumerate(chunks):
        embedding = await embedding_client.embed(chunk)
        session.add(
            DocumentChunk(
                request_id=payload.request_id,
                source_name=payload.source_name,
                chunk_index=index,
                content=chunk,
                content_hash=sha256_text(chunk),
                embedding=embedding,
                metadata=payload.metadata,
            )
        )
    await session.commit()
    return len(chunks)


async def search_chunks(session: AsyncSession, query: str, top_k: int = 5) -> list[RagDocumentChunk]:
    embedding_client = _get_embedding_client()
    query_embedding = await embedding_client.embed(query)
    distance_expr = DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")
    stmt = (
        select(DocumentChunk, distance_expr)
        .order_by(distance_expr)
        .limit(top_k)
    )
    result = await session.execute(stmt)
    rows = result.all()
    documents: list[RagDocumentChunk] = []
    for document, distance in rows:
        score = max(0.0, 1.0 - float(distance or 0.0))
        documents.append(
            RagDocumentChunk(
                id=document.id,
                source_name=document.source_name,
                chunk_index=document.chunk_index,
                content=document.content,
                score=score,
                metadata=document.metadata or {},
            )
        )
    return documents


async def generate_grounded_answer(
    session: AsyncSession,
    *,
    query: str,
    authority: str,
    risk_score: int,
    request_id: str | None = None,
    top_k: int = 5,
) -> RagGenerateResponse:
    evidence = await search_chunks(session, query=f"{authority} {query}", top_k=top_k)
    citations = [
        Citation(source_name=item.source_name, chunk_index=item.chunk_index, excerpt=item.content[:280])
        for item in evidence
    ]
    context_blocks = [item.model_dump() for item in evidence]
    prompt = build_grounded_prompt(query=query, authority=authority, risk_score=risk_score, context_blocks=context_blocks)
    llm_client = _get_llm_client()
    answer = await llm_client.generate(prompt=prompt, query=query, citations=citations)
    return RagGenerateResponse(answer=answer, citations=citations, evidence=evidence)
