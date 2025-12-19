"""Test script for the deep agent."""

import asyncio

from dotenv import load_dotenv

from agent.deep_agent import find_requirement_files

# Load environment variables
load_dotenv()


async def main() -> None:
    """Test the deep agent with a sample requirement ID."""
    # Test with STCA-041
    print("Testing with requirement ID: STCA-041")  # noqa: T201
    print("-" * 80)  # noqa: T201

    try:
        files = await find_requirement_files("STCA-041", verbose=True)
        print(f"\nFound {len(files)} files:")  # noqa: T201
        for file_path in files:
            print(f"  - {file_path}")  # noqa: T201
    except Exception as e:
        print(f"Error: {e}")  # noqa: T201
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
