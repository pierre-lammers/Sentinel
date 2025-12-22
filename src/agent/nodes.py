"""Graph nodes for test coverage pipeline."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

from deepagents import create_deep_agent
from langchain_core.messages import HumanMessage
from langgraph.runtime import Runtime
from mistralai.models import SystemMessage, UserMessage

from agent.deep_agent import retrieve_scenario_and_dataset_files
from agent.llm_factory import get_llm, get_mistral_client
from agent.models import (
    CoverageAnalysis,
    FalsePositive,
    FalsePositiveCheck,
    ScenarioResult,
    TestCase,
    TestCaseList,
)
from agent.prompts import (
    GENERATE_TEST_CASES_SYSTEM,
    GENERATE_TEST_CASES_USER,
    IDENTIFY_COVERAGE_SYSTEM,
    IDENTIFY_COVERAGE_USER,
    VERIFY_FALSE_POSITIVE_SYSTEM,
    VERIFY_FALSE_POSITIVE_USER,
    format_test_cases_list,
)
from agent.state import Context, State
from agent.tools import COVERAGE_TOOLS

# Retry configuration for transient API errors
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

# =============================================================================
# Coverage Agent
# =============================================================================

COVERAGE_AGENT_PROMPT = """You are a test coverage analyst with deep reasoning capabilities.

Your mission is to analyze test scenarios and determine which test cases are truly covered,
using careful reasoning and systematic exploration.

## Analysis Approach

Use a multi-step reasoning process (chain of thought):

1. **Understand the Test Scenario:**
   - Use `read_test_file` to read the scenario file
   - Use `parse_test_structure` to understand the file format and structure
   - Use `get_file_summary` to get an overview of the file

2. **For Each Test Case - Think Step by Step:**

   a) **Understand What Should Be Tested:**
      - What is the test case trying to verify?
      - What conditions or behaviors should be validated?

   b) **Search for Evidence:**
      - Use `search_in_file` to find keywords, identifiers, or patterns
      - Look for test setup (input data, preconditions)
      - Look for verification logic (checks, assertions, expected outcomes)

   c) **Verify Actual Implementation:**
      - Does the test file ACTUALLY set up the described scenario?
      - Does it ACTUALLY verify the expected outcome?
      - Is there explicit or implicit assertion logic?

   d) **Beware of False Positives:**
      - Distinguish between what's DESCRIBED vs. what's IMPLEMENTED
      - Comments or documentation mentioning a test ≠ actual test implementation
      - Similar-sounding test cases may test different conditions
      - Check if the test data matches what the test case requires

3. **Explore Related Context (if needed):**
   - Use `list_related_files` to find related test files or configurations
   - Use `read_test_file` on related files if they might contain relevant setup

## Coverage Criteria

A test case is **COVERED** if and only if ALL of these are present:
- ✅ Test data setup that matches the test case requirements
- ✅ Execution or simulation of the scenario
- ✅ Verification of the expected outcome (explicit or implicit assertions)

A test case is **NOT COVERED** if:
- ❌ Only mentioned in comments/documentation without implementation
- ❌ Setup exists but no verification of outcome
- ❌ A different (but similar) condition is tested instead
- ❌ The description says one thing but the code tests another

## Output Format

For each test case, provide your reasoning and conclusion:

**Test Case: [ID] - [Description]**

**Reasoning:**
[Your step-by-step thought process: what you searched for, what you found,
why you believe it's covered or not covered]

**Status:** COVERED or NOT_COVERED

**Evidence:** [Specific lines, elements, or patterns from the test file that prove
your conclusion. Empty if not covered]

---

Be systematic, thorough, and honest. When in doubt, verify your assumptions with additional searches.
Focus on actual implementation, not just mentions or intentions."""


def get_coverage_agent(model: str = "codestral-2501") -> Any:
    """Create a deep coverage analysis agent with reasoning capabilities."""
    llm = get_llm(model=model, temperature=0.0)
    return create_deep_agent(
        model=llm,
        tools=COVERAGE_TOOLS,
        system_prompt=COVERAGE_AGENT_PROMPT,
    )


def _parse_agent_coverage_output(
    agent_output: str, generated_test_cases: list[str]
) -> list[TestCase]:
    """Parse agent output into structured coverage data."""
    test_cases: list[TestCase] = []

    for tc_string in generated_test_cases:
        parts = tc_string.split(":", 1)
        tc_id = parts[0].strip()
        tc_desc = parts[1].strip() if len(parts) > 1 else ""

        # Check if covered in agent output
        is_covered = False
        if tc_id in agent_output:
            # Find context around the test case ID
            pattern = rf"{re.escape(tc_id)}[^A-Z]*?(COVERED|NOT_COVERED)"
            match = re.search(pattern, agent_output, re.IGNORECASE)
            if match:
                is_covered = match.group(1).upper() == "COVERED"
            else:
                # Fallback: look for COVERED near the ID without NOT_
                context_start = agent_output.find(tc_id)
                context = agent_output[context_start : context_start + 200]
                if (
                    "COVERED" in context.upper()
                    and "NOT_COVERED" not in context.upper()
                ):
                    is_covered = True

        test_cases.append(TestCase(id=tc_id, description=tc_desc, present=is_covered))

    return test_cases


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

        return {
            "generated_test_cases": [
                f"{tc.id}: {tc.description}" for tc in parsed.test_cases
            ]
        }
    except Exception as e:
        return {"errors": [f"Test case generation error: {e}"]}


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
        "test_cases": [
            {"id": tc["id"], "description": tc["description"], "present": tc["present"]}
            for tc in test_cases
        ],
    }

    # Verify false positives for covered test cases
    present_tcs = [tc for tc in test_cases if tc["present"]]
    false_positives = await _verify_false_positives(
        present_tcs, evidence_map, state, ctx, scenario_result, content
    )

    # Update test cases based on false positive results
    fp_ids = {fp["test_case_id"] for fp in false_positives}
    for tc in scenario_result["test_cases"]:
        if tc["id"] in fp_ids:
            tc["present"] = False

    return {
        "scenario_results": [scenario_result],
        "false_positives": false_positives,
        "current_scenario_index": idx + 1,
    }


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
    test_cases_formatted = "\n".join(
        [f"- {tc}" for tc in state.get("generated_test_cases", [])]
    )

    task_prompt = f"""Analyze this test scenario for coverage.

**Scenario file:** {scenario_path}

**Test cases to verify:**
{test_cases_formatted}

**Requirement context:**
{state.get("requirement_description", "N/A")}

For each test case, determine if it is COVERED or NOT_COVERED.
Provide evidence from the XML file for covered test cases."""

    try:
        result = await agent.ainvoke({"messages": [HumanMessage(content=task_prompt)]})
        final_message = result["messages"][-1].content

        # Parse agent output to extract coverage info
        test_cases = _parse_agent_coverage_output(
            final_message, state.get("generated_test_cases", [])
        )

        scenario_result: ScenarioResult = {
            "scenario_name": scenario_name,
            "scenario_path": scenario_path,
            "test_cases": test_cases,
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

        test_cases = [
            {"id": tc.id, "description": tc.description, "present": tc.present}
            for tc in parsed.test_cases
        ]
        evidence_map = {tc.id: tc.evidence for tc in parsed.test_cases}

        return {"test_cases": test_cases, "evidence_map": evidence_map}
    except Exception as e:
        return {"error": f"Coverage analysis error: {e}"}


async def _verify_false_positives(
    present_tcs: list[dict[str, Any]],
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
            tc, evidence_map.get(tc["id"], ""), state, ctx, scenario_result, content
        )
        for tc in present_tcs
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    return [r for r in results if isinstance(r, dict) and r is not None]


async def _verify_single_tc(
    tc: dict[str, Any],
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
                        test_case_id=tc["id"],
                        test_case_description=tc["description"],
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
                "test_case_id": tc["id"],
                "test_case_description": tc["description"],
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

    aggregated: dict[str, TestCase] = {}
    for result in results:
        for tc in result["test_cases"]:
            tc_id = tc["id"]
            if tc_id not in aggregated:
                aggregated[tc_id] = {
                    "id": tc_id,
                    "description": tc["description"],
                    "present": tc["present"],
                }
            elif tc["present"]:
                # OR logic: covered in any scenario = covered
                aggregated[tc_id]["present"] = True

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
