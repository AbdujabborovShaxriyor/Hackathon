# Architecture

## Design Goals

- Minimize hallucination by forcing all generation through retrieval-backed context
- Keep every state transition auditable
- Separate concerns into independently deployable services
- Make the system secure by default with JWT, RBAC, validation, and file hygiene
- Keep the platform production-friendly with async IO, caching hooks, and containerization

## Service Responsibilities

### API Gateway

- Validates the caller JWT
- Orchestrates ingestion, classification, RAG, compliance, and workflow persistence
- Exposes public endpoints for request handling and audit inspection

### Ingestion Service

- Handles PDF, DOCX, and email ingestion patterns
- Extracts text from binary files
- Uses OCR if native extraction is insufficient

### Classification Service

- Detects authority type
- Assigns a risk score
- Produces routing metadata for downstream services

### RAG Service

- Stores and retrieves chunks in pgvector
- Builds prompts from retrieved evidence
- Generates responses only from supplied context

### Compliance Service

- Detects forbidden phrases
- Checks that required legal terms are present
- Verifies document structure before human review

### Workflow Service

- Manages draft, review, approved, rejected, and revised states
- Records user edits and decisions

### Auth Service

- Issues JWTs
- Enforces roles: `admin`, `legal_operator`, `auditor`

## Data Model

- `users`: identity and role-based access
- `requests`: incoming government requests
- `responses`: generated and edited response drafts
- `audit_logs`: immutable trace of all actions
- `document_chunks`: indexed knowledge base fragments for RAG

## Deployment

- PostgreSQL with pgvector for transactional and vector storage
- Redis for queueing and caching hooks
- FastAPI containers per service
- Kubernetes manifests for each deployable unit

