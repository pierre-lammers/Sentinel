"""Experiment evaluators for requirement evaluation using Langfuse datasets."""

import json
import os
from typing import Any

from langchain_mistralai import ChatMistralAI
from langfuse import Evaluation
from pydantic import SecretStr


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
    # Initialize LLM for evaluation using Mistral
    api_key = os.getenv("MISTRAL_API_KEY")
    llm = ChatMistralAI(
        model_name="mistral-large-latest",
        api_key=SecretStr(api_key) if api_key else None,
        temperature=0,
    )

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
    evaluation_prompt = f"""You are evaluating test case status accuracy. Compare the generated output against reference test cases.

<generated_output>
{output_str}
</generated_output>

<reference_test_cases>
{expected_str}
</reference_test_cases>

<evaluation_criteria>
1. Identify test cases that are common between reference_test_cases and generated_output
2. For each common test case, compare the "present" status field
3. Count how many common test cases have identical "present" status

A test case is considered "common" if:
- The same test scenario is described (exact wording not required)
- The same condition being tested is covered
- Equivalent formulations are acceptable (e.g., "NTZ inactive" = "NTZ area is not active")

Calculate the percentage: (test cases with matching present status / TOTAL reference test cases) × 100

IMPORTANT: The denominator is the TOTAL number of reference test cases, NOT the number of common test cases.
Example: If there are 15 reference test cases, 8 are found in generated output, and 6 have matching present status, the percentage is 6/15 = 40%
</evaluation_criteria>

<instructions>
1. List all test cases from reference_test_cases
2. For each reference test case, check if it exists in generated_output (FOUND or NOT FOUND)
3. For FOUND test cases (common test cases), compare the "present" status
4. Mark each common test case as MATCH (same present status) or MISMATCH (different present status)
5. Calculate the percentage of MATCH test cases among common test cases
6. Apply the scoring rule below
</instructions>

<scoring_rule>
First list each reference test case and mark it as:
- NOT FOUND (not in generated output)
- MATCH (found in generated output with same "present" status)
- MISMATCH (found in generated output but different "present" status)

Then calculate:
- Total reference test cases (all test cases in reference)
- Common test cases (MATCH + MISMATCH)
- Matching test cases (only MATCH)
- Percentage = (MATCH / TOTAL reference test cases) × 100

Score between 1 and 10 based on percentage of matching present status:
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
    "analysis": "Your detailed analysis of each test case with NOT FOUND/MATCH/MISMATCH status",
    "common_count": number_of_common_test_cases,
    "matching_count": number_of_test_cases_with_same_present_status,
    "total_reference_count": total_reference_test_cases,
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

        # Fix unescaped newlines within string values
        def fix_json_newlines(text: str) -> str:
            """Escape literal newlines only within quoted strings."""
            result = []
            in_string = False
            i = 0
            while i < len(text):
                char = text[i]
                # Handle escaped characters
                if char == "\\" and i + 1 < len(text):
                    result.append(char)
                    result.append(text[i + 1])
                    i += 2
                    continue
                # Toggle string state on unescaped quotes
                elif char == '"':
                    in_string = not in_string
                    result.append(char)
                # Escape newlines only inside strings
                elif char == "\n" and in_string:
                    result.append("\\n")
                else:
                    result.append(char)
                i += 1
            return "".join(result)

        response_text = fix_json_newlines(response_text)
        result = json.loads(response_text)

        score = result.get("score", 0)
        percentage = result.get("percentage", 0)
        common_count = result.get("common_count", 0)
        matching_count = result.get("matching_count", 0)
        total_reference_count = result.get("total_reference_count", 0)
        analysis = result.get("analysis", "")

        comment = (
            f"Status Match: {matching_count}/{total_reference_count} "
            f"({percentage:.1f}%) - Common: {common_count}\n{analysis}"
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
