"""Evaluator for RAG requirement retrieval using Langfuse datasets."""

import json
import os
import re
from typing import Any

from langchain_mistralai import ChatMistralAI
from langfuse import Evaluation
from pydantic import SecretStr


def requirement_retrieval_evaluator(
    *, output: Any, expected_output: Any, **kwargs: Any
) -> Evaluation:
    """LLM-as-judge evaluator for RAG requirement retrieval quality.

    Evaluates how well the retrieved requirement matches the expected requirement.

    Args:
        output: The retrieved requirement description
        expected_output: The reference requirement description
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

    # Extract requirement_description from output and expected_output
    if isinstance(output, dict):
        output_text = output.get("requirement_description", "")
    else:
        # If output is a string, try to parse it as JSON
        try:
            output_parsed = json.loads(output)
            output_text = output_parsed.get("requirement_description", output)
        except (json.JSONDecodeError, AttributeError):
            output_text = str(output)

    if isinstance(expected_output, dict):
        expected_text = expected_output.get("requirement_description", "")
    else:
        # If expected_output is a string, try to parse it as JSON
        try:
            expected_parsed = json.loads(expected_output)
            expected_text = expected_parsed.get(
                "requirement_description", expected_output
            )
        except (json.JSONDecodeError, AttributeError):
            expected_text = str(expected_output)

    # Check for errors
    has_error = False
    if isinstance(output, dict) and output.get("errors"):
        has_error = True
        error_msg = "; ".join(output["errors"])
        output_text = f"ERROR: {error_msg}"

    # Create evaluation prompt
    evaluation_prompt = f"""You are evaluating the quality of a retrieved requirement description.

<retrieved_requirement>
{output_text}
</retrieved_requirement>

<expected_requirement>
{expected_text}
</expected_requirement>

<evaluation_criteria>
Compare the retrieved requirement against the expected requirement and assess:
1. Completeness: Does the retrieved requirement contain all key information from the expected requirement?
2. Accuracy: Is the information in the retrieved requirement correct and matches the expected requirement?
3. Relevance: Does the retrieved requirement focus on the correct requirement without extraneous information?
4. Precision: Is the retrieved requirement specific and detailed enough?
</evaluation_criteria>

<scoring_rule>
Score between 1 and 10:
- 10: Perfect match - all information present and accurate
- 8-9: Excellent - minor missing details or slight rewording
- 6-7: Good - most key information present, some missing details
- 4-5: Fair - significant missing information or some inaccuracies
- 2-3: Poor - major missing information or significant inaccuracies
- 1: Failure - completely wrong requirement or error

Return your response in JSON format:
{{
    "completeness": "Assessment of completeness (1-10)",
    "accuracy": "Assessment of accuracy (1-10)",
    "relevance": "Assessment of relevance (1-10)",
    "precision": "Assessment of precision (1-10)",
    "analysis": "Detailed explanation of your evaluation",
    "score": final_score_1_to_10
}}
</scoring_rule>"""

    try:
        # Return immediate failure if there was an error
        if has_error:
            return Evaluation(
                name="requirement_retrieval",
                value=1,
                comment=f"Retrieval failed: {output_text}",
            )

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

        # Try to parse JSON, with fallback for control character issues
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError as parse_error:
            # If parsing fails due to control characters, try to fix them
            # This handles cases where the LLM includes unescaped newlines/tabs
            if "control character" in str(parse_error).lower():
                # Escape control characters in the JSON string values
                # This regex finds string values and escapes control chars within them
                def escape_controls(match: re.Match[str]) -> str:
                    s: str = match.group(0)
                    return (
                        s.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
                    )

                # Match string values in JSON (simplified pattern)
                response_text = re.sub(
                    r'"([^"\\]|\\.)*"', escape_controls, response_text
                )
                result = json.loads(response_text)
            else:
                raise

        score = result.get("score", 0)
        analysis = result.get("analysis", "")
        completeness = result.get("completeness", "N/A")
        accuracy = result.get("accuracy", "N/A")
        relevance = result.get("relevance", "N/A")
        precision = result.get("precision", "N/A")

        comment = f"""Quality Assessment:
- Completeness: {completeness}
- Accuracy: {accuracy}
- Relevance: {relevance}
- Precision: {precision}

{analysis}"""

        return Evaluation(
            name="requirement_retrieval",
            value=score,
            comment=comment,
        )

    except Exception as e:
        # Return error evaluation if something goes wrong
        return Evaluation(
            name="requirement_retrieval",
            value=0,
            comment=f"Evaluation failed: {e!s}",
        )
