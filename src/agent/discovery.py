"""Project structure discovery for test coverage analysis."""

from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_mistralai import ChatMistralAI

from agent.utils import DATASET_PATH


@tool
def list_dataset_structure() -> dict[str, Any]:
    """List the directory structure of the dataset folder.

    Returns:
        Dictionary with folder structure and file patterns
    """
    if not DATASET_PATH.exists():
        return {"error": f"Dataset path {DATASET_PATH} does not exist"}

    structure: dict[str, Any] = {
        "root": str(DATASET_PATH),
        "folders": [],
    }

    for item in DATASET_PATH.iterdir():
        if item.is_dir():
            files = [f.name for f in item.rglob("*") if f.is_file()][:20]
            subdirs = [d.name for d in item.iterdir() if d.is_dir()]
            structure["folders"].append(
                {
                    "name": item.name,
                    "files": files,
                    "subdirs": subdirs,
                }
            )

    return structure


@tool
def analyze_naming_patterns(folder_name: str) -> dict[str, Any]:
    """Analyze file naming patterns in a specific folder.

    Args:
        folder_name: Name of the folder to analyze

    Returns:
        Dictionary with detected patterns
    """
    folder_path = DATASET_PATH / folder_name
    if not folder_path.exists():
        return {"error": f"Folder {folder_name} not found"}

    patterns: dict[str, Any] = {
        "folder_name": folder_name,
        "file_types": {},
        "sample_names": [],
    }

    files = list(folder_path.rglob("*"))
    for f in files[:50]:  # Limit to 50 files
        if f.is_file():
            ext = f.suffix
            patterns["file_types"][ext] = patterns["file_types"].get(ext, 0) + 1
            if len(patterns["sample_names"]) < 10:
                patterns["sample_names"].append(f.name)

    return patterns


DISCOVERY_TOOLS = [list_dataset_structure, analyze_naming_patterns]


def create_discovery_agent(model: str = "codestral-2501") -> Any:
    """Create an agent for discovering project structure."""
    llm = ChatMistralAI(model_name=model, temperature=0.0)
    return create_agent(
        model=llm,
        tools=DISCOVERY_TOOLS,
        system_prompt="You analyze project structures to find test files.",
    )


async def discover_project_structure(requirement_id: str) -> dict[str, Any]:
    """Discover how tests are organized for a given requirement.

    Args:
        requirement_id: The requirement ID to find tests for

    Returns:
        Strategy for finding test files
    """
    agent = create_discovery_agent()

    task = f"""Analyze the dataset structure to find tests for: {requirement_id}

Use the tools to:
1. List the dataset structure
2. Identify folders that might contain tests for {requirement_id}
3. Analyze naming patterns in those folders

Return a clear strategy including folder and file patterns."""

    result = await agent.ainvoke({"messages": [HumanMessage(content=task)]})
    final_answer = result["messages"][-1].content

    return {
        "discovery_output": final_answer,
        "requirement_id": requirement_id,
    }
