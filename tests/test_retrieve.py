"""Experiment for requirement retrieval evaluation using Langfuse datasets.

Usage:
    python tests/test_retrieve.py
"""

import sys
from pathlib import Path
from typing import Any

from langfuse import Langfuse

# Add project root to path so imports work from anywhere
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent.regex_extract import (  # noqa: E402
    RegexState,
    retrieve_requirement_regex,
)
from tests.evaluators import requirement_retrieval_evaluator  # noqa: E402


def run_experiment() -> None:
    """Run requirement retrieval experiment using Langfuse dataset."""
    langfuse = Langfuse()

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

    dataset = langfuse.get_dataset("rag-requirement-retrieval")
    result = dataset.run_experiment(
        name="Regex Requirement Retrieval",
        description="Evaluation of regex-based requirement retrieval",
        task=regex_task,  # type: ignore[arg-type]
        evaluators=[requirement_retrieval_evaluator],
    )

    print(f"\n{'=' * 80}")
    print("Regex Requirement Retrieval Results")
    print(f"{'=' * 80}")
    print(result.format())


if __name__ == "__main__":
    run_experiment()
