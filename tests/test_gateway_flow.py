from __future__ import annotations

from pathlib import Path
import asyncio
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api-gateway"))

from service import process_request  # type: ignore  # noqa: E402


class FakeUpload:
    def __init__(self, filename: str, content: bytes) -> None:
        self.filename = filename
        self._content = content

    async def read(self) -> bytes:
        return self._content


class FakeSession:
    def __init__(self) -> None:
        self.objects = []

    def add(self, obj) -> None:
        self.objects.append(obj)

    async def flush(self) -> None:
        for obj in self.objects:
            if getattr(obj, "id", None) in {None, ""}:
                setattr(obj, "id", str(uuid4()))

    async def commit(self) -> None:
        return None

    async def refresh(self, obj) -> None:
        return None


class FakeClients:
    async def ingest(self, file_name: str, file_bytes: bytes):
        return {
            "file_name": file_name,
            "file_hash": "abc123",
            "text": "Background. Analysis. Conclusion. respectfully subject to verification without prejudice based on the documents reviewed.",
            "page_count": 1,
            "method": "raw",
        }

    async def classify(self, text: str):
        return {"authority": "tax", "risk_score": 40, "rationale": "ok", "labels": ["tax"]}

    async def generate(self, payload: dict):
        return {
            "answer": "Background. Analysis. Conclusion. respectfully subject to verification without prejudice based on the documents reviewed.",
            "citations": [{"source_name": "law.md", "chunk_index": 0, "excerpt": "citation"}],
            "evidence": [],
        }

    async def compliance(self, payload: dict):
        return {"passed": True, "issues": [], "required_terms_found": ["respectfully"], "forbidden_terms_found": []}


def test_gateway_pipeline_creates_request_and_response(monkeypatch) -> None:
    import service as gateway_service  # type: ignore

    monkeypatch.setattr(gateway_service, "ServiceClients", FakeClients)
    session = FakeSession()
    upload = FakeUpload("request.pdf", b"dummy-bytes")

    result = asyncio.run(process_request(session, file=upload, subject="Tax authority filing response", current_user_id="user-1"))

    assert result.request.authority == "tax"
    assert result.response.status == "under_review"
    assert result.compliance["passed"] is True
    assert len(session.objects) >= 2
