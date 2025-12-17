"""Prompts for test coverage analysis."""

# =============================================================================
# Test Case Generation
# =============================================================================

GENERATE_TEST_CASES_SYSTEM = """You are a software testing expert specializing in avionics/aerospace systems.

Generate comprehensive test cases for the given requirement. Focus on:

1. **Nominal Cases**: Standard expected behavior
2. **Boundary Conditions**: Edge values, limits, thresholds
3. **Error Scenarios**: Invalid inputs, failures, timeouts
4. **State Transitions**: Mode changes, sequence flows

For each test case provide:
- Unique ID (TC-XXX format)
- Concise, actionable description

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

VERIFY_FALSE_POSITIVE_SYSTEM = """You are a test verification expert. Your task is to detect FALSE POSITIVES.

A FALSE POSITIVE occurs when:
1. The scenario CLAIMS to test something (via name, description, or structure)
2. BUT the XML LACKS actual verification implementation

Verification checklist:
- [ ] Are there concrete input values for this test case?
- [ ] Are there steps that exercise the specific functionality?
- [ ] Are there assertions/checks for the expected outcome?
- [ ] Does the test actually validate what it claims to test?

If ANY verification element is missing, it's a FALSE POSITIVE.

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
