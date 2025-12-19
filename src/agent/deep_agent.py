"""Deep agent for exploring test dataset and finding files by requirement ID."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, List

from deepagents import create_deep_agent  # type: ignore[import-untyped]
from deepagents.backends import FilesystemBackend  # type: ignore[import-untyped]
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from pydantic import SecretStr

DATASET_PATH = Path(__file__).parent.parent.parent / "dataset"

load_dotenv(Path(__file__).parent.parent.parent / ".env")

SYSTEM_PROMPT = f"""
You are a test codebase explorer agent. Your mission is to find all scenario tests files associated with a given requirement ID provided in the human message. 

You have the following tools at your disposal:
- `ls`: to list files and directories
- `grep`: to search for patterns within files and directories

You are only allowed to explore files and folders **inside the dataset folder**, which is located at {DATASET_PATH}. Do not include any files outside this folder.

When given a requirement ID:
1. Explore the dataset folder using `ls` to find the folder corresponding to this requirement ID.
2. List all subdirectories and files inside the requirement folder, without assuming any specific structure or naming conventions.
3. Use `grep` if needed to identify relevant files or patterns.
4. Collect the full paths of all files found within the dataset folder.
5. Return a comprehensive and exhaustive list of all file paths associated with the requirement ID.

Be thorough: ensure you include all files under the dataset folder, and do not mention or include any files outside of it.
"""


def get_mistral_llm(
    model: str = "codestral-2501", temperature: float = 0.0
) -> ChatMistralAI:
    """Get a ChatMistralAI instance configured with API key."""
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY not set")
    return ChatMistralAI(
        model_name=model, temperature=temperature, api_key=SecretStr(api_key)
    )


def create_dataset_explorer_agent(
    model: str = "codestral-2501",
    temperature: float = 0.0,
) -> Any:
    """Create a deep agent for exploring the test dataset."""
    llm = get_mistral_llm(model=model, temperature=temperature)

    agent = create_deep_agent(
        model=llm,
        backend=FilesystemBackend(root_dir=str(DATASET_PATH), virtual_mode=False),
        system_prompt=SYSTEM_PROMPT,
    )

    return agent


async def find_requirement_files(
    requirement_id: str,
    model: str = "codestral-2501",
    verbose: bool = False,
) -> List[str]:
    """Find all files associated with a requirement ID using the deep agent."""
    agent = create_dataset_explorer_agent(model=model)

    prompt = f"Find all files associated with requirement ID: {requirement_id}"

    result = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})

    # Extract the agent's final message
    final_message = result["messages"][-1].content

    if verbose:
        import logging

        logger = logging.getLogger(__name__)
        logger.info("=== Agent Response ===")
        logger.info(final_message)
        logger.info("=====================")

    # Try to parse file paths from agent response (one per line)
    file_paths = []
    for line in final_message.splitlines():
        line = line.strip()
        if line:
            # Remove markdown list markers (-, *, +) if present
            if line.startswith(("- ", "* ", "+ ")):
                line = line[2:].strip()
            file_paths.append(line)

    return file_paths


# Example usage
if __name__ == "__main__":

    async def main() -> None:
        """Demonstrate deep agent usage."""
        req_id = "STCA-041"  # Example requirement ID
        files = await find_requirement_files(req_id, verbose=True)
        print("\nCollected file paths:")  # noqa: T201
        for f in files:
            print(f)  # noqa: T201

    asyncio.run(main())
