"""Regex-based requirement extraction from SRS PDF with persistent caching."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pymupdf  # type: ignore[import-untyped]
from diskcache import Cache

# Path to SRS document
SRS_PATH = Path(__file__).parent.parent.parent / "dataset" / "SRS.pdf"

# Cache directory
CACHE_DIR = Path(__file__).parent.parent.parent / ".cache" / "requirements"

# Regex pattern for requirement IDs (e.g., SKYRADAR-ARR-044, SKYRADAR-CPDLC-047)
REQ_PATTERN = re.compile(r"\b(SKYRADAR-[A-Z]+-\d+)\b")

# Initialize persistent cache (thread-safe and process-safe)
_cache = Cache(str(CACHE_DIR))


def _get_pdf_hash() -> str:
    """Compute SHA256 hash of SRS PDF to detect changes."""
    return hashlib.sha256(SRS_PATH.read_bytes()).hexdigest()


def _extract_requirement(req_id: str, srs_text: str) -> str | None:
    """Extract requirement text from SRS using regex.

    Args:
        req_id: Requirement ID (e.g., "SKYRADAR-ARR-044")
        srs_text: Full SRS document text

    Returns:
        Requirement text or None if not found
    """
    # Find all requirement positions
    matches = list(REQ_PATTERN.finditer(srs_text))
    if not matches:
        return None

    # Find target requirement and next position
    for i, m in enumerate(matches):
        if m.group(1) == req_id:
            next_pos = matches[i + 1].start() if i + 1 < len(matches) else len(srs_text)
            raw_text = srs_text[m.start() : next_pos]

            # Clean up: remove excessive whitespace while preserving structure
            lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
            return "\n".join(lines)

    return None


def get_requirement(req_id: str) -> str | None:
    """Get requirement text with automatic cache invalidation on PDF change.

    Args:
        req_id: Requirement ID (e.g., "SKYRADAR-ARR-044")

    Returns:
        Requirement text or None if not found
    """
    # Check if PDF has changed
    current_hash = _get_pdf_hash()
    cached_hash: str | None = _cache.get("_pdf_hash")

    if cached_hash != current_hash:
        # PDF changed - clear cache and update hash
        _cache.clear()
        _cache["_pdf_hash"] = current_hash

    # Try cache first
    if req_id in _cache:
        cached_value: str = _cache[req_id]
        return cached_value

    # Cache miss - extract and store
    with pymupdf.open(SRS_PATH) as doc:
        srs_text = "\n".join(page.get_text(sort=True) for page in doc)

    result = _extract_requirement(req_id, srs_text)
    if result is not None:
        _cache[req_id] = result

    return result


@dataclass
class RegexState:
    """State for regex extraction."""

    req_name: str = ""
    requirement_description: str = ""
    errors: list[str] = field(default_factory=list)


async def retrieve_requirement_regex(state: RegexState) -> dict[str, Any]:
    """Retrieve requirement using cached regex extraction.

    Args:
        state: Current state with req_name

    Returns:
        Dict with requirement_description or errors
    """
    try:
        result = get_requirement(state.req_name)
        if result is None:
            return {
                "errors": [*state.errors, f"Requirement {state.req_name} not found"]
            }
        return {"requirement_description": result}
    except Exception as e:
        return {"errors": [*state.errors, f"Regex extraction error: {e}"]}
