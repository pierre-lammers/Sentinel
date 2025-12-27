"""Test script for the deep agent."""

import asyncio

from dotenv import load_dotenv

from agent.deep_agent_file_explorer import (
    analyze_requirement_files,
    find_requirement_files,
)

# Load environment variables
load_dotenv()


async def main() -> None:
    """Test the deep agent with a sample requirement ID."""
    requirement_id = "STCA-041"

    print("============ALL FILES==============")

    all_files = await find_requirement_files(requirement_id)
    for f in all_files.files:
        print(f"- {f}")

    filtered_files = await analyze_requirement_files(all_files.files)

    print("============SCENARIOS==============")
    for f in filtered_files.scenarios:
        print(f"- Scenario: {f}")

    print("============DATASETS==============")
    for f in filtered_files.datasets:
        print(f"- Dataset: {f}")


if __name__ == "__main__":
    asyncio.run(main())
