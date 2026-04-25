from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF
from docx import Document
from PIL import Image
import pytesseract


@dataclass(slots=True)
class ExtractedText:
    text: str
    page_count: int
    method: str


def _extract_pdf_text(file_bytes: bytes) -> ExtractedText:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text_parts: list[str] = []
    for page in doc:
        text = page.get_text("text").strip()
        if text:
            text_parts.append(text)
    native_text = "\n\n".join(text_parts).strip()
    if native_text:
        return ExtractedText(text=native_text, page_count=doc.page_count, method="pdf-native")

    ocr_parts: list[str] = []
    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        image = Image.open(io.BytesIO(pix.tobytes("png")))
        ocr_text = pytesseract.image_to_string(image).strip()
        if ocr_text:
            ocr_parts.append(ocr_text)
    return ExtractedText(text="\n\n".join(ocr_parts).strip(), page_count=doc.page_count, method="pdf-ocr")


def _extract_docx_text(file_bytes: bytes) -> ExtractedText:
    document = Document(io.BytesIO(file_bytes))
    text = "\n".join(p.text for p in document.paragraphs if p.text.strip()).strip()
    return ExtractedText(text=text, page_count=1, method="docx")


def _extract_email_text(file_bytes: bytes) -> ExtractedText:
    text = file_bytes.decode("utf-8", errors="ignore").strip()
    return ExtractedText(text=text, page_count=1, method="email")


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> ExtractedText:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf_text(file_bytes)
    if suffix in {".docx", ".doc"}:
        return _extract_docx_text(file_bytes)
    if suffix in {".eml", ".txt"}:
        return _extract_email_text(file_bytes)
    return ExtractedText(text=file_bytes.decode("utf-8", errors="ignore").strip(), page_count=1, method="raw")


async def extract_text_from_upload(upload_file) -> ExtractedText:
    file_bytes = await upload_file.read()
    return extract_text_from_bytes(file_bytes, upload_file.filename or "upload.bin")

