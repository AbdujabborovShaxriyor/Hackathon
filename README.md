# Legal AI Response Platform

Production-oriented microservice platform for automating legal responses to government authorities with RAG, compliance checks, human approval, and auditability.

## Architecture

- `api-gateway`: public FastAPI entrypoint and orchestration layer
- `ingestion-service`: file upload, text extraction, OCR fallback
- `classification-service`: authority classification and risk scoring
- `rag-service`: retrieval, prompt building, grounded generation, pgvector search
- `compliance-service`: legal rule engine and format validation
- `workflow-service`: approval, rejection, edits, and state transitions
- `auth-service`: JWT authentication and RBAC
- `libs/common`: shared database, models, security, and audit helpers
- `libs/schemas`: shared request/response contracts
- `libs/utils`: extraction, prompting, and LLM abstraction utilities

## Quick Start

1. Copy `.env.example` to `.env` and change the secrets.
2. Start the stack:

```bash
docker compose up --build
```

`docker compose` will run the one-off `migrations` service first so the database schema is created before the app services come up.

3. Open the gateway:

```text
http://localhost:8000/docs
```

## Local Development

Install dependencies:

```bash
python -m pip install -e .[dev]
```

Run database migrations manually if you want to manage schema outside service startup:

```bash
alembic upgrade head
```

Run a service locally:

```bash
uvicorn main:app --reload --port 8000
```

from inside a service directory after exporting `PYTHONPATH` to the repo root.

## Core Flow

1. A user authenticates through `auth-service`.
2. The gateway accepts a government request and stores the raw input.
3. Ingestion extracts text from PDF/DOCX and falls back to OCR.
4. Classification tags the authority and risk level.
5. RAG retrieves legal context from pgvector and generates a grounded draft.
6. Compliance checks for forbidden language, required legal terms, and formatting.
7. Workflow assigns the draft to a human operator for approval or edit.
8. Every action is written to `audit_logs`.

## Provider Settings

- `LLM_PROVIDER=vertex` uses Gemini/Vertex AI.
- `LLM_PROVIDER=openrouter` uses an OpenAI-compatible provider such as OpenRouter.
- `EMBEDDING_PROVIDER=deterministic` keeps vector generation local and predictable.
- `EMBEDDING_PROVIDER=openai` uses OpenAI-compatible embeddings if your provider supports them.

## Production Notes

- Keep `AUTO_MIGRATE_DB=true` for local development.
- For production, run migrations in a dedicated job or release step and set `AUTO_MIGRATE_DB=false`.
- Rotate any API key that was ever pasted into chat or into version control history.

## Testing

```bash
pytest -q
```

## API Docs

See [docs/api.md](docs/api.md) for endpoint coverage and request shapes.
