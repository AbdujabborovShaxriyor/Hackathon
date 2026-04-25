from __future__ import annotations

from libs.schemas.contracts import IngestionResult
from libs.utils.file_handling import safe_filename, sha256_bytes
from libs.utils.text_extract import extract_text_from_bytes


async def ingest_file(filename: str, file_bytes: bytes) -> IngestionResult:
    extracted = extract_text_from_bytes(file_bytes, filename)
    return IngestionResult(
        file_name=safe_filename(filename),
        file_hash=sha256_bytes(file_bytes),
        text=extracted.text,
        page_count=extracted.page_count,
        method=extracted.method,
    )

