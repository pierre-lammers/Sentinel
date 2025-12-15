"""Regex-based requirement extraction from SRS PDF."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import pymupdf  # type: ignore[import-untyped]

# Path to SRS document
SRS_PATH = Path(__file__).parent.parent.parent / "dataset" / "SRS.pdf"

# Regex pattern for requirement IDs (e.g., SKYRADAR-ARR-044, SKYRADAR-CPDLC-047)
REQ_PATTERN = re.compile(r"\b(SKYRADAR-[A-Z]+-\d+)\b")


@lru_cache(maxsize=1)
def _load_srs_text() -> str:
    """Load and cache full SRS text from PDF."""
    with pymupdf.open(SRS_PATH) as doc:
        return "\n".join(page.get_text(sort=True) for page in doc)


def extract_requirement(req_id: str) -> str | None:
    """Extract requirement text from SRS using regex.

    Args:
        req_id: Requirement ID (e.g., "SKYRADAR-ARR-044")

    Returns:
        Requirement text or None if not found
    """
    text = _load_srs_text()

    # Find all requirement positions
    matches = list(REQ_PATTERN.finditer(text))
    if not matches:
        return None

    # Find target requirement
    target_match = None
    next_pos = len(text)

    for i, m in enumerate(matches):
        if m.group(1) == req_id:
            target_match = m
            # Find next requirement position
            if i + 1 < len(matches):
                next_pos = matches[i + 1].start()
            break

    if not target_match:
        return None

    # Extract text between current and next requirement
    raw_text = text[target_match.start() : next_pos]

    # Clean up: remove excessive whitespace while preserving structure
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    return "\n".join(lines)


@dataclass
class RegexState:
    """State for regex extraction."""

    req_name: str = ""
    requirement_description: str = ""
    errors: list[str] = field(default_factory=list)


async def retrieve_requirement_regex(state: RegexState) -> dict[str, Any]:
    """Retrieve requirement using regex extraction.

    Args:
        state: Current state with req_name

    Returns:
        Dict with requirement_description or errors
    """
    try:
        result = extract_requirement(state.req_name)
        if result is None:
            return {
                "errors": [*state.errors, f"Requirement {state.req_name} not found"]
            }
        return {"requirement_description": result}
    except Exception as e:
        return {"errors": [*state.errors, f"Regex extraction error: {e}"]}
