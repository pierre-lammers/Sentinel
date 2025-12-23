"""Experiment evaluators for requirement evaluation using Langfuse datasets."""

import json
from typing import Any, cast

from langfuse import Evaluation
from pydantic import BaseModel, Field

from agent.llm_factory import get_llm


class TestCaseMatch(BaseModel):
    """Represents a match between an expected and generated test case."""

    expected_description: str = Field(
        description="Description of the expected test case"
    )
    generated_description: str = Field(
        description="Description of the matching generated test case"
    )
    isSamePresent: bool = Field(
        description="Whether output_present equals expected_present"
    )


class TestCaseMatches(BaseModel):
    """List of test case matches."""

    matches: list[TestCaseMatch] = Field(
        description="List of matches for each expected test case"
    )


def test_case_coverage_evaluator(
    *, output: Any, expected_output: Any, **kwargs: Any
) -> Evaluation:
    """Evaluates test case coverage by comparing generated vs expected test cases.

    Uses an LLM to semantically match test case descriptions between output and expected_output.

    Args:
        output: Graph output dict with 'aggregated_test_cases' field
        expected_output: Expected output dict with 'aggregated_test_cases' field
        **kwargs: Additional keyword arguments

    Returns:
        Evaluation object with score (0-10) and detailed comment
    """
    llm = get_llm(temperature=0)

    # Parse output and expected_output if they are strings
    if isinstance(output, str):
        try:
            output = json.loads(output)
        except json.JSONDecodeError:
            output = {}
    if isinstance(expected_output, str):
        try:
            expected_output = json.loads(expected_output)
        except json.JSONDecodeError:
            expected_output = {}

    # Extract aggregated_test_cases from dictionaries
    if isinstance(output, dict):
        output_test_cases = output.get("aggregated_test_cases", [])
    else:
        output_test_cases = []

    if isinstance(expected_output, dict):
        expected_test_cases = expected_output.get("aggregated_test_cases", [])
    else:
        expected_test_cases = []

    # Handle empty cases
    if not expected_test_cases:
        return Evaluation(
            name="test_case_coverage",
            value=0,
            comment="No expected test cases in aggregated_test_cases",
        )

    if not output_test_cases:
        return Evaluation(
            name="test_case_coverage",
            value=0,
            comment="No generated test cases in aggregated_test_cases",
        )

    # Normalize present field (handle boolean and string values)
    def normalize_present(value: Any) -> str:
        """Normalize present field to string for comparison."""
        if isinstance(value, bool):
            return str(value).lower()
        return str(value).lower()

    # Build test case info with normalized present field
    expected_with_present = [
        {
            "description": tc.get("description", str(tc)),
            "present": normalize_present(tc.get("present")),
            "id": tc.get("id", ""),
        }
        for tc in expected_test_cases
    ]

    output_with_present = [
        {
            "description": tc.get("description", str(tc)),
            "present": normalize_present(tc.get("present")),
            "id": tc.get("id", ""),
        }
        for tc in output_test_cases
    ]

    # Format for LLM with present field info
    expected_text = "\n".join(
        f"{i + 1}. {tc['description']} [present={tc['present']}]"
        for i, tc in enumerate(expected_with_present)
    )
    output_text = "\n".join(
        f"{i + 1}. {tc['description']} [present={tc['present']}]"
        for i, tc in enumerate(output_with_present)
    )

    # Create evaluation prompt
    evaluation_prompt = f"""You are evaluating test case coverage by matching generated test cases to expected test cases.

<expected_test_cases>
{expected_text}
</expected_test_cases>

<generated_test_cases>
{output_text}
</generated_test_cases>

For each expected test case:
1. Find the generated test case that describes the SAME test scenario (semantic match)
2. Compare their 'present' field values
3. Set isSamePresent to true ONLY if both descriptions match semantically AND present values are identical

Return one match per expected test case with:
- expected_description: The expected test case description
- generated_description: The best matching generated test case description
- isSamePresent: true if semantic match AND present values are the same, false otherwise"""

    try:
        # Use structured output directly with BaseModel
        llm_with_structure = llm.with_structured_output(TestCaseMatches)
        response = cast(TestCaseMatches, llm_with_structure.invoke(evaluation_prompt))

        # Access matches directly from structured response
        matches_list = response.matches

        # Count successful matches where isSamePresent is true
        matched_count = sum(1 for m in matches_list if m.isSamePresent)
        total_expected = len(expected_test_cases)
        score = (matched_count / total_expected) * 10

        # Build detailed comment
        match_details = "\n".join(
            f"  [{i + 1}] {'✓' if m.isSamePresent else '✗'} {m.expected_description[:80]}..."
            for i, m in enumerate(matches_list)
        )

        comment = f"""Test Case Coverage Assessment:
- Total Expected: {total_expected}
- Correctly Matched (same coverage): {matched_count}
- Score: {matched_count}/{total_expected} ({(matched_count / total_expected) * 100:.1f}%)

Match Details:
{match_details}"""

        return Evaluation(
            name="test_case_coverage",
            value=score,
            comment=comment,
        )

    except Exception as e:
        return Evaluation(
            name="test_case_coverage",
            value=0,
            comment=f"Evaluation failed: {e!s}",
        )
