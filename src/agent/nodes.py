"""Graph nodes for test coverage pipeline."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from deepagents import create_deep_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_core.messages import HumanMessage
from langgraph.runtime import Runtime
from mistralai.models import SystemMessage, UserMessage

from agent.deep_agent import retrieve_scenario_and_dataset_files
from agent.llm_factory import get_llm, get_mistral_client
from agent.models import (
    AgentCoverageAnalysis,
    CoverageAnalysis,
    FalsePositive,
    FalsePositiveCheck,
    ScenarioResult,
    TestCaseList,
)
from agent.prompts import (
    ANALYZE_SCENARIO_AGENT_SYSTEM,
    ANALYZE_SCENARIO_AGENT_TASK,
    GENERATE_TEST_CASES_SYSTEM,
    GENERATE_TEST_CASES_USER,
    IDENTIFY_COVERAGE_SYSTEM,
    IDENTIFY_COVERAGE_USER,
    VERIFY_FALSE_POSITIVE_SYSTEM,
    VERIFY_FALSE_POSITIVE_USER,
    format_test_cases_list,
)
from agent.state import Context, State

# Retry configuration for transient API errors
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

# =============================================================================
# Coverage Agent
# =============================================================================


def get_coverage_agent(model: str = "codestral-2501") -> Any:
    """Create a deep coverage analysis agent with reasoning capabilities."""
    llm = get_llm(model=model, temperature=0.0)
    return create_deep_agent(
        model=llm,
        system_prompt=ANALYZE_SCENARIO_AGENT_SYSTEM,
        response_format=ToolStrategy(AgentCoverageAnalysis),
    )


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
    """Generate test cases for the requirement using LLM."""
    if state.get("errors"):
        return {}

    ctx = runtime.context or Context()
    client = get_mistral_client()

    async def _make_api_call() -> Any:
        return await client.chat.parse_async(
            model=ctx.llm_model,
            messages=[
                SystemMessage(content=GENERATE_TEST_CASES_SYSTEM),
                UserMessage(
                    content=GENERATE_TEST_CASES_USER.format(
                        req_name=state["req_name"],
                        requirement_description=state.get(
                            "requirement_description", ""
                        ),
                    )
                ),
            ],
            temperature=ctx.temperature,
            response_format=TestCaseList,
        )

    try:
        response = await _retry_api_call(_make_api_call)

        parsed = _get_parsed(response)
        if not parsed:
            return {"errors": ["No parsed response from LLM"]}

        return {"generated_test_cases": parsed.test_cases}
    except Exception as e:
        return {"errors": [f"Test case generation error: {e}"]}


async def analyze_scenario_agent(
    state: State, runtime: Runtime[Context]
) -> dict[str, Any]:
    """Analyze scenario using a ReAct agent with exploration tools.

    The agent can read files, search patterns, parse XML, and explore
    related files to determine test coverage with multi-step reasoning.
    """
    if state.get("errors"):
        return {"current_scenario_index": state.get("current_scenario_index", 0) + 1}

    paths = state.get("scenario_paths", [])
    idx = state.get("current_scenario_index", 0)

    if idx >= len(paths):
        return {}

    scenario_path = paths[idx]
    ctx = runtime.context or Context()
    scenario_name = Path(scenario_path).stem

    # Create agent
    agent = get_coverage_agent(model=ctx.llm_model)

    # Format test cases for the prompt
    generated_tcs = state.get("generated_test_cases", [])
    test_cases_formatted = "\n".join(
        [f"- {tc.id}: {tc.description}" for tc in generated_tcs]
    )

    task_prompt = ANALYZE_SCENARIO_AGENT_TASK.format(
        scenario_path=scenario_path,
        test_cases_formatted=test_cases_formatted,
    )

    try:
        result = await agent.ainvoke({"messages": [HumanMessage(content=task_prompt)]})
        final_message = result["messages"][-1].content

        # Extract structured response from agent
        coverage_analysis = result["structured_response"]

        scenario_result: ScenarioResult = {
            "scenario_name": scenario_name,
            "scenario_path": scenario_path,
            "test_cases": coverage_analysis.test_cases,
        }

        return {
            "scenario_results": [scenario_result],
            "current_scenario_index": idx + 1,
            "agent_reasoning": [final_message],
        }

    except Exception as e:
        return {
            "errors": [f"Agent analysis error for {scenario_path}: {e}"],
            "current_scenario_index": idx + 1,
        }


async def analyze_scenario(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    """Analyze current scenario: load, identify coverage, verify false positives.

    Combines loading, coverage identification, and false positive verification
    into a single node for cleaner graph structure.
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
    evidence_map = coverage_result["evidence_map"]

    # Build scenario result
    scenario_result: ScenarioResult = {
        "scenario_name": scenario_name,
        "scenario_path": path,
        "test_cases": test_cases,
    }

    # Verify false positives for covered test cases
    present_tcs = [tc for tc in test_cases if tc.present]
    false_positives = await _verify_false_positives(
        present_tcs, evidence_map, state, ctx, scenario_result, content
    )

    # Update test cases based on false positive results
    fp_ids = {fp["test_case_id"] for fp in false_positives}
    for tc in scenario_result["test_cases"]:
        if tc.id in fp_ids:
            tc.present = False

    return {
        "scenario_results": [scenario_result],
        "false_positives": false_positives,
        "current_scenario_index": idx + 1,
    }


async def _identify_coverage(
    state: State, ctx: Context, scenario_name: str, content: str
) -> dict[str, Any]:
    """Identify which test cases are covered by the scenario."""
    if not state.get("generated_test_cases"):
        return {"test_cases": [], "evidence_map": {}}

    client = get_mistral_client()

    async def _make_api_call() -> Any:
        return await client.chat.parse_async(
            model=ctx.llm_model,
            messages=[
                SystemMessage(content=IDENTIFY_COVERAGE_SYSTEM),
                UserMessage(
                    content=IDENTIFY_COVERAGE_USER.format(
                        req_name=state["req_name"],
                        scenario_name=scenario_name,
                        test_cases_list=format_test_cases_list(
                            state["generated_test_cases"]
                        ),
                        scenario_content=content,
                    )
                ),
            ],
            temperature=ctx.temperature,
            response_format=CoverageAnalysis,
        )

    try:
        response = await _retry_api_call(_make_api_call)

        parsed = _get_parsed(response)
        if not parsed:
            return {"error": "No parsed response from coverage LLM"}

        evidence_map = {tc.id: tc.evidence for tc in parsed.test_cases}

        return {"test_cases": parsed.test_cases, "evidence_map": evidence_map}
    except Exception as e:
        return {"error": f"Coverage analysis error: {e}"}


async def _verify_false_positives(
    present_tcs: list[Any],
    evidence_map: dict[str, str],
    state: State,
    ctx: Context,
    scenario_result: ScenarioResult,
    content: str,
) -> list[FalsePositive]:
    """Verify covered test cases for false positives (parallelized)."""
    if not present_tcs:
        return []

    tasks = [
        _verify_single_tc(
            tc, evidence_map.get(tc.id, ""), state, ctx, scenario_result, content
        )
        for tc in present_tcs
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    return [r for r in results if isinstance(r, dict) and r is not None]


async def _verify_single_tc(
    tc: Any,
    evidence: str,
    state: State,
    ctx: Context,
    scenario_result: ScenarioResult,
    content: str,
) -> FalsePositive | None:
    """Verify a single test case for false positive."""
    client = get_mistral_client()

    async def _make_api_call() -> Any:
        return await client.chat.parse_async(
            model=ctx.llm_model,
            messages=[
                SystemMessage(content=VERIFY_FALSE_POSITIVE_SYSTEM),
                UserMessage(
                    content=VERIFY_FALSE_POSITIVE_USER.format(
                        req_name=state["req_name"],
                        scenario_name=scenario_result["scenario_name"],
                        test_case_id=tc.id,
                        test_case_description=tc.description,
                        evidence=evidence or "No evidence provided",
                        scenario_content=content,
                    )
                ),
            ],
            temperature=ctx.temperature,
            response_format=FalsePositiveCheck,
        )

    try:
        response = await _retry_api_call(_make_api_call)

        parsed = _get_parsed(response)
        if parsed and parsed.is_false_positive:
            return {
                "scenario_name": scenario_result["scenario_name"],
                "scenario_path": scenario_result["scenario_path"],
                "test_case_id": tc.id,
                "test_case_description": tc.description,
                "reason": parsed.reason,
            }
        return None
    except Exception:
        return None


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


# =============================================================================
# Helpers
# =============================================================================


async def _retry_api_call(
    api_call: Any,
    max_retries: int = MAX_RETRIES,
    delay: float = RETRY_DELAY_SECONDS,
) -> Any:
    """Retry an async API call with exponential backoff.

    Args:
        api_call: Async callable to execute
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds

    Returns:
        API response

    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    for attempt in range(max_retries):
        try:
            return await api_call()
        except Exception as e:
            last_exception = e
            error_str = str(e)
            # Only retry on 503 or transient errors
            if "503" in error_str or "Service unavailable" in error_str:
                if attempt < max_retries - 1:
                    wait_time = delay * (2**attempt)  # Exponential backoff
                    await asyncio.sleep(wait_time)
                    continue
            # Re-raise non-retryable errors immediately
            raise
    raise last_exception  # type: ignore[misc]


def _get_parsed(response: Any) -> Any:
    """Extract parsed response from Mistral response."""
    if not response.choices or not response.choices[0].message:
        return None
    return response.choices[0].message.parsed
