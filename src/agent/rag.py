"""RAG retrieval module for requirement extraction."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from mistralai.models import SystemMessage, UserMessage
from pydantic import BaseModel, Field

from agent.utils import get_mistral_client, get_vector_store


class FilteredRequirement(BaseModel):
    """Filtered requirement extracted from RAG chunks."""

    requirement_text: str = Field(
        description="The complete requirement text, filtered from surrounding context"
    )


@dataclass
class RAGState:
    """State for RAG retrieval."""

    req_name: str = ""
    requirement_description: str = ""
    errors: list[str] = field(default_factory=list)


@dataclass
class RAGContext:
    """Runtime configuration for RAG retrieval."""

    llm_model: str = "codestral-2501"
    rag_top_k: int = 4
    temperature: float = 0.0
    use_mmr: bool = True
    mmr_lambda: float = 0.8


class RAGRuntime:
    """Simple runtime wrapper for RAG context."""

    def __init__(self, ctx: RAGContext | None = None) -> None:
        """Initialize runtime with optional context."""
        self.context = ctx or RAGContext()


async def retrieve_requirement(state: RAGState, runtime: RAGRuntime) -> dict[str, Any]:
    """Retrieve requirement description via RAG and filter with LLM."""
    try:
        ctx = runtime.context

        # Search vector store with enriched query
        def _search() -> list[Any]:
            vs = get_vector_store()
            query = (
                f"Requirement {state.req_name}: "
                f"Find the complete requirement specification for {state.req_name} "
                f"including description, constraints, and details"
            )
            if ctx.use_mmr:
                return vs.max_marginal_relevance_search(
                    query,
                    k=ctx.rag_top_k,
                    fetch_k=ctx.rag_top_k * 3,
                    lambda_mult=ctx.mmr_lambda,
                )
            return vs.similarity_search(query, k=ctx.rag_top_k)

        docs = await asyncio.to_thread(_search)
        if not docs:
            return {
                "errors": [*state.errors, f"No document found for {state.req_name}"]
            }

        # Combine chunks with metadata
        chunks = "\n\n---\n\n".join(
            f"Chunk {i + 1} (Page {d.metadata.get('page', 'N/A')}, "
            f"Index {d.metadata.get('chunk_index', 'N/A')}):\n{d.page_content}"
            for i, d in enumerate(docs)
        )

        # Extract requirement with LLM
        response = await get_mistral_client().chat.parse_async(
            model=ctx.llm_model,
            messages=[
                SystemMessage(
                    content="""You are a requirement extraction expert for SRS documents.

Extract the COMPLETE text of the specified requirement from the chunks.

Instructions:
1. Search through all provided chunks for the requirement ID
2. Extract the FULL requirement text including:
   - Main description
   - Sub-requirements or constraints
   - Related specifications
3. Remove headers, footers, page numbers, unrelated requirements
4. Preserve all technical details and formatting
5. If split across chunks, combine coherently

Return empty string if requirement not found."""
                ),
                UserMessage(
                    content=f"Requirement ID: {state.req_name}\n\nChunks:\n{chunks}\n\n"
                    f"Extract the complete text for requirement {state.req_name}."
                ),
            ],
            temperature=ctx.temperature,
            response_format=FilteredRequirement,
        )

        if not response.choices or not response.choices[0].message:
            raise ValueError("No response from Mistral")

        parsed = response.choices[0].message.parsed
        if not parsed or not parsed.requirement_text:
            return {"errors": [*state.errors, f"Could not extract {state.req_name}"]}

        return {"requirement_description": parsed.requirement_text}
    except Exception as e:
        return {"errors": [*state.errors, f"RAG error: {e}"]}
