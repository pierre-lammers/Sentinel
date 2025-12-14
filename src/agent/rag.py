"""RAG retrieval module for requirement extraction."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from langgraph.runtime import Runtime
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
    errors: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Initialize mutable defaults."""
        if self.errors is None:
            self.errors = []


@dataclass
class RAGContext:
    """Runtime configuration for RAG retrieval."""

    llm_model: str = "codestral-2501"
    rag_top_k: int = 2
    temperature: float = 0.0


async def retrieve_requirement(
    state: RAGState, runtime: Runtime[RAGContext]
) -> dict[str, Any]:
    """Retrieve requirement description via RAG and filter with LLM.

    Args:
        state: Current RAG state containing req_name
        runtime: Runtime context with RAG configuration

    Returns:
        Dictionary with requirement_description or errors
    """
    try:
        context = runtime.context or RAGContext()

        # Perform vector store search in a separate thread to avoid blocking
        def _search_vector_store() -> list[Any]:
            return get_vector_store().similarity_search(
                f"Requirement {state.req_name}", k=context.rag_top_k
            )

        docs = await asyncio.to_thread(_search_vector_store)
        if not docs:
            return {
                "errors": [*state.errors, f"No document found for {state.req_name}"]
            }

        # Combine retrieved chunks
        combined_chunks = "\n\n---\n\n".join(
            [f"Chunk {i + 1}:\n{doc.page_content}" for i, doc in enumerate(docs)]
        )

        # Use LLM to filter and extract only the relevant requirement
        client = get_mistral_client()
        response = await client.chat.parse_async(
            model=context.llm_model,
            messages=[
                SystemMessage(
                    content="""You are a requirement extraction expert.
Extract ONLY the complete text of the specified requirement from the provided chunks.

Remove any surrounding text, headers, or unrelated content.
Return only the requirement description itself.

If the requirement is not found in the chunks, return an empty string."""
                ),
                UserMessage(
                    content=f"""Requirement ID: {state.req_name}

Retrieved chunks:
{combined_chunks}

Extract the complete text for requirement {state.req_name}."""
                ),
            ],
            temperature=context.temperature,
            response_format=FilteredRequirement,
        )

        if not response.choices or not response.choices[0].message:
            raise ValueError("No response from Mistral")

        parsed = response.choices[0].message.parsed
        if not parsed or not parsed.requirement_text:
            return {
                "errors": [
                    *state.errors,
                    f"Could not extract requirement {state.req_name} from chunks",
                ]
            }

        return {"requirement_description": parsed.requirement_text}
    except Exception as e:
        return {"errors": [*state.errors, f"RAG error: {e}"]}
