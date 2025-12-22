"""Deep agent for exploring test dataset and finding files by requirement ID."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, cast

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend  # type: ignore[import-untyped]
from dotenv import load_dotenv
from langchain.agents.structured_output import ToolStrategy
from pydantic import BaseModel, Field, field_validator

from agent.llm_factory import get_llm

DATASET_PATH = Path(__file__).parent.parent.parent / "dataset"

load_dotenv(Path(__file__).parent.parent.parent / ".env")


class RequirementFiles(BaseModel):
    """Structured output model for requirement file paths."""

    files: List[str] = Field(
        description="List of absolute file paths associated with the requirement ID"
    )

    @field_validator("files", mode="before")
    @classmethod
    def validate_paths(cls, v: Any) -> List[str]:
        """Validate that each item is a valid path string."""
        if not isinstance(v, list):
            raise ValueError("files must be a list")

        validated_paths = []
        for item in v:
            if not isinstance(item, str):
                raise ValueError(f"Each file path must be a string, got {type(item)}")
            # Validate that it's a valid path format
            try:
                Path(item)
                validated_paths.append(item)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid path format: {item}") from e

        return validated_paths


class ScenarioDatasetAnalysis(BaseModel):
    """Structured output model for scenario and dataset classification."""

    scenarios: List[str] = Field(
        description="List of absolute file paths identified as scenario test files"
    )
    datasets: List[str] = Field(
        description="List of absolute file paths identified as dataset files"
    )

    @field_validator("scenarios", "datasets", mode="before")
    @classmethod
    def validate_paths(cls, v: Any) -> List[str]:
        """Validate that each item is a valid path string."""
        if not isinstance(v, list):
            raise ValueError("Field must be a list")

        validated_paths = []
        for item in v:
            if not isinstance(item, str):
                raise ValueError(f"Each file path must be a string, got {type(item)}")
            try:
                Path(item)
                validated_paths.append(item)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid path format: {item}") from e

        return validated_paths


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
5. Return a structured response with all file paths in a list format.

Be thorough: ensure you include all files under the dataset folder, and do not mention or include any files outside of it.
"""

ANALYZER_SYSTEM_PROMPT = """
You are a test scenario and dataset classifier agent. Your mission is to analyze provided file paths and classify each file as either a scenario test file or a dataset file.

You have the following tools at your disposal:
- `read_file`: to read and analyze the content of files

When given a list of file paths:
1. For each file, use the `read_file` tool to examine its content.
2. Analyze the file content to determine if it is:
   - A **scenario test file**: Contains test scenarios, test cases, requirements, acceptance criteria, or similar testing-related content
   - A **dataset file**: Contains data, raw information, or resources used for testing (JSON, CSV, Excel, databases, etc.)
3. Classify each file into the appropriate category based on its content analysis.
4. Return a structured response with two lists:
   - `scenarios`: All files identified as scenario test files
   - `datasets`: All files identified as dataset files

Be thorough: examine the content of each file carefully to make an accurate classification.
"""


def create_dataset_explorer_agent(
    model: str = "codestral-2501",
    temperature: float = 0.0,
) -> Any:
    """Create a deep agent for exploring the test dataset with structured output."""
    llm = get_llm(model=model, temperature=temperature)

    agent = create_deep_agent(
        model=llm,
        backend=FilesystemBackend(root_dir=str(DATASET_PATH), virtual_mode=False),
        system_prompt=SYSTEM_PROMPT,
        response_format=ToolStrategy(RequirementFiles),
    )

    return agent


async def find_requirement_files(
    requirement_id: str, model: str = "codestral-2501"
) -> RequirementFiles:
    """Find all files associated with a requirement ID using the deep agent.

    Returns:
        RequirementFiles object containing file paths associated with the requirement ID.
    """
    agent = create_dataset_explorer_agent(model=model)

    prompt = f"Find all files associated with requirement ID: {requirement_id}"

    result = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})

    # Extract the structured output from the final message
    return cast(RequirementFiles, result["structured_response"])


def create_file_analyzer_agent(
    model: str = "codestral-2501",
    temperature: float = 0.0,
) -> Any:
    """Create a deep agent for analyzing and classifying files as scenarios or datasets."""
    llm = get_llm(model=model, temperature=temperature)

    agent = create_deep_agent(
        model=llm,
        backend=FilesystemBackend(root_dir=str(DATASET_PATH), virtual_mode=False),
        system_prompt=ANALYZER_SYSTEM_PROMPT,
        response_format=ToolStrategy(ScenarioDatasetAnalysis),
    )

    return agent


async def analyze_requirement_files(
    file_paths: List[str], model: str = "codestral-2501"
) -> ScenarioDatasetAnalysis:
    """Analyze files to classify them as scenario test files or dataset files.

    Args:
        file_paths: List of file paths to analyze.
        model: Model name to use for analysis.

    Returns:
        ScenarioDatasetAnalysis object containing classified file paths.
    """
    agent = create_file_analyzer_agent(model=model)

    files_list = "\n".join(file_paths)
    prompt = f"""Analyze the following files and classify each as either a scenario test file or a dataset file:

{files_list}

For each file, read its content and determine if it is a scenario test file (containing test cases, requirements, acceptance criteria, etc.) or a dataset file (containing data, resources, etc.)."""

    result = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})

    # Extract the structured output from the final message
    return cast(ScenarioDatasetAnalysis, result["structured_response"])


async def retrieve_scenario_and_dataset_files(
    requirement_id: str, model: str = "codestral-2501"
) -> ScenarioDatasetAnalysis:
    """Retrieve and classify scenario and dataset files for a given requirement ID.

    Args:
        requirement_id: The requirement ID to search for.
        model: Model name to use for analysis.

    """
    all_files = await find_requirement_files(requirement_id, model=model)
    classified_files = await analyze_requirement_files(all_files.files, model=model)
    return classified_files
