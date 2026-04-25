from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile, status

from libs.common.config import get_settings
from libs.schemas.contracts import HealthResponse, IngestionResult
from service import ingest_file


app = FastAPI(title="Ingestion Service", version="1.0.0")
settings = get_settings()
ALLOWED_SUFFIXES = {".pdf", ".docx", ".doc", ".eml", ".txt"}


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@app.post("/ingest", response_model=IngestionResult)
async def ingest(file: UploadFile = File(...)) -> IngestionResult:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")
    if not any(file.filename.lower().endswith(suffix) for suffix in ALLOWED_SUFFIXES):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported file type")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
    return await ingest_file(file.filename, content)
