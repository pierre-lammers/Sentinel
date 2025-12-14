"""Script to create Langfuse dataset for RAG requirement retrieval evaluation."""

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langfuse import Langfuse

# Load environment variables from .env file
load_dotenv()


def add_rag_requirement_item(
    langfuse: Langfuse,
    dataset_name: str,
    req_name: str,
    expected_output: dict[str, Any],
) -> None:
    """Add a dataset item for RAG requirement retrieval.

    Args:
        langfuse: Initialized Langfuse client
        dataset_name: The name of the dataset to add the item to
        req_name: The requirement name (e.g., "ARR-044")
        expected_output: Dictionary containing the expected requirement description
    """
    # Create dataset item
    langfuse.create_dataset_item(
        dataset_name=dataset_name,
        input={"req_name": expected_output["req_name"]},
        expected_output=expected_output,
        metadata={
            "description": f"RAG retrieval for requirement {req_name}",
            "requirement_length": len(
                expected_output.get("requirement_description", "")
            ),
        },
    )
    print(f"Added RAG dataset item for {expected_output['req_name']}")


def create_rag_dataset() -> None:
    """Create a Langfuse dataset for RAG requirement retrieval evaluation."""
    # Initialize Langfuse client with environment variables
    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST"),
    )

    # Path to RAG expected outputs directory
    rag_expected_outputs_dir = Path(__file__).parent / "rag_expected_outputs"

    # Check if directory exists
    if not rag_expected_outputs_dir.exists():
        print(f"Error: Directory {rag_expected_outputs_dir} does not exist")
        print("Creating directory...")
        rag_expected_outputs_dir.mkdir(parents=True)
        print(
            f"Please add expected output JSON files to {rag_expected_outputs_dir} "
            'with format: {"req_name": "ARR-044", "requirement_description": "..."}'
        )
        return

    # Find all JSON files in rag_expected_outputs directory
    json_files = list(rag_expected_outputs_dir.glob("*.json"))

    if not json_files:
        print(f"No JSON files found in {rag_expected_outputs_dir}")
        print(
            "Please add expected output JSON files with format: "
            '{"req_name": "ARR-044", "requirement_description": "..."}'
        )
        return

    print(f"Found {len(json_files)} requirement(s) to process for RAG dataset")

    # Create dataset for RAG evaluation
    dataset_name = "rag-requirement-retrieval"
    try:
        langfuse.create_dataset(
            name=dataset_name,
            description="Evaluation dataset for RAG requirement retrieval",
            metadata={
                "requirements_count": len(json_files),
            },
        )
        print(f"Created dataset: {dataset_name}")
    except Exception as e:
        print(f"Dataset may already exist: {e}")

    # Process each expected output file and add as dataset item
    for json_file in sorted(json_files):
        # Extract requirement name from filename (e.g., "ARR-044.json" -> "ARR-044")
        req_name = json_file.stem

        print(f"\n{'=' * 80}")
        print(f"Processing requirement: {req_name}")
        print(f"{'=' * 80}")

        # Load expected output
        with open(json_file) as f:
            expected_output = json.load(f)

        # Verify req_name matches
        if expected_output.get("req_name") != req_name:
            print(
                f"Warning: req_name in file ({expected_output.get('req_name')}) "
                f"does not match filename ({req_name})"
            )

        # Verify requirement_description exists
        if "requirement_description" not in expected_output:
            print(f"Error: Missing 'requirement_description' in {json_file}")
            continue

        # Add dataset item for this requirement
        add_rag_requirement_item(langfuse, dataset_name, req_name, expected_output)

    # Flush to ensure all data is sent
    langfuse.flush()
    print(f"\n{'=' * 80}")
    print("All RAG dataset items added successfully!")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    create_rag_dataset()
