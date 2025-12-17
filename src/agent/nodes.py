"""Graph nodes for test coverage pipeline."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from langgraph.runtime import Runtime
from mistralai.models import SystemMessage, UserMessage

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
from agent.utils import find_scenario_files, get_mistral_client

# =============================================================================
# Data Loading Nodes
# =============================================================================


async def load_scenarios(state: State, runtime: Runtime[Context]) -> dict[str, Any]:  # noqa: ARG001
    """Load XML scenario file paths for the requirement."""
    paths = await asyncio.to_thread(find_scenario_files, state["req_name"])
    if not paths:
        return {"errors": [f"No scenarios found for {state['req_name']}"]}
    return {"scenario_paths": paths, "current_scenario_index": 0}


async def retrieve_requirement(
    state: State, runtime: Runtime[Context]
) -> dict[str, Any]:  # noqa: ARG001
    """Retrieve requirement description using regex extraction."""
    from agent.regex_extract import RegexState, retrieve_requirement_regex

    regex_state = RegexState(
        req_name=state["req_name"], errors=list(state.get("errors", []))
    )
    return await retrieve_requirement_regex(regex_state)


async def load_current_scenario(
    state: State, runtime: Runtime[Context]
) -> dict[str, Any]:  # noqa: ARG001
    """Load content of the current XML scenario."""
    errors = state.get("errors", [])
    paths = state.get("scenario_paths", [])
    idx = state.get("current_scenario_index", 0)

    if errors or idx >= len(paths):
        return {}

    path = paths[idx]
    try:
        content = await asyncio.to_thread(Path(path).read_text, encoding="utf-8")
        return {
            "current_scenario_content": content,
            "current_scenario_name": Path(path).stem,
        }
    except Exception as e:
        return {"errors": [f"Error reading {path}: {e}"]}


# =============================================================================
# LLM Nodes
# =============================================================================


async def generate_test_cases(
    state: State, runtime: Runtime[Context]
) -> dict[str, Any]:
    """Generate test cases for the requirement using LLM."""
    if state.get("errors"):
        return {}

    try:
        ctx = runtime.context or Context()
        client = get_mistral_client()

        response = await client.chat.parse_async(
            model=ctx.llm1_model,
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

        parsed = _get_parsed_response(response)
        if not parsed:
            raise ValueError("No parsed response from LLM")

        return {
            "generated_test_cases": [
                f"{tc.id}: {tc.description}" for tc in parsed.test_cases
            ]
        }
    except Exception as e:
        return {"errors": [f"Test case generation error: {e}"]}


async def identify_coverage(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    """Identify which test cases are covered by the current scenario."""
    if (
        state.get("errors")
        or not state.get("generated_test_cases")
        or not state.get("current_scenario_content")
    ):
        return {}

    try:
        ctx = runtime.context or Context()
        client = get_mistral_client()

        response = await client.chat.parse_async(
            model=ctx.llm1_model,
            messages=[
                SystemMessage(content=IDENTIFY_COVERAGE_SYSTEM),
                UserMessage(
                    content=IDENTIFY_COVERAGE_USER.format(
                        req_name=state["req_name"],
                        scenario_name=state.get("current_scenario_name", ""),
                        test_cases_list=format_test_cases_list(
                            state["generated_test_cases"]
                        ),
                        scenario_content=state["current_scenario_content"],
                    )
                ),
            ],
            temperature=ctx.temperature,
            response_format=CoverageAnalysis,
        )

        parsed = _get_parsed_response(response)
        if not parsed:
            raise ValueError("No parsed response from LLM")

        result: ScenarioResult = {
            "scenario_name": state.get("current_scenario_name", ""),
            "scenario_path": state["scenario_paths"][
                state.get("current_scenario_index", 0)
            ],
            "test_cases": [
                {"id": tc.id, "description": tc.description, "present": tc.present}
                for tc in parsed.test_cases
            ],
        }
        # Store evidence for false positive verification
        evidence_map = {tc.id: tc.evidence for tc in parsed.test_cases}

        return {"scenario_results": [result], "_evidence_map": evidence_map}
    except Exception as e:
        return {"errors": [f"Coverage analysis error: {e}"]}


async def verify_false_positives(
    state: State, runtime: Runtime[Context]
) -> dict[str, Any]:
    """Verify covered test cases for false positives (parallelized)."""
    results = state.get("scenario_results", [])
    if state.get("errors") or not results:
        return {}

    current_result = results[-1]
    present_test_cases = [tc for tc in current_result["test_cases"] if tc["present"]]

    if not present_test_cases:
        return {}

    ctx = runtime.context or Context()
    evidence_map: dict[str, str] = state.get("_evidence_map") or {}  # type: ignore[assignment]

    # Parallel verification
    tasks = [
        _verify_single_test_case(
            tc=tc,
            state=state,
            ctx=ctx,
            scenario_result=current_result,
            evidence=evidence_map.get(tc["id"], ""),
        )
        for tc in present_test_cases
    ]

    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    false_positives: list[FalsePositive] = []
    for i, result in enumerate(results_list):
        if isinstance(result, BaseException):
            continue
        if result is not None:
            false_positives.append(result)
            # Mark as not present in the original test case
            present_test_cases[i]["present"] = False

    return {"false_positives": false_positives}


async def _verify_single_test_case(
    tc: TestCase,
    state: State,
    ctx: Context,
    scenario_result: ScenarioResult,
    evidence: str,
) -> FalsePositive | None:
    """Verify a single test case for false positive."""
    try:
        client = get_mistral_client()
        response = await client.chat.parse_async(
            model=ctx.llm2_model,
            messages=[
                SystemMessage(content=VERIFY_FALSE_POSITIVE_SYSTEM),
                UserMessage(
                    content=VERIFY_FALSE_POSITIVE_USER.format(
                        req_name=state["req_name"],
                        scenario_name=scenario_result["scenario_name"],
                        test_case_id=tc["id"],
                        test_case_description=tc["description"],
                        evidence=evidence or "No evidence provided",
                        scenario_content=state.get("current_scenario_content", ""),
                    )
                ),
            ],
            temperature=ctx.temperature,
            response_format=FalsePositiveCheck,
        )

        parsed = _get_parsed_response(response)
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
# Control Flow Nodes
# =============================================================================


async def move_to_next_scenario(
    state: State, runtime: Runtime[Context]
) -> dict[str, Any]:  # noqa: ARG001
    """Increment scenario index."""
    return {"current_scenario_index": state.get("current_scenario_index", 0) + 1}


def has_more_scenarios(state: State) -> str:
    """Determine if more scenarios remain to process."""
    if state.get("errors"):
        return "end"
    idx = state.get("current_scenario_index", 0)
    paths = state.get("scenario_paths", [])
    return "continue" if idx < len(paths) else "end"


# =============================================================================
# Aggregation Nodes
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
            if tc["id"] not in aggregated:
                aggregated[tc["id"]] = {
                    "id": tc["id"],
                    "description": tc["description"],
                    "present": tc["present"],
                }
            else:
                # OR logic: if covered in any scenario, mark as covered
                aggregated[tc["id"]]["present"] = (
                    aggregated[tc["id"]]["present"] or tc["present"]
                )

    return {"aggregated_test_cases": list(aggregated.values())}


async def write_false_positives_report(
    state: State, runtime: Runtime[Context]
) -> dict[str, Any]:  # noqa: ARG001
    """Write false positives report to file."""
    fps = state.get("false_positives", [])
    if not fps:
        return {}

    try:
        output_dir = Path(__file__).parent.parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        report_path = output_dir / f"false_positives_{state['req_name']}.txt"

        lines = [
            f"False Positives Report for Requirement: {state['req_name']}",
            "=" * 80,
            "",
        ]
        for fp in fps:
            lines.extend(
                [
                    f"Scenario: {fp['scenario_name']}",
                    f"File: {fp['scenario_path']}",
                    f"Test Case: {fp['test_case_id']} - {fp['test_case_description']}",
                    f"Reason: {fp['reason']}",
                    "-" * 80,
                    "",
                ]
            )

        await asyncio.to_thread(
            report_path.write_text, "\n".join(lines), encoding="utf-8"
        )
        return {}
    except Exception as e:
        return {"errors": [f"Error writing report: {e}"]}


# =============================================================================
# Helpers
# =============================================================================


def _get_parsed_response(response: Any) -> Any:
    """Extract parsed response from Mistral response."""
    if not response.choices or not response.choices[0].message:
        return None
    return response.choices[0].message.parsed
