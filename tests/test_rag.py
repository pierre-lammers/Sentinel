"""Experiment for RAG requirement retrieval evaluation using Langfuse datasets."""

import sys
from pathlib import Path
from typing import Any

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
from tests.rag_evaluator import requirement_retrieval_evaluator  # noqa: E402


def run_rag_experiment() -> None:
    """Run RAG retrieval experiment using Langfuse dataset."""
    # Initialize Langfuse client
    langfuse = Langfuse()

    # Define task function
    async def rag_task(*, item: Any) -> Any:
        """Task function that runs RAG retrieval for a requirement.

        Args:
            item: DatasetItemClient with input from the dataset

        Returns:
            Dictionary containing the RAG retrieval output
        """
        # Get input from dataset item
        input_req_name = item.input["req_name"]

        # Create RAG state
        rag_state = RAGState(req_name=input_req_name)

        # Create runtime with default RAG context
        rag_runtime = RAGRuntime(RAGContext())

        # Run RAG retrieval
        result = await retrieve_requirement(rag_state, rag_runtime)

        # Return result as dictionary
        return {
            "req_name": input_req_name,
            "requirement_description": result.get("requirement_description", ""),
            "errors": result.get("errors", []),
        }

    # Get dataset from Langfuse
    dataset = langfuse.get_dataset("rag-requirement-retrieval")

    # Run experiment on entire dataset with evaluator
    experiment_result = dataset.run_experiment(
        name="RAG Requirement Retrieval Test",
        description="Evaluation of RAG requirement retrieval quality",
        task=rag_task,  # type: ignore[arg-type]
        evaluators=[requirement_retrieval_evaluator],
    )

    # Display results
    print(f"\n{'=' * 80}")
    print("RAG Retrieval Experiment Results")
    print(f"{'=' * 80}")
    print(experiment_result.format())


if __name__ == "__main__":
    run_rag_experiment()
