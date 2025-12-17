"""State definitions for the test coverage pipeline."""

from __future__ import annotations

import operator
from dataclasses import dataclass
from typing import Annotated

from typing_extensions import TypedDict

from agent.models import FalsePositive, ScenarioResult, TestCase


def replace_or_keep(current: str, new: str) -> str:
    """Replace value only if new is non-empty."""
    return new if new else current


def last_value(current: int, new: int) -> int:
    """Use the new value (last write wins)."""
    return new


class State(TypedDict, total=False):
    """Pipeline state using TypedDict with reducers.

    Uses Annotated types for automatic state merging:
    - operator.add: Append lists
    - replace_or_keep: Only update if non-empty
    """

    # Input
    req_name: str

    # Scenario iteration
    scenario_paths: list[str]
    current_scenario_index: Annotated[int, last_value]
    current_scenario_content: Annotated[str, replace_or_keep]
    current_scenario_name: Annotated[str, replace_or_keep]

    # Requirement data
    requirement_description: Annotated[str, replace_or_keep]

    # Generated test cases (list of "TC-XXX: description")
    generated_test_cases: list[str]

    # Results (append mode)
    scenario_results: Annotated[list[ScenarioResult], operator.add]
    aggregated_test_cases: list[TestCase]
    false_positives: Annotated[list[FalsePositive], operator.add]

    # Errors (append mode)
    errors: Annotated[list[str], operator.add]


@dataclass
class Context:
    """Runtime configuration for the pipeline."""

    llm1_model: str = "codestral-2501"
    llm2_model: str = "codestral-2501"
    temperature: float = 0.0
