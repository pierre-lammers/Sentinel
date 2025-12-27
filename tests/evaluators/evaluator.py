"""Experiment evaluators for requirement evaluation using Langfuse datasets."""

import json
from typing import Any, cast

from langchain.agents.structured_output import ToolStrategy
from langfuse import Evaluation
from pydantic import BaseModel, Field

from agent.llm_factory import LLMProvider, get_agent


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


EVALUATOR_SYSTEM_PROMPT = """You are a test case coverage evaluator."""


def create_test_case_evaluator_agent(
    model: str = "codestral-2501",
    temperature: float = 0.0,
    provider: LLMProvider | None = None,
) -> Any:
    """Create an agent for evaluating test case coverage with structured output.

    Uses ModelRetryMiddleware for automatic retry with exponential backoff.
    """
    agent = get_agent(
        model=model,
        temperature=temperature,
        provider=provider,
        system_prompt=EVALUATOR_SYSTEM_PROMPT,
        response_format=ToolStrategy(TestCaseMatches),
        max_retries=5,  # Higher retry count for rate limits
        initial_delay=10.0,  # Longer initial delay for rate limits
    )

    return agent


async def evaluate_test_cases_async(
    output_test_cases: list[Any],
    expected_test_cases: list[Any],
    model: str = "codestral-2501",
    provider: LLMProvider | None = None,
) -> TestCaseMatches:
    """Evaluate test cases using the deep agent.

    Args:
        output_test_cases: Generated test cases to evaluate.
        expected_test_cases: Expected test cases to compare against.
        model: Model name to use for evaluation.
        provider: LLM provider to use (Mistral, OpenAI, or Anthropic).

    Returns:
        TestCaseMatches object containing matches for each expected test case.
    """
    agent = create_test_case_evaluator_agent(model=model, provider=provider)

    evaluation_prompt = f"""You are evaluating test case coverage by matching generated test cases to expected test cases.
    <expected_test_cases>
    {expected_test_cases}
    </expected_test_cases>

    <output_test_cases>
    {output_test_cases}
    </output_test_cases>

    For each expected test case:
    1. Find the generated test case that describes the SAME test scenario (semantic match)
    2. Compare their 'present' field values
    3. Set isSamePresent to true ONLY if both descriptions match semantically AND present values are identical

    Return one match per expected test case with:
    - expected_description: The expected test case description
    - generated_description: The best matching generated test case description
    - isSamePresent: true if semantic match AND present values are the same, false otherwise"""

    # ModelRetryMiddleware handles retries automatically
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": evaluation_prompt}]}
    )

    # Extract the structured output from the final message
    return cast(TestCaseMatches, result["structured_response"])


async def test_case_coverage_evaluator(
    *, output: Any, expected_output: Any, **kwargs: Any
) -> Evaluation:
    """Evaluates test case coverage by comparing generated vs expected test cases.

    Uses an LLM agent to semantically match test case descriptions between output and expected_output.

    Args:
        output: Graph output dict with 'aggregated_test_cases' field
        expected_output: Expected output dict with 'aggregated_test_cases' field
        **kwargs: Additional keyword arguments

    Returns:
        Evaluation object with score (0-10) and detailed comment
    """

    # Extract aggregated_test_cases from dictionaries
    output_test_cases = output.get("aggregated_test_cases", [])
    expected_test_cases = expected_output.get("aggregated_test_cases", [])

    if not output_test_cases:
        return Evaluation(
            name="test_case_coverage",
            value=0,
            comment="No generated test cases in aggregated_test_cases",
        )

    try:
        # Run the async evaluation using the deep agent
        response = await evaluate_test_cases_async(
            output_test_cases, expected_test_cases
        )

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
