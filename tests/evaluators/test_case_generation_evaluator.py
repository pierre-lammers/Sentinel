"""Evaluator for test case generation using Langfuse datasets."""

import json
import os
from typing import Any

from langchain_mistralai import ChatMistralAI
from langfuse import Evaluation
from pydantic import SecretStr


def test_case_generation_evaluator(
    *, output: Any, expected_output: Any, **kwargs: Any
) -> Evaluation:
    """LLM-as-judge evaluator for test case generation quality.

    Evaluates how well the generated test cases match the expected test cases
    using semantic similarity rather than exact matching.

    Args:
        output: The generated test cases list
        expected_output: The expected test cases list
        **kwargs: Additional keyword arguments

    Returns:
        Evaluation object with score and reasoning
    """
    # Initialize LLM for evaluation using Mistral
    api_key = os.getenv("MISTRAL_API_KEY")
    llm = ChatMistralAI(
        model_name="mistral-large-latest",
        api_key=SecretStr(api_key) if api_key else None,
        temperature=0,
    )

    # Extract test cases from output
    if isinstance(output, dict):
        generated_cases = output.get("generated_test_cases", [])
        has_error = bool(output.get("errors"))
        error_msg = "; ".join(output.get("errors", []))
    else:
        try:
            output_parsed = json.loads(output) if isinstance(output, str) else output
            generated_cases = output_parsed.get("generated_test_cases", [])
            has_error = bool(output_parsed.get("errors"))
            error_msg = "; ".join(output_parsed.get("errors", []))
        except (json.JSONDecodeError, AttributeError, TypeError):
            generated_cases = []
            has_error = True
            error_msg = "Failed to parse output"

    # Extract expected test cases from expected_output
    if isinstance(expected_output, dict):
        expected_cases = expected_output.get("aggregated_test_cases", [])
    else:
        try:
            expected_parsed = (
                json.loads(expected_output)
                if isinstance(expected_output, str)
                else expected_output
            )
            expected_cases = expected_parsed.get("aggregated_test_cases", [])
        except (json.JSONDecodeError, AttributeError, TypeError):
            expected_cases = []

    # Return immediate failure if there was an error
    if has_error:
        return Evaluation(
            name="test_case_generation",
            value=0,
            comment=f"Generation failed: {error_msg}",
        )

    # Return failure if no test cases generated
    if not generated_cases:
        return Evaluation(
            name="test_case_generation",
            value=0,
            comment="No test cases were generated",
        )

    # Extract descriptions only (ignoring the 'present' field)
    expected_descriptions = [
        tc.get("description", "") for tc in expected_cases if isinstance(tc, dict)
    ]

    if not expected_descriptions:
        return Evaluation(
            name="test_case_generation",
            value=0,
            comment="No expected test cases found",
        )

    # Format test cases for evaluation
    generated_text = "\n".join(
        f"{i + 1}. {case}"
        if isinstance(case, str)
        else f"{i + 1}. {case.id}: {case.description}"
        for i, case in enumerate(generated_cases)
    )
    expected_text = "\n".join(
        f"{i + 1}. {desc}" for i, desc in enumerate(expected_descriptions)
    )

    # Create evaluation prompt
    evaluation_prompt = f"""You are evaluating the quality of generated test cases for a requirement.

<generated_test_cases>
{generated_text}
</generated_test_cases>

<expected_test_cases>
{expected_text}
</expected_test_cases>

<evaluation_criteria>
Compare the generated test cases against the expected test cases and assess:

1. **Semantic Coverage**: For each expected test case, determine if there is a generated test case that covers the same testing scenario (even if worded differently)
2. **Completeness**: How many of the expected test cases are covered by the generated test cases?
3. **Precision**: Are the generated test cases relevant and accurate?

IMPORTANT:
- Focus on semantic meaning, not exact wording
- A generated test case matches an expected one if it tests the same condition/scenario
- Count how many expected test cases have a semantic match in the generated set
- Ignore extra test cases that aren't in the expected set (they don't reduce the score)
- The 'present' field in expected output should be ignored - only descriptions matter
</evaluation_criteria>

<scoring_rule>
Calculate the coverage score as:
coverage_score = (number of expected test cases with semantic match / total expected test cases) * 10

For example:
- If 22 out of 22 expected test cases are covered: score = 10/10
- If 20 out of 22 expected test cases are covered: score = 9.1/10
- If 15 out of 22 expected test cases are covered: score = 6.8/10
- If 0 out of 22 expected test cases are covered: score = 0/10

Return your response in JSON format:
{{
    "total_expected": number_of_expected_test_cases,
    "matched_count": number_of_matched_expected_test_cases,
    "coverage_percentage": percentage_of_coverage,
    "matches": [
        {{
            "expected_index": index_in_expected_list,
            "generated_index": index_in_generated_list_or_null,
            "is_match": true_or_false,
            "reason": "brief explanation"
        }}
    ],
    "analysis": "Overall analysis of test case quality and coverage",
    "score": final_score_0_to_10
}}
</scoring_rule>"""

    try:
        # Call LLM for evaluation
        response = llm.invoke(evaluation_prompt)
        response_text = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )

        # Parse JSON response
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        result = json.loads(response_text)

        score = result.get("score", 0)
        analysis = result.get("analysis", "")
        total_expected = result.get("total_expected", len(expected_descriptions))
        matched_count = result.get("matched_count", 0)
        coverage_percentage = result.get("coverage_percentage", 0)

        comment = f"""Test Case Generation Assessment:
- Total Expected Test Cases: {total_expected}
- Matched Test Cases: {matched_count}
- Coverage: {coverage_percentage:.1f}%
- Generated Count: {len(generated_cases)}

{analysis}"""

        return Evaluation(
            name="test_case_generation",
            value=score,
            comment=comment,
        )

    except Exception as e:
        # Return error evaluation if something goes wrong
        return Evaluation(
            name="test_case_generation",
            value=0,
            comment=f"Evaluation failed: {e!s}",
        )
