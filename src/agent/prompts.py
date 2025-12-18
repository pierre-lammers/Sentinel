"""Prompts for test coverage analysis."""

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

IDENTIFY_COVERAGE_SYSTEM = """You are a test coverage analyst for XML test scenarios.

Analyze the XML scenario and determine which test cases have ACTUAL test implementation.

COVERAGE CRITERIA - A test case is PRESENT (covered) ONLY if the XML contains:
1. **Test data setup** relevant to the test case (input values, conditions)
2. **Verification steps** that check the expected outcome
3. **Assertions or checks** (explicit or implicit in the XML structure)

A test case is NOT PRESENT if:
- Only mentioned in comments/descriptions without actual test steps
- No verification of the expected outcome
- Missing required test data for that specific case

For each test case, provide:
- present: true/false based on actual coverage
- evidence: Quote the XML element/section that proves coverage (or empty if not present)

Return JSON: {"test_cases": [{"id": "TC-001", "description": "...", "present": true, "evidence": "<step>..."}]}"""

IDENTIFY_COVERAGE_USER = """Requirement: {req_name}
Scenario: {scenario_name}

Test Cases to check:
{test_cases_list}

Scenario XML:
```xml
{scenario_content}
```"""


# =============================================================================
# False Positive Verification (Agent 2)
# =============================================================================

VERIFY_FALSE_POSITIVE_SYSTEM = """You are a test verification expert for avionics XML test scenarios.

Your task is to verify if a test case has ACTUAL implementation in the XML.

IMPORTANT: This is an avionics XML test format with specific verification patterns:

VALID VERIFICATION ELEMENTS in this format:
1. <Alerts alertType="..." alertGenerated="true/false"/> - This IS an assertion
2. <TestResult> with resultDescription - This documents expected behavior
3. <TrackUpdate> with flight data - This provides concrete input values
4. <SystemStatusUpdate>, <DatapageAMANUpdate> - These configure test conditions
5. Any XML element that sets up or verifies conditions IS valid test content

A test case is PROPERLY IMPLEMENTED if:
- Input conditions are set up via XML elements (TrackUpdate, SystemStatusUpdate, etc.)
- Expected outcome is documented (TestResult description)
- Alert assertion exists (<Alerts alertGenerated="true/false"/>)

A test case is a FALSE POSITIVE ONLY if:
- The scenario mentions the test case but has NO relevant XML elements at all
- The XML completely lacks any setup or verification for that specific condition

IMPORTANT: Be LENIENT. If the XML has relevant data and assertions, the test IS implemented.

Return JSON:
{
  "is_false_positive": true/false,
  "reason": "Detailed explanation with XML evidence",
  "missing_elements": ["list", "of", "missing", "elements"]
}"""

VERIFY_FALSE_POSITIVE_USER = """Requirement: {req_name}
Scenario: {scenario_name}

Test Case to verify:
- ID: {test_case_id}
- Description: {test_case_description}
- Claimed coverage evidence: {evidence}

Scenario XML:
```xml
{scenario_content}
```

Verify if this test case has COMPLETE verification in the XML, or is it a false positive?"""


# =============================================================================
# Helper functions
# =============================================================================


def format_test_cases_list(test_cases: list[str]) -> str:
    """Format test cases as a bullet list."""
    return "\n".join(f"- {tc}" for tc in test_cases)
