"""Experiment for test case generation evaluation using Langfuse datasets.

Usage:
    python tests/test_generate_test_cases.py
"""

import sys
from pathlib import Path
from typing import Any

from langfuse import Langfuse

# Add project root to path so imports work from anywhere
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent.nodes import generate_test_cases  # noqa: E402
from agent.state import Context, State  # noqa: E402
from tests.evaluators import (  # noqa: E402
    test_case_generation_evaluator,
)


class TestRuntime:
    """Simple runtime wrapper for test case generation context."""

    def __init__(self, ctx: Context | None = None) -> None:
        """Initialize runtime with context."""
        self.context = ctx or Context()


def run_experiment() -> None:
    """Run test case generation experiment using Langfuse dataset."""
    langfuse = Langfuse()

    async def generate_task(*, item: Any) -> Any:
        """Test case generation task."""
        req_name = item.input["req_name"]
        requirement_description = item.input["requirement_description"]

        # Create state with requirement info
        state: State = {
            "req_name": req_name,
            "requirement_description": requirement_description,
            "scenario_paths": [],
            "current_scenario_index": 0,
            "scenario_results": [],
            "aggregated_test_cases": [],
            "false_positives": [],
            "errors": [],
        }

        # Create runtime with default context
        runtime = TestRuntime(Context())

        # Generate test cases
        result = await generate_test_cases(state, runtime)  # type: ignore[arg-type]

        return {
            "req_name": req_name,
            "generated_test_cases": result.get("generated_test_cases", []),
            "errors": result.get("errors", []),
        }

    dataset = langfuse.get_dataset("test-case-generation")
    result = dataset.run_experiment(
        name="Test Case Generation Evaluation",
        description="Evaluation of LLM-based test case generation from requirements",
        task=generate_task,  # type: ignore[arg-type]
        evaluators=[test_case_generation_evaluator],
    )

    print(f"\n{'=' * 80}")
    print("Test Case Generation Results")
    print(f"{'=' * 80}")
    print(result.format())


if __name__ == "__main__":
    run_experiment()
