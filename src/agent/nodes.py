"""Graph nodes for test coverage pipeline."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, cast

from langchain.agents.structured_output import ToolStrategy
from langgraph.runtime import Runtime

from agent.deep_agent import retrieve_scenario_and_dataset_files
from agent.llm_factory import get_agent
from agent.models import (
    CoverageAnalysis,
    ScenarioResult,
    TestCaseList,
)
from agent.prompts import (
    GENERATE_TEST_CASES_SYSTEM,
    GENERATE_TEST_CASES_USER,
    IDENTIFY_COVERAGE_SYSTEM,
    IDENTIFY_COVERAGE_USER,
    format_test_cases_list,
)
from agent.state import Context, State

# =============================================================================
# Data Loading Nodes
# =============================================================================


async def load_scenarios(state: State, runtime: Runtime[Context]) -> dict[str, Any]:  # noqa: ARG001
    """Load XML scenario file paths for the requirement."""
    paths = await retrieve_scenario_and_dataset_files(state["req_name"])
    if not paths:
        return {"errors": [f"No scenarios found for {state['req_name']}"]}
    return {
        "scenario_paths": paths.scenarios,
        "dataset_paths": paths.datasets,
        "current_scenario_index": 0,
    }


async def retrieve_requirement(
    state: State, runtime: Runtime[Context]
) -> dict[str, Any]:  # noqa: ARG001
    """Retrieve requirement description using regex extraction."""
    from agent.regex_extract import RegexState, retrieve_requirement_regex

    regex_state = RegexState(
        req_name=state["req_name"],
        errors=list(state.get("errors", [])),
    )
    return await retrieve_requirement_regex(regex_state)


# =============================================================================
# LLM Nodes
# =============================================================================


async def generate_test_cases(
    state: State, runtime: Runtime[Context]
) -> dict[str, Any]:
    """Generate test cases for the requirement using LLM.

    Uses ModelRetryMiddleware for automatic retry with exponential backoff.
    """
    if state.get("errors"):
        return {}

    ctx = runtime.context or Context()

    # Create agent with structured output and retry middleware
    agent = get_agent(
        model=ctx.llm_model,
        temperature=ctx.temperature,
        response_format=ToolStrategy(TestCaseList),
        system_prompt=GENERATE_TEST_CASES_SYSTEM,
    )

    try:
        # ModelRetryMiddleware handles retries automatically
        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": GENERATE_TEST_CASES_USER.format(
                            req_name=state["req_name"],
                            requirement_description=state.get(
                                "requirement_description", ""
                            ),
                        ),
                    }
                ]
            }
        )

        parsed = cast(TestCaseList, result.get("structured_response"))
        if not parsed:
            return {"errors": ["No parsed response from LLM"]}

        return {"generated_test_cases": parsed.test_cases}
    except Exception as e:
        return {"errors": [f"Test case generation error: {e}"]}


async def analyze_scenario(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    """Analyze current scenario: load and identify coverage.

    Combines loading and coverage identification into a single node
    for cleaner graph structure.
    """
    if state.get("errors"):
        return {"current_scenario_index": state.get("current_scenario_index", 0) + 1}

    paths = state.get("scenario_paths", [])
    idx = state.get("current_scenario_index", 0)

    if idx >= len(paths):
        return {}

    path = paths[idx]
    ctx = runtime.context or Context()

    # Load scenario content
    try:
        content = await asyncio.to_thread(Path(path).read_text, encoding="utf-8")
        scenario_name = Path(path).stem
    except Exception as e:
        return {
            "errors": [f"Error reading {path}: {e}"],
            "current_scenario_index": idx + 1,
        }

    # Identify coverage
    coverage_result = await _identify_coverage(state, ctx, scenario_name, content)
    if "error" in coverage_result:
        return {
            "errors": [coverage_result["error"]],
            "current_scenario_index": idx + 1,
        }

    test_cases = coverage_result["test_cases"]

    # Build scenario result
    scenario_result: ScenarioResult = {
        "scenario_name": scenario_name,
        "scenario_path": path,
        "test_cases": test_cases,
    }

    return {
        "scenario_results": [scenario_result],
        "current_scenario_index": idx + 1,
    }


async def _identify_coverage(
    state: State, ctx: Context, scenario_name: str, content: str
) -> dict[str, Any]:
    """Identify which test cases are covered by the scenario.

    Uses ModelRetryMiddleware for automatic retry with exponential backoff.
    """
    if not state.get("generated_test_cases"):
        return {"test_cases": [], "evidence_map": {}}

    # Create agent with structured output and retry middleware
    agent = get_agent(
        model=ctx.llm_model,
        temperature=ctx.temperature,
        response_format=ToolStrategy(CoverageAnalysis),
        system_prompt=IDENTIFY_COVERAGE_SYSTEM,
    )

    try:
        # ModelRetryMiddleware handles retries automatically
        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": IDENTIFY_COVERAGE_USER.format(
                            req_name=state["req_name"],
                            scenario_name=scenario_name,
                            test_cases_list=format_test_cases_list(
                                state["generated_test_cases"]
                            ),
                            scenario_content=content,
                        ),
                    }
                ]
            }
        )

        parsed = cast(CoverageAnalysis, result.get("structured_response"))
        if not parsed:
            return {"error": "No parsed response from coverage LLM"}

        evidence_map = {tc.id: tc.evidence for tc in parsed.test_cases}

        return {"test_cases": parsed.test_cases, "evidence_map": evidence_map}
    except Exception as e:
        return {"error": f"Coverage analysis error: {e}"}


# =============================================================================
# Routing
# =============================================================================


def route_scenario_loop(state: State) -> str:
    """Determine if more scenarios remain to process."""
    if state.get("errors"):
        return "end"
    idx = state.get("current_scenario_index", 0)
    paths = state.get("scenario_paths", [])
    return "continue" if idx < len(paths) else "end"


# =============================================================================
# Aggregation
# =============================================================================


async def aggregate_test_cases(
    state: State, runtime: Runtime[Context]
) -> dict[str, Any]:  # noqa: ARG001
    """Aggregate test cases with OR logic on coverage."""
    results = state.get("scenario_results", [])
    if not results:
        return {"aggregated_test_cases": []}

    aggregated: dict[str, Any] = {}
    for result in results:
        for tc in result["test_cases"]:
            tc_id = tc.id
            if tc_id not in aggregated:
                aggregated[tc_id] = tc
            elif tc.present:
                # OR logic: covered in any scenario = covered
                aggregated[tc_id].present = True

    return {"aggregated_test_cases": list(aggregated.values())}
