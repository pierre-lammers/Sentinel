"""State definitions for the test coverage pipeline."""

from __future__ import annotations

import operator
from dataclasses import dataclass
from typing import Annotated, Any

from typing_extensions import TypedDict

from agent.models import FalsePositive, ScenarioResult


def _last_value(_: int, new: int) -> int:
    """Use the new value (last write wins)."""
    return new


class State(TypedDict, total=False):
    """Pipeline state for test coverage analysis.

    Reducers:
    - operator.add: Append to lists
    - _last_value: Replace with new value
    """

    # Input
    req_name: str

    # Requirement data
    requirement_description: str

    # Scenario iteration
    scenario_paths: list[str]
    dataset_paths: list[str]
    current_scenario_index: Annotated[int, _last_value]

    # Generated test cases (Pydantic models from structured output)
    generated_test_cases: list[Any]

    # Results (append mode for loop accumulation)
    scenario_results: Annotated[list[ScenarioResult], operator.add]
    aggregated_test_cases: list[Any]  # Pydantic models from structured output
    false_positives: Annotated[list[FalsePositive], operator.add]

    # Agent reasoning (for debugging/tracing)
    agent_reasoning: Annotated[list[str], operator.add]

    # Errors (append mode)
    errors: Annotated[list[str], operator.add]


@dataclass
class Context:
    """Runtime configuration for the pipeline."""

    llm_model: str = "codestral-2501"
    temperature: float = 0.0
