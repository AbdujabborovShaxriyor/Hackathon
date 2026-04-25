from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


AuthorityType = Literal["tax", "prosecutor", "central_bank", "court", "other"]
UserRole = Literal["admin", "legal_operator", "auditor"]
RequestStatus = Literal["received", "classified", "draft_ready", "under_review", "approved", "rejected", "needs_revision"]
ResponseStatus = Literal["draft", "under_review", "approved", "rejected", "revised"]


class HealthResponse(BaseModel):
    status: str = "ok"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=12, max_length=256)
    role: UserRole = "legal_operator"

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if not any(ch.isdigit() for ch in value):
            raise ValueError("password must contain at least one digit")
        if not any(ch.isalpha() for ch in value):
            raise ValueError("password must contain letters")
        return value


class UserRead(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class BootstrapAdminRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    bootstrap_token: str


class GovernmentRequestCreate(BaseModel):
    source_filename: str
    source_hash: str
    raw_text: str
    subject: str
    authority: AuthorityType
    risk_score: int = Field(ge=0, le=100)
    classification: dict[str, Any] = Field(default_factory=dict)


class GovernmentRequestRead(BaseModel):
    id: str
    source_filename: str
    source_hash: str
    raw_text: str
    authority: AuthorityType
    subject: str
    risk_score: int
    classification: dict[str, Any]
    status: RequestStatus
    created_by: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IngestionResult(BaseModel):
    file_name: str
    file_hash: str
    text: str
    page_count: int = 0
    method: str


class ClassificationRequest(BaseModel):
    text: str = Field(min_length=1)


class ClassificationResult(BaseModel):
    authority: AuthorityType
    risk_score: int = Field(ge=0, le=100)
    rationale: str
    labels: list[str] = Field(default_factory=list)


class RagDocumentChunk(BaseModel):
    id: str
    source_name: str
    chunk_index: int
    content: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class RagSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class RagIndexRequest(BaseModel):
    source_name: str = Field(min_length=1)
    text: str = Field(min_length=1)
    request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    chunk_size: int = Field(default=1000, ge=200, le=4000)
    chunk_overlap: int = Field(default=100, ge=0, le=1000)


class RagIndexResponse(BaseModel):
    indexed_chunks: int
    source_name: str


class RagGenerateRequest(BaseModel):
    query: str = Field(min_length=1)
    authority: AuthorityType
    risk_score: int = Field(ge=0, le=100)
    request_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class Citation(BaseModel):
    source_name: str
    chunk_index: int
    excerpt: str


class RagGenerateResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    evidence: list[RagDocumentChunk] = Field(default_factory=list)


class ComplianceIssue(BaseModel):
    code: str
    severity: Literal["low", "medium", "high"]
    message: str
    field: str | None = None


class ComplianceRequest(BaseModel):
    text: str = Field(min_length=1)
    authority: AuthorityType


class ComplianceResult(BaseModel):
    passed: bool
    issues: list[ComplianceIssue] = Field(default_factory=list)
    required_terms_found: list[str] = Field(default_factory=list)
    forbidden_terms_found: list[str] = Field(default_factory=list)


class WorkflowEditRequest(BaseModel):
    final_text: str = Field(min_length=1)
    comment: str | None = None


class WorkflowDecisionRequest(BaseModel):
    comment: str | None = None


class ResponseRead(BaseModel):
    id: str
    request_id: str
    draft_text: str
    final_text: str | None
    citations: list[dict[str, Any]]
    compliance_result: dict[str, Any]
    status: ResponseStatus
    version: int
    created_by: str | None
    approved_by: str | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AuditLogRead(BaseModel):
    id: str
    request_id: str | None
    response_id: str | None
    actor_id: str | None
    action: str
    entity_type: str
    before_state: dict[str, Any]
    after_state: dict[str, Any]
    details: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class RequestPipelineResponse(BaseModel):
    request: GovernmentRequestRead
    response: ResponseRead
    classification: ClassificationResult
    ingestion: IngestionResult
    compliance: ComplianceResult
