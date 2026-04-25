from __future__ import annotations

from fastapi import FastAPI

from libs.schemas.contracts import ClassificationRequest, ClassificationResult, HealthResponse
from service import classify_text


app = FastAPI(title="Classification Service", version="1.0.0")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@app.post("/classify", response_model=ClassificationResult)
async def classify(payload: ClassificationRequest) -> ClassificationResult:
    return classify_text(payload.text)
