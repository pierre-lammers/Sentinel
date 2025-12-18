"""Experiment evaluators for requirement evaluation using Langfuse datasets."""

import json
import os
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse import Evaluation

from src.langfuse.utils import retrieve_prompt


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
    # Initialize LLM for evaluation using Google Gemini
    api_key = os.getenv("GOOGLE_API_KEY")
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=api_key,
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

    variables = {
        "output_str": output_str,
        "expected_str": expected_str
    }

    evaluation_prompt = retrieve_prompt("Evaluator - Coverage", **variables)

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
