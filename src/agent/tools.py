"""Tools for the test coverage analysis agent."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from agent.utils import DATASET_PATH


@tool
def read_test_file(file_path: str) -> str:
    """Read and return the content of a test file.

    Args:
        file_path: Absolute or relative path to the test file

    Returns:
        The file content as a string
    """
    try:
        path = Path(file_path)
        if not path.is_absolute():
            path = DATASET_PATH / file_path
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def search_in_file(query: str, file_path: str) -> list[str]:
    """Search for a pattern in a test file using regex.

    Args:
        query: Regex pattern to search for
        file_path: Path to the file to search in

    Returns:
        List of matching lines with line numbers
    """
    try:
        path = Path(file_path)
        if not path.is_absolute():
            path = DATASET_PATH / file_path
        content = path.read_text(encoding="utf-8")

        matches = []
        for i, line in enumerate(content.split("\n"), 1):
            if re.search(query, line, re.IGNORECASE):
                matches.append(f"Line {i}: {line.strip()}")

        return matches if matches else ["No matches found"]
    except Exception as e:
        return [f"Error searching: {e}"]


@tool
def parse_xml_structure(file_path: str) -> dict[str, Any]:
    """Parse XML test file and return structured information.

    Args:
        file_path: Path to the XML file

    Returns:
        Dictionary with XML structure info (tags, attributes, hierarchy)
    """
    try:
        path = Path(file_path)
        if not path.is_absolute():
            path = DATASET_PATH / file_path
        content = path.read_text(encoding="utf-8")
        root = ET.fromstring(content)

        def parse_element(elem: ET.Element, depth: int = 0) -> dict[str, Any]:
            result: dict[str, Any] = {
                "tag": elem.tag,
                "attributes": dict(elem.attrib),
            }
            if elem.text and elem.text.strip():
                result["text"] = elem.text.strip()[:100]
            if depth < 3:  # Limit depth to avoid huge output
                children = [parse_element(child, depth + 1) for child in elem]
                if children:
                    result["children"] = children[:10]  # Limit children
            return result

        return {
            "root_tag": root.tag,
            "structure": parse_element(root),
        }
    except Exception as e:
        return {"error": f"Error parsing XML: {e}"}


@tool
def list_related_files(scenario_path: str) -> list[str]:
    """Find files related to a test scenario (same directory, config files).

    Args:
        scenario_path: Path to the scenario file

    Returns:
        List of related file paths
    """
    try:
        path = Path(scenario_path)
        if not path.is_absolute():
            path = DATASET_PATH / scenario_path

        related = []

        # Files in same directory
        if path.parent.exists():
            for f in path.parent.iterdir():
                if f.is_file() and f != path:
                    try:
                        rel = f.relative_to(DATASET_PATH)
                        related.append(str(rel))
                    except ValueError:
                        related.append(str(f))

        return related if related else ["No related files found"]
    except Exception as e:
        return [f"Error listing files: {e}"]


@tool
def get_file_summary(file_path: str, max_lines: int = 50) -> str:
    """Get a summary of a file (first N lines + stats).

    Args:
        file_path: Path to the file
        max_lines: Maximum number of lines to include

    Returns:
        File summary with stats and preview
    """
    try:
        path = Path(file_path)
        if not path.is_absolute():
            path = DATASET_PATH / file_path
        content = path.read_text(encoding="utf-8")

        lines = content.split("\n")
        total_lines = len(lines)
        preview = "\n".join(lines[:max_lines])
        truncated = "...(truncated)" if total_lines > max_lines else ""

        return (
            f"File: {file_path}\nLines: {total_lines}\nPreview:\n{preview}{truncated}"
        )
    except Exception as e:
        return f"Error getting summary: {e}"


# Export all tools
COVERAGE_TOOLS = [
    read_test_file,
    search_in_file,
    parse_xml_structure,
    list_related_files,
    get_file_summary,
]
