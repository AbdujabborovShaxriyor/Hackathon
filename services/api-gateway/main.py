from __future__ import annotations

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.common.audit import record_audit
from libs.common.database import get_async_session, init_db
from libs.common.dependencies import get_bearer_token, get_current_user
from libs.common.models import AuditLog, GovernmentRequest, Response, User
from libs.schemas.contracts import (
    AuditLogRead,
    HealthResponse,
    RequestPipelineResponse,
    ResponseRead,
    WorkflowDecisionRequest,
    WorkflowEditRequest,
)
from clients import ServiceClients
from service import get_request_detail, process_request


app = FastAPI(title="API Gateway", version="1.0.0")


@app.on_event("startup")
async def startup() -> None:
    await init_db()


@app.get("/", include_in_schema=False)
async def root() -> HTMLResponse:
    return HTMLResponse(
        """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Legal AI Response Platform</title>
    <style>
      :root {
        --bg: #f4efe6;
        --panel: rgba(255, 252, 247, 0.92);
        --ink: #1f2937;
        --muted: #5f6b7a;
        --accent: #0f766e;
        --accent-2: #c2410c;
        --border: rgba(31, 41, 55, 0.12);
        --shadow: 0 20px 40px rgba(31, 41, 55, 0.12);
      }

      * { box-sizing: border-box; }

      body {
        margin: 0;
        font-family: Georgia, "Times New Roman", serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(15, 118, 110, 0.14), transparent 28%),
          radial-gradient(circle at top right, rgba(194, 65, 12, 0.12), transparent 24%),
          linear-gradient(180deg, #f8f4ed 0%, var(--bg) 100%);
      }

      main {
        width: min(1100px, calc(100% - 32px));
        margin: 32px auto 48px;
      }

      .hero, .panel {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 24px;
        box-shadow: var(--shadow);
      }

      .hero {
        padding: 32px;
        margin-bottom: 24px;
      }

      h1 {
        margin: 0 0 12px;
        font-size: clamp(2.2rem, 5vw, 4rem);
        line-height: 0.95;
      }

      .lead {
        margin: 0;
        max-width: 760px;
        font-family: "Segoe UI", sans-serif;
        font-size: 1.05rem;
        line-height: 1.6;
        color: var(--muted);
      }

      .grid {
        display: grid;
        grid-template-columns: 1.15fr 0.85fr;
        gap: 24px;
      }

      .panel {
        padding: 24px;
      }

      h2, h3 {
        margin-top: 0;
      }

      form {
        display: grid;
        gap: 14px;
      }

      label {
        display: grid;
        gap: 6px;
        font-family: "Segoe UI", sans-serif;
        font-size: 0.95rem;
        font-weight: 600;
      }

      input, textarea, button {
        width: 100%;
        border-radius: 14px;
        border: 1px solid var(--border);
        padding: 12px 14px;
        font: inherit;
      }

      input, textarea {
        background: #fffdf9;
      }

      textarea {
        min-height: 120px;
        resize: vertical;
      }

      button {
        cursor: pointer;
        border: none;
        background: linear-gradient(135deg, var(--accent), #115e59);
        color: white;
        font-family: "Segoe UI", sans-serif;
        font-weight: 700;
      }

      button.secondary {
        background: linear-gradient(135deg, var(--accent-2), #9a3412);
      }

      .actions {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
      }

      .actions > * {
        flex: 1 1 180px;
      }

      .steps, .links {
        display: grid;
        gap: 12px;
      }

      .step, .result-block {
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 14px 16px;
        background: rgba(255, 255, 255, 0.65);
      }

      .eyebrow {
        font-family: "Segoe UI", sans-serif;
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--accent);
      }

      .status {
        margin: 12px 0 0;
        font-family: "Segoe UI", sans-serif;
        color: var(--muted);
      }

      pre {
        margin: 0;
        white-space: pre-wrap;
        word-break: break-word;
        font-family: Consolas, monospace;
        font-size: 0.92rem;
      }

      a {
        color: var(--accent);
      }

      @media (max-width: 860px) {
        .grid {
          grid-template-columns: 1fr;
        }
      }
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <div class="eyebrow">Operational Console</div>
        <h1>Legal AI Response Platform</h1>
        <p class="lead">
          Submit a government request, trigger ingestion, classification, draft generation,
          and compliance review, then inspect the pipeline output from the gateway.
        </p>
        <p class="status" id="health-status">Checking platform health...</p>
      </section>

      <section class="grid">
        <section class="panel">
          <h2>Process New Request</h2>
          <form id="request-form">
            <label>
              Bearer token
              <input id="token" name="token" type="password" placeholder="Paste the JWT from /auth/login" required />
            </label>
            <label>
              Request subject
              <input id="subject" name="subject" type="text" placeholder="Tax inquiry regarding Q1 filings" required />
            </label>
            <label>
              Government letter or attachment
              <input id="file" name="file" type="file" required />
            </label>
            <div class="actions">
              <button type="submit">Run Full Pipeline</button>
              <button class="secondary" type="button" id="health-button">Recheck Health</button>
            </div>
          </form>
          <p class="status" id="submit-status">Waiting for input.</p>
          <div class="result-block">
            <h3>Pipeline Result</h3>
            <pre id="result">{}</pre>
          </div>
        </section>

        <aside class="panel">
          <h2>Main Logic</h2>
          <div class="steps">
            <div class="step"><strong>1. Ingestion</strong><br />Extract text from uploaded PDF or DOCX, with OCR fallback when needed.</div>
            <div class="step"><strong>2. Classification</strong><br />Detect authority type, estimate legal risk, and store rationale.</div>
            <div class="step"><strong>3. Generation</strong><br />Build a grounded response draft using the RAG service and available evidence.</div>
            <div class="step"><strong>4. Compliance</strong><br />Check forbidden language, required legal terms, and workflow readiness.</div>
          </div>

          <h3 style="margin-top: 24px;">Quick Links</h3>
          <div class="links">
            <a href="/health" target="_blank" rel="noreferrer">Gateway health</a>
            <a href="/docs" target="_blank" rel="noreferrer">API docs</a>
            <a href="http://localhost:8001/health" target="_blank" rel="noreferrer">Auth service health</a>
          </div>
        </aside>
      </section>
    </main>

    <script>
      const healthStatus = document.getElementById("health-status");
      const submitStatus = document.getElementById("submit-status");
      const result = document.getElementById("result");
      const form = document.getElementById("request-form");

      async function checkHealth() {
        healthStatus.textContent = "Checking platform health...";
        try {
          const response = await fetch("/health");
          const data = await response.json();
          healthStatus.textContent = response.ok
            ? `Gateway status: ${data.status}`
            : `Gateway returned ${response.status}`;
        } catch (error) {
          healthStatus.textContent = `Health check failed: ${error.message}`;
        }
      }

      document.getElementById("health-button").addEventListener("click", checkHealth);

      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const token = document.getElementById("token").value.trim();
        const subject = document.getElementById("subject").value.trim();
        const fileInput = document.getElementById("file");

        if (!token || !subject || !fileInput.files.length) {
          submitStatus.textContent = "Token, subject, and file are all required.";
          return;
        }

        const body = new FormData();
        body.append("subject", subject);
        body.append("file", fileInput.files[0]);

        submitStatus.textContent = "Running ingestion, classification, generation, and compliance checks...";
        result.textContent = "{}";

        try {
          const response = await fetch("/v1/requests", {
            method: "POST",
            headers: {
              Authorization: `Bearer ${token}`
            },
            body
          });

          const payload = await response.json();
          if (!response.ok) {
            submitStatus.textContent = `Pipeline failed with ${response.status}.`;
            result.textContent = JSON.stringify(payload, null, 2);
            return;
          }

          submitStatus.textContent = "Pipeline completed successfully.";
          result.textContent = JSON.stringify(payload, null, 2);
        } catch (error) {
          submitStatus.textContent = `Request failed: ${error.message}`;
        }
      });

      checkHealth();
    </script>
  </body>
</html>
        """
    )


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@app.post("/v1/requests", response_model=RequestPipelineResponse)
async def create_request(
    file: UploadFile = File(...),
    subject: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> RequestPipelineResponse:
    if current_user.role not in {"admin", "legal_operator"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    return await process_request(session, file=file, subject=subject, current_user_id=current_user.id)


@app.get("/v1/requests/{request_id}")
async def read_request(
    request_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in {"admin", "legal_operator", "auditor"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    return await get_request_detail(session, request_id)


@app.post("/v1/responses/{response_id}/approve", response_model=ResponseRead)
async def approve_response(
    response_id: str,
    payload: WorkflowDecisionRequest,
    token: str = Depends(get_bearer_token),
    current_user: User = Depends(get_current_user),
) -> ResponseRead:
    if current_user.role not in {"admin", "legal_operator"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    clients = ServiceClients()
    result = await clients.workflow_action(f"/workflow/{response_id}/approve", payload.model_dump(), token=token)
    return ResponseRead.model_validate(result)


@app.post("/v1/responses/{response_id}/reject", response_model=ResponseRead)
async def reject_response(
    response_id: str,
    payload: WorkflowDecisionRequest,
    token: str = Depends(get_bearer_token),
    current_user: User = Depends(get_current_user),
) -> ResponseRead:
    if current_user.role not in {"admin", "legal_operator"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    clients = ServiceClients()
    result = await clients.workflow_action(f"/workflow/{response_id}/reject", payload.model_dump(), token=token)
    return ResponseRead.model_validate(result)


@app.post("/v1/responses/{response_id}/edit", response_model=ResponseRead)
async def edit_response(
    response_id: str,
    payload: WorkflowEditRequest,
    token: str = Depends(get_bearer_token),
    current_user: User = Depends(get_current_user),
) -> ResponseRead:
    if current_user.role not in {"admin", "legal_operator"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    clients = ServiceClients()
    result = await clients.workflow_action(f"/workflow/{response_id}/edit", payload.model_dump(), token=token)
    return ResponseRead.model_validate(result)


@app.get("/v1/audit", response_model=list[AuditLogRead])
async def audit_logs(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> list[AuditLogRead]:
    if current_user.role not in {"admin", "auditor"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    result = await session.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(1000))
    return [AuditLogRead.model_validate(row) for row in result.scalars().all()]
