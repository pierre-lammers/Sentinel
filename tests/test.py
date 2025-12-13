"""Experiment for requirement evaluation using Langfuse datasets."""

import sys
from pathlib import Path
from typing import Any

from langfuse import Langfuse

# Add project root to path so imports work from anywhere
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent import graph  # noqa: E402
from tests.evaluator import test_case_coverage_evaluator  # noqa: E402


def run_all_experiments() -> None:
    """Run experiments for entire dataset using Langfuse."""
    # Initialize Langfuse client
    langfuse = Langfuse()

    # Define task function
    async def requirement_task(*, item: Any) -> Any:
        """Task function that runs the graph for a requirement.

        Args:
            item: DatasetItemClient with input from the dataset

        Returns:
            Dictionary containing the graph output
        """
        # Get input from dataset item
        input_req_name = item.input["req_name"]

        # Run the graph
        result: dict[str, Any] = await graph.ainvoke(
            {"req_name": input_req_name},  # type: ignore[arg-type]
        )

        # Return result as dictionary
        return {
            "req_name": result.get("req_name", ""),
            "scenario_paths": result.get("scenario_paths", []),
            "scenario_results": [
                {
                    "scenario_name": sr["scenario_name"],
                    "scenario_path": sr["scenario_path"],
                    "test_cases": [
                        {
                            "id": tc["id"],
                            "description": tc["description"],
                            "present": tc["present"],
                        }
                        for tc in sr["test_cases"]
                    ],
                }
                for sr in result.get("scenario_results", [])
            ],
            "aggregated_test_cases": [
                {
                    "id": tc["id"],
                    "description": tc["description"],
                    "present": tc["present"],
                }
                for tc in result.get("aggregated_test_cases", [])
            ],
            "errors": result.get("errors", []),
        }

    # Get dataset from Langfuse
    dataset = langfuse.get_dataset("requirements-evaluation")

    # Run experiment on entire dataset with evaluator
    experiment_result = dataset.run_experiment(
        name="Full Dataset Pipeline Test",
        description="Evaluation of entire requirements-evaluation dataset for test case generation",
        task=requirement_task,  # type: ignore[arg-type]
        evaluators=[test_case_coverage_evaluator],
    )

    # Display results
    print(f"\n{'=' * 80}")
    print("Results for entire dataset")
    print(f"{'=' * 80}")
    print(experiment_result.format())


if __name__ == "__main__":
    run_all_experiments()
