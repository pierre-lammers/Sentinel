"""Experiment evaluators for requirement evaluation using Langfuse datasets."""

import json
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse import Evaluation


def test_case_coverage_evaluator(
    *, output: Any, expected_output: Any, **kwargs: Any
) -> Evaluation:
    """LLM-as-judge evaluator for test case coverage.

    Evaluates how many reference test cases are present in the generated output.

    Args:
        output: The generated output from the task
        expected_output: The reference test cases
        **kwargs: Additional keyword arguments

    Returns:
        Evaluation object with score and reasoning
    """
    # Initialize LLM for evaluation (using Gemini 2.0 Flash)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)

    # Extract aggregated_test_cases from output and expected_output
    if isinstance(output, dict):
        output_data = output.get("aggregated_test_cases", output)
    else:
        # If output is a string, try to parse it as JSON
        try:
            output_parsed = json.loads(output)
            output_data = output_parsed.get("aggregated_test_cases", output_parsed)
        except (json.JSONDecodeError, AttributeError):
            output_data = output

    if isinstance(expected_output, dict):
        expected_data = expected_output.get("aggregated_test_cases", expected_output)
    else:
        # If expected_output is a string, try to parse it as JSON
        try:
            expected_parsed = json.loads(expected_output)
            expected_data = expected_parsed.get(
                "aggregated_test_cases", expected_parsed
            )
        except (json.JSONDecodeError, AttributeError):
            expected_data = expected_output

    # Convert to JSON strings for the prompt
    output_str = (
        json.dumps(output_data, indent=2)
        if not isinstance(output_data, str)
        else output_data
    )
    expected_str = (
        json.dumps(expected_data, indent=2)
        if not isinstance(expected_data, str)
        else expected_data
    )

    # Create evaluation prompt
    evaluation_prompt = f"""You are evaluating test case coverage. Compare the generated output against reference test cases.

<generated_output>
{output_str}
</generated_output>

<reference_test_cases>
{expected_str}
</reference_test_cases>

<evaluation_criteria>
Count how many test cases from reference_test_cases are present in generated_output.

A test case is considered "present" if:
- The same test scenario is described (exact wording not required)
- The same condition being tested is covered
- Equivalent formulations are acceptable (e.g., "NTZ inactive" = "NTZ area is not active")

Calculate the percentage: (FOUND / total reference tests) × 100
</evaluation_criteria>

<instructions>
1. List all test cases from reference_test_cases
2. For each reference test case, check if it exists in generated_output (FOUND or MISSING)
3. Calculate the percentage of FOUND test cases
4. Apply the scoring rule below
</instructions>

<scoring_rule>
First list each reference test case and mark it as FOUND or MISSING. Then calculate the percentage of found test cases and explain your scoring.
Score between 1 and 10 based on percentage of reference tests found:
- 0-9% = 1
- 10-19% = 2
- 20-29% = 3
- 30-39% = 4
- 40-49% = 5
- 50-59% = 6
- 60-69% = 7
- 70-79% = 8
- 80-89% = 9
- 90-100% = 10

Return your response in JSON format:
{{
    "analysis": "Your detailed analysis of each test case",
    "found_count": number_of_found_test_cases,
    "total_count": total_reference_test_cases,
    "percentage": calculated_percentage,
    "score": final_score_1_to_10
}}
</scoring_rule>"""

    try:
        # Call LLM for evaluation
        response = llm.invoke(evaluation_prompt)
        # Ensure response content is a string
        response_text = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )

        # Parse JSON response
        # Try to extract JSON from markdown code blocks if present
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
        percentage = result.get("percentage", 0)
        found_count = result.get("found_count", 0)
        total_count = result.get("total_count", 0)
        analysis = result.get("analysis", "")

        comment = (
            f"Coverage: {found_count}/{total_count} ({percentage:.1f}%)\n{analysis}"
        )

        return Evaluation(
            name="test_case_coverage",
            value=score,
            comment=comment,
        )

    except Exception as e:
        # Return error evaluation if something goes wrong
        return Evaluation(
            name="test_case_coverage",
            value=0,
            comment=f"Evaluation failed: {e!s}",
        )
