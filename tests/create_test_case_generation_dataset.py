"""Create Langfuse dataset for test case generation evaluation.

This script populates the Langfuse dataset with test cases from expected outputs.
"""

import asyncio
import json
import sys
from pathlib import Path

from langfuse import Langfuse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent.regex_extract import RegexState, retrieve_requirement_regex  # noqa: E402


async def create_dataset() -> None:
    """Create Langfuse dataset from expected outputs."""
    langfuse = Langfuse()

    # Create or get the dataset
    dataset_name = "test-case-generation"
    print(f"Creating dataset: {dataset_name}")

    # Create the dataset first
    try:
        langfuse.create_dataset(
            name=dataset_name,
            description="Dataset for evaluating test case generation from requirements",
        )
        print(f"Dataset '{dataset_name}' created successfully")
    except Exception as e:
        print(f"Dataset might already exist or creation failed: {e}")

    # Load expected outputs
    expected_outputs_dir = Path(__file__).parent / "expected_outputs"
    expected_files = list(expected_outputs_dir.glob("*.json"))

    if not expected_files:
        print(f"No expected output files found in {expected_outputs_dir}")
        return

    print(f"Found {len(expected_files)} expected output file(s)")

    # Process each expected output file
    for expected_file in expected_files:
        print(f"\nProcessing: {expected_file.name}")

        with expected_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        req_name = data.get("req_name", "")
        aggregated_test_cases = data.get("aggregated_test_cases", [])

        if not req_name:
            print(f"  Skipping {expected_file.name}: no req_name found")
            continue

        if not aggregated_test_cases:
            print(f"  Skipping {expected_file.name}: no aggregated_test_cases found")
            continue

        # Retrieve the requirement description using regex extraction
        print(f"  Retrieving requirement description for {req_name}...")
        regex_state = RegexState(req_name=req_name, errors=[])
        result = await retrieve_requirement_regex(regex_state)

        requirement_description = result.get("requirement_description", "")
        if not requirement_description:
            print(
                f"  Warning: Could not retrieve requirement description for {req_name}"
            )
            requirement_description = f"[Failed to retrieve description for {req_name}]"

        # Create dataset item
        langfuse.create_dataset_item(
            dataset_name=dataset_name,
            input={
                "req_name": req_name,
                "requirement_description": requirement_description,
            },
            expected_output={
                "aggregated_test_cases": aggregated_test_cases,
            },
        )

        print(
            f"  Added item: {req_name} with {len(aggregated_test_cases)} expected test cases"
        )

    print(f"\n{'=' * 80}")
    print(f"Dataset '{dataset_name}' created successfully!")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    asyncio.run(create_dataset())
