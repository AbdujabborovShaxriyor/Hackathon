# API Documentation

## Auth Service

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/bootstrap-admin`

## Ingestion Service

- `POST /ingest`
- `GET /health`

## Classification Service

- `POST /classify`
- `GET /health`

## RAG Service

- `POST /documents/index`
- `POST /generate`
- `POST /search`
- `GET /health`

## Compliance Service

- `POST /compliance/check`
- `GET /health`

## Workflow Service

- `POST /workflow/{response_id}/approve`
- `POST /workflow/{response_id}/reject`
- `POST /workflow/{response_id}/edit`
- `GET /workflow/{response_id}`
- `GET /health`

## API Gateway

- `POST /v1/requests`
- `GET /v1/requests/{request_id}`
- `POST /v1/responses/{response_id}/approve`
- `POST /v1/responses/{response_id}/reject`
- `POST /v1/responses/{response_id}/edit`
- `GET /v1/audit`
- `GET /health`

