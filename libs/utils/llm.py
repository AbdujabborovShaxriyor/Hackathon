from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Protocol

from libs.common.config import get_settings

from libs.schemas.contracts import Citation


def deterministic_embedding(text: str, dimension: int = 1536) -> list[float]:
    values = [0.0] * dimension
    if not text:
        return values
    tokens = text.lower().split()
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for i in range(0, len(digest), 2):
            idx = int.from_bytes(digest[i : i + 2], "big") % dimension
            values[idx] += 1.0
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


def build_grounded_prompt(query: str, authority: str, risk_score: int, context_blocks: list[dict]) -> str:
    snippets = []
    for block in context_blocks:
        snippets.append(f"[Source: {block['source_name']} #{block['chunk_index']}]\n{block['content']}")
    context_text = "\n\n".join(snippets) if snippets else "No retrieved context available."
    return (
        "You are a legal response drafting assistant. "
        "Answer strictly from the retrieved context. "
        "Do not invent statutes, facts, or deadlines. "
        "If the context is insufficient, say so clearly and request human review.\n\n"
        f"Authority: {authority}\nRisk score: {risk_score}\nRequest: {query}\n\n"
        f"Context:\n{context_text}"
    )


class EmbeddingClient(Protocol):
    async def embed(self, text: str) -> list[float]:
        ...


class GroundedLLM(Protocol):
    async def generate(self, *, prompt: str, query: str, citations: list[Citation]) -> str:
        ...


@dataclass(slots=True)
class FallbackEmbeddingClient:
    dimension: int = 1536

    async def embed(self, text: str) -> list[float]:
        return deterministic_embedding(text, self.dimension)


@dataclass(slots=True)
class FallbackGroundedLLM:
    async def generate(self, *, prompt: str, query: str, citations: list[Citation]) -> str:
        citation_lines = "\n".join(
            f"- {item.source_name} #{item.chunk_index}: {item.excerpt[:240]}" for item in citations
        )
        if not citation_lines:
            citation_lines = "- No retrieved citations were available."
        summary = query.strip().splitlines()[0][:240]
        return (
            "Background:\n"
            f"Respectfully, this response addresses: {summary}.\n\n"
            "Analysis:\n"
            "Based on the documents reviewed, the requested information is summarized without prejudice and remains subject to verification.\n"
            "The draft is intentionally limited to retrieved context and does not introduce unsupported facts.\n\n"
            "Conclusion:\n"
            "Please review the citations below and confirm any deadline obligations before dispatch.\n\n"
            f"Citations:\n{citation_lines}\n"
        )


@dataclass(slots=True)
class OpenAIEmbeddingClient:
    model: str = "text-embedding-3-small"

    async def embed(self, text: str) -> list[float]:
        settings = get_settings()
        if not settings.openai_api_key:
            return deterministic_embedding(text, settings.embedding_dimension)
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        response = await client.embeddings.create(model=self.model, input=text)
        return list(response.data[0].embedding)


@dataclass(slots=True)
class DeterministicEmbeddingClient:
    dimension: int = 1536

    async def embed(self, text: str) -> list[float]:
        return deterministic_embedding(text, self.dimension)


@dataclass(slots=True)
class OpenAIGroundedLLM:
    model: str = "gpt-4.1-mini"

    async def generate(self, *, prompt: str, query: str, citations: list[Citation]) -> str:
        settings = get_settings()
        if not settings.openai_api_key:
            return await FallbackGroundedLLM().generate(prompt=prompt, query=query, citations=citations)
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        response = await client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": "You draft legal responses grounded only in the supplied context.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return response.output_text or await FallbackGroundedLLM().generate(
            prompt=prompt, query=query, citations=citations
        )


@dataclass(slots=True)
class GeminiGroundedLLM:
    model: str = "gemini-1.5-pro"

    async def generate(self, *, prompt: str, query: str, citations: list[Citation]) -> str:
        settings = get_settings()
        if not settings.gemini_api_key and not settings.gemini_project_id:
            return await FallbackGroundedLLM().generate(prompt=prompt, query=query, citations=citations)
        import asyncio

        def _run() -> str:
            if settings.gemini_project_id:
                import vertexai
                from vertexai.generative_models import GenerativeModel

                vertexai.init(project=settings.gemini_project_id, location=settings.gemini_location)
                model = GenerativeModel(self.model)
                response = model.generate_content(prompt)
                return getattr(response, "text", "") or ""

            import google.generativeai as genai

            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(prompt)
            return getattr(response, "text", "") or ""

        text = await asyncio.to_thread(_run)
        return text or await FallbackGroundedLLM().generate(prompt=prompt, query=query, citations=citations)


def get_embedding_client():
    settings = get_settings()
    provider = settings.embedding_provider.lower()
    if provider == "openai" and settings.openai_api_key:
        return OpenAIEmbeddingClient()
    return DeterministicEmbeddingClient(dimension=settings.embedding_dimension)


def get_grounded_llm():
    settings = get_settings()
    provider = settings.llm_provider.lower()
    if provider == "openrouter" and settings.openai_api_key:
        return OpenAIGroundedLLM(model=settings.openai_model)
    if provider in {"vertex", "gemini"} and settings.gemini_project_id:
        return GeminiGroundedLLM(model=settings.gemini_model)
    return FallbackGroundedLLM()
