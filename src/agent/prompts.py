"""Prompts for test coverage analysis."""

from typing import Any

# =============================================================================
# Test Case Generation
# =============================================================================

GENERATE_TEST_CASES_SYSTEM = """You are a software testing expert specializing in avionics/aerospace systems.

Generate comprehensive test cases for the given requirement. For each condition mentioned:

1. **Nominal Case**: All conditions satisfied → expected behavior (usually NO alert)
2. **Condition NOT Satisfied**: For EACH condition Cn AND its sub-conditions, test when NOT satisfied
3. **State Transitions IN**: Cn transitions from NOT satisfied to satisfied
4. **State Transitions OUT**: Cn transitions from satisfied to NOT satisfied
5. **Boundary Cases**: For thresholds/limits, test at EXACTLY the boundary value

IMPORTANT - Split conditions with multiple aspects:
- If a condition has sub-conditions (e.g., "track in ARRIVAL phase WITH valid time-to-threshold"), test EACH sub-condition separately
- Example: C2 = "ARRIVAL phase + valid TTT" → generate: "C2: phase != ARRIVAL" AND "C2: TTT invalid"

For threshold conditions (delays, separations, etc.), generate:
- Value < threshold (NOT satisfied)
- Value = EXACTLY threshold (BOUNDARY)
- Value > threshold (satisfied)

For each test case provide:
- Unique ID (TC-XXX format)
- Description with: condition reference (C1, C2...), sub-condition if any, test type, expected outcome

Return ONLY valid JSON: {"test_cases": [{"id": "TC-001", "description": "..."}]}"""

GENERATE_TEST_CASES_USER = """Requirement: {req_name}

Description:
{requirement_description}"""


# =============================================================================
# Coverage Identification (Agent 1)
# =============================================================================
IDENTIFY_COVERAGE_SYSTEM = (
    """You are a test coverage analyst for avionics XML test scenarios."""
)

IDENTIFY_COVERAGE_USER = """
Requirement: {req_name}
Scenario: {scenario_name}

Scenario Content:
{scenario_content}

Test Cases to Check:
{test_cases_list}

Analyze the scenario content above to understand what is really being tested.
Pay particular attention to the code and not the description, which may be incorrect.
For each test case in the list, determine if it is present (covered) in the scenario.
"""


# =============================================================================
# Helper functions
# =============================================================================


def format_test_cases_list(test_cases: list[Any]) -> str:
    """Format test cases as a bullet list.

    Args:
        test_cases: List of Pydantic models with 'id' and 'description' attributes

    Returns:
        Formatted string with bullet points
    """
    return "\n".join(f"- {tc.id}: {tc.description}" for tc in test_cases)
