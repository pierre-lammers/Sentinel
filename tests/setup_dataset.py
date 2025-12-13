"""Script to create Langfuse datasets for requirement evaluation."""

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langfuse import Langfuse

# Load environment variables from .env file
load_dotenv()


def add_requirement_item(
    langfuse: Langfuse,
    dataset_name: str,
    req_name: str,
    expected_output: dict[str, Any],
) -> None:
    """Add a dataset item for a specific requirement.

    Args:
        langfuse: Initialized Langfuse client
        dataset_name: The name of the dataset to add the item to
        req_name: The requirement name (e.g., "ARR-044")
        expected_output: Dictionary containing the expected output for this requirement
    """
    # Create dataset item
    langfuse.create_dataset_item(
        dataset_name=dataset_name,
        input={"req_name": expected_output["req_name"]},
        expected_output=expected_output,
        metadata={
            "description": f"Complete test case coverage for {req_name}",
            "scenarios": expected_output.get("scenario_paths", []),
            "scenarios_count": len(expected_output.get("scenario_paths", [])),
            "test_cases_count": len(expected_output.get("aggregated_test_cases", [])),
        },
    )
    print(f"Added dataset item for {expected_output['req_name']}")


def create_all_datasets() -> None:
    """Create a single Langfuse dataset with items for all requirements."""
    # Initialize Langfuse client with environment variables
    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST"),
    )

    # Path to expected outputs directory
    expected_outputs_dir = Path(__file__).parent / "expected_outputs"

    # Check if directory exists
    if not expected_outputs_dir.exists():
        print(f"Error: Directory {expected_outputs_dir} does not exist")
        return

    # Find all JSON files in expected_outputs directory
    json_files = list(expected_outputs_dir.glob("*.json"))

    if not json_files:
        print(f"No JSON files found in {expected_outputs_dir}")
        return

    print(f"Found {len(json_files)} requirement(s) to process")

    # Create single dataset for all requirements
    dataset_name = "requirements-evaluation"
    try:
        langfuse.create_dataset(
            name=dataset_name,
            description="Evaluation dataset for all requirements",
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

        # Add dataset item for this requirement
        add_requirement_item(langfuse, dataset_name, req_name, expected_output)

    # Flush to ensure all data is sent
    langfuse.flush()
    print(f"\n{'=' * 80}")
    print("All dataset items added successfully!")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    create_all_datasets()
