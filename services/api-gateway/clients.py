from __future__ import annotations

from typing import Any

import httpx
from fastapi import HTTPException, status

from libs.common.config import get_settings


class ServiceClients:
    def __init__(self) -> None:
        settings = get_settings()
        self.ingestion = settings.ingestion_service_url
        self.classification = settings.classification_service_url
        self.rag = settings.rag_service_url
        self.compliance_url = settings.compliance_service_url
        self.workflow = settings.workflow_service_url

    async def _post(self, base_url: str, path: str, *, json: Any | None = None, files: Any | None = None, headers: dict[str, str] | None = None):
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(f"{base_url}{path}", json=json, files=files, headers=headers)
            except httpx.HTTPError as exc:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Service unavailable: {base_url}") from exc
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

    async def ingest(self, file_name: str, file_bytes: bytes):
        files = {"file": (file_name, file_bytes)}
        return await self._post(self.ingestion, "/ingest", files=files)

    async def classify(self, text: str):
        return await self._post(self.classification, "/classify", json={"text": text})

    async def generate(self, payload: dict[str, Any]):
        return await self._post(self.rag, "/generate", json=payload)

    async def compliance(self, payload: dict[str, Any]):
        return await self._post(self.compliance_url, "/compliance/check", json=payload)

    async def workflow_action(self, path: str, payload: dict[str, Any], token: str):
        headers = {"Authorization": f"Bearer {token}"}
        return await self._post(self.workflow, path, json=payload, headers=headers)
