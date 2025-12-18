"""Experiment for requirement retrieval evaluation using Langfuse datasets.

Usage:
    python tests/test_rag.py rag    # Use semantic RAG retrieval
    python tests/test_rag.py regex  # Use regex-based extraction
"""

import sys
from pathlib import Path
from typing import Any, Literal

from langfuse import Langfuse

# Add project root to path so imports work from anywhere
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent.rag import (  # noqa: E402
    RAGContext,
    RAGRuntime,
    RAGState,
    retrieve_requirement,
)
from agent.regex_extract import (  # noqa: E402
    RegexState,
    retrieve_requirement_regex,
)
from tests.evaluators import requirement_retrieval_evaluator  # noqa: E402


def run_experiment(method: Literal["rag", "regex"] = "rag") -> None:
    """Run requirement retrieval experiment using Langfuse dataset.

    Args:
        method: Retrieval method - "rag" for semantic search, "regex" for pattern matching
    """
    langfuse = Langfuse()

    async def rag_task(*, item: Any) -> Any:
        """RAG retrieval task."""
        req_name = item.input["req_name"]
        state = RAGState(req_name=req_name)
        runtime = RAGRuntime(RAGContext())
        result = await retrieve_requirement(state, runtime)
        return {
            "req_name": req_name,
            "requirement_description": result.get("requirement_description", ""),
            "errors": result.get("errors", []),
        }

    async def regex_task(*, item: Any) -> Any:
        """Regex extraction task."""
        req_name = item.input["req_name"]
        state = RegexState(req_name=req_name)
        result = await retrieve_requirement_regex(state)
        return {
            "req_name": req_name,
            "requirement_description": result.get("requirement_description", ""),
            "errors": result.get("errors", []),
        }

    task = regex_task if method == "regex" else rag_task
    name = f"{'Regex' if method == 'regex' else 'RAG'} Requirement Retrieval"

    dataset = langfuse.get_dataset("rag-requirement-retrieval")
    result = dataset.run_experiment(
        name=name,
        description=f"Evaluation of {method.upper()} requirement retrieval",
        task=task,  # type: ignore[arg-type]
        evaluators=[requirement_retrieval_evaluator],
    )

    print(f"\n{'=' * 80}")
    print(f"{name} Results")
    print(f"{'=' * 80}")
    print(result.format())


if __name__ == "__main__":
    method: Literal["rag", "regex"] = "rag"
    if len(sys.argv) > 1 and sys.argv[1] in ("rag", "regex"):
        method = sys.argv[1]  # type: ignore[assignment]
    run_experiment(method)
