from __future__ import annotations

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from libs.common.database import get_async_session, init_db
from libs.schemas.contracts import HealthResponse, RagGenerateRequest, RagGenerateResponse, RagIndexRequest, RagIndexResponse, RagSearchRequest, RagDocumentChunk
from service import generate_grounded_answer, index_document, search_chunks


app = FastAPI(title="RAG Service", version="1.0.0")


@app.on_event("startup")
async def startup() -> None:
    await init_db()


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@app.post("/documents/index", response_model=RagIndexResponse)
async def index_documents(payload: RagIndexRequest, session: AsyncSession = Depends(get_async_session)) -> RagIndexResponse:
    count = await index_document(session, payload)
    return RagIndexResponse(indexed_chunks=count, source_name=payload.source_name)


@app.post("/search", response_model=list[RagDocumentChunk])
async def search(payload: RagSearchRequest, session: AsyncSession = Depends(get_async_session)) -> list[RagDocumentChunk]:
    return await search_chunks(session, payload.query, payload.top_k)


@app.post("/generate", response_model=RagGenerateResponse)
async def generate(payload: RagGenerateRequest, session: AsyncSession = Depends(get_async_session)) -> RagGenerateResponse:
    return await generate_grounded_answer(
        session,
        query=payload.query,
        authority=payload.authority,
        risk_score=payload.risk_score,
        request_id=payload.request_id,
        top_k=payload.top_k,
    )
