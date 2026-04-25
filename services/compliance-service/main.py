from __future__ import annotations

from fastapi import FastAPI

from libs.schemas.contracts import ComplianceRequest, ComplianceResult, HealthResponse
from service import check_compliance


app = FastAPI(title="Compliance Service", version="1.0.0")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@app.post("/compliance/check", response_model=ComplianceResult)
async def compliance_check(payload: ComplianceRequest) -> ComplianceResult:
    return check_compliance(payload.text, payload.authority)
