# Create New Requirement Test Suite Command

Generates a complete test suite for a new SKYRADAR requirement with comprehensive test coverage analysis, test scenarios, and coverage matrix documentation.

## Usage

```
/create-req-test-suite <REQ-CODE>
```

## Examples

```
/create-req-test-suite STCA-042
/create-req-test-suite MSAW-026
/create-req-test-suite RWY-001
```

## What This Command Does

This command launches a specialized agent that will:

1. Extract the requirement specification from `SRS.txt`
2. Identify all N conditions that must be tested
3. Create the folder structure: `TS_<REQ-CODE>/`
4. Generate 4 test scenario files with proper XML structure
5. Create the comprehensive `CLAUDE.md` coverage analysis
6. Ensure test_04 includes an intentional false positive for AI detection

## Implementation

You are launching the requirement-test-suite-generator agent with the requirement code: **{{arg1}}**

Use the Task tool with subagent_type="general-purpose" to execute the following optimized prompt:

```xml
<task>
  <objective>
    Generate a complete, production-ready test suite for requirement SKYRADAR-{{arg1}}
    with comprehensive test scenarios, coverage analysis, and intentional quality issues
    for AI system evaluation.
  </objective>

  <context>
    <requirement_code>SKYRADAR-{{arg1}}</requirement_code>
    <base_path>/Users/pierrelammers/Desktop/evaluation</base_path>
    <srs_file>/Users/pierrelammers/Desktop/evaluation/SRS.txt</srs_file>
    <reference_suite>/Users/pierrelammers/Desktop/evaluation/TS_MSAW-025</reference_suite>
    <domain>Air Traffic Control (SKYRADAR system)</domain>
    <test_framework>XML-based scenario simulation with state transitions</test_framework>
  </context>

  <instructions>
    <step_one>
      <name>Extract Requirement Specification</name>
      <process>
        1. Read /Users/pierrelammers/Desktop/evaluation/SRS.txt completely
        2. Locate the requirement with code "SKYRADAR-{{arg1}}"
        3. Extract and document:
           - Full requirement title/description
           - ALL conditions (typically 5-7 bullet points)
           - Parameter names, values, and thresholds
           - Safety impact classification
           - Verification method and level
        4. Assign sequential IDs to each condition: C1, C2, C3, ... CN
      </process>
      <output_format>
        REQUIREMENT EXTRACTION:
        - Code: SKYRADAR-{{arg1}}
        - Title: [Full title]
        - Total Conditions: N
        - Conditions Table:
          | ID | Condition Text | Parameter | Value/Range |
          |----|----|----|----|
          | C1 | [Full text] | [param] | [value] |
      </output_format>
    </step_one>

    <step_two>
      <name>Design Coverage Strategy</name>
      <thinking>
        Think through which conditions will be tested explicitly vs implicitly:
        - How can I distribute N conditions across 4 tests?
        - Which 3-4 conditions should be explicitly tested (✅)?
        - Which 3-4 conditions should be left as gaps (❌)?
        - How can test_04 have a plausible but flawed claim?

        Design the false positive by choosing one of:
        1. Missing state change: Claim transition happens, but XML element is missing
        2. Wrong assertion: Assert alert generated when state should prevent it
        3. Incomplete OR logic: Test only one half of an OR condition
        4. Redundancy: Test a condition already covered elsewhere
      </thinking>
      <constraints>
        - Coverage should be 3-4 explicit tests (✅) and 3-4 gaps (❌)
        - Each valid test (01, 02, 03) must have exactly 1 condition marked ✅
        - test_04 must have a hidden flaw that appears correct initially
        - Coverage matrix must be accurate and match actual XML files
      </constraints>
    </step_two>

    <step_three>
      <name>Generate Valid Test Scenarios (test_01, test_02, test_03)</name>
      <xml_template>
        &lt;?xml version="1.0" encoding="UTF-8"?&gt;
        &lt;ScenarioDefinition scenarioId="scenario_SKYRADAR-{{arg1}}-[NN]"
                            scenarioDescription="[CLEAR ONE-LINE DESCRIPTION OF TEST OBJECTIVE]"&gt;
          &lt;!-- SETUP PHASE: Establish baseline system state --&gt;
          &lt;FlightPlanUpdate time="0"&gt;
            &lt;FlightPlan trackNum="1" ... /&gt;
          &lt;/FlightPlanUpdate&gt;

          &lt;IdentUpdate time="1000"&gt;
            &lt;Ident trackNum="1" ... /&gt;
          &lt;/IdentUpdate&gt;

          &lt;!-- CONFIG PHASE: Set system parameters and configuration --&gt;
          &lt;SystemConfigUpdate time="2000"&gt;
            [All relevant system parameters, thresholds, and status values]
          &lt;/SystemConfigUpdate&gt;

          &lt;!-- BASELINE PHASE: Initial state where condition is NOT met --&gt;
          &lt;TrackUpdates time="5000"&gt;
            [Track position/state where alert should NOT be generated]
          &lt;/TrackUpdates&gt;

          &lt;TestResult resultTimeInMilliSec="5000"
                      resultDescription="Baseline: [Specific state description], alert should NOT be generated"&gt;
            &lt;Alerts alertType="[ALERT_TYPE]" trackNum="1" alertGenerated="false"/&gt;
          &lt;/TestResult&gt;

          &lt;!-- TRANSITION PHASE: Change condition to meet requirements --&gt;
          &lt;SystemStatusUpdate time="10000"&gt;
            [Status or configuration change that should trigger alert]
          &lt;/SystemStatusUpdate&gt;

          &lt;TrackUpdates time="12000"&gt;
            [Track state confirming the condition is now met]
          &lt;/TrackUpdates&gt;

          &lt;!-- VERIFICATION PHASE: Verify alert generation --&gt;
          &lt;TestResult resultTimeInMilliSec="15000"
                      resultDescription="Condition triggered: [Specific state description], alert SHOULD be generated"&gt;
            &lt;Alerts alertType="[ALERT_TYPE]" trackNum="1" alertGenerated="true"/&gt;
          &lt;/TestResult&gt;
        &lt;/ScenarioDefinition&gt;
      </xml_template>
      <validation_rules>
        - Must follow: baseline state → condition triggered → alert generation
        - Assertions must match actual XML state at that time
        - Use realistic domain values (altitudes in feet, speeds in knots, etc.)
        - Each test should focus on ONE primary condition
        - All other conditions should be implicitly satisfied (🟡)
      </validation_rules>
    </step_three>

    <step_four>
      <name>Generate False Positive Test (test_04)</name>
      <objective>
        Create a test that APPEARS to test a valid condition but has hidden flaws
        that would not be immediately obvious to a human reviewer. The test should
        pass when run, but the assertions do not validate what the description claims.
      </objective>
      <false_positive_example>
        Technique: Missing State Change
        - Claim: "Test validates system transition from STANDBY to OPERATIONAL"
        - Description: "Verifies MSAW alert generation when MSAW system becomes OPERATIONAL"
        - Reality: The XML is missing the SystemStatusUpdate tag that changes status
        - Last status value: STANDBY (from initial SystemConfigUpdate)
        - Assertion: alertGenerated="true" (expecting alert due to OPERATIONAL status)
        - Problem: Status is still STANDBY, so assertion validates incorrect behavior
        - Why it passes: The XML syntax is valid, and the assertion technically passes
        - Why it's wrong: The test doesn't actually test the transition it claims to test
      </false_positive_example>
      <guidelines>
        - Make the description sound plausible
        - Hide the flaw in a realistic way (missing tag, incomplete transition)
        - The test must pass (valid XML, no runtime errors)
        - The assertion must be syntactically correct but logically wrong
        - Document the flaw thoroughly in CLAUDE.md
      </guidelines>
    </step_four>

    <step_five>
      <name>Create CLAUDE.md Coverage Analysis</name>
      <template>
        # Test Coverage Analysis - SKYRADAR-{{arg1}}

        ## Requirement Summary

        **SKYRADAR-{{arg1}}**: [Full title]

        SKYRADAR shall [primary behavior statement] if ALL of the following conditions are met:

        ### Conditions List

        | ID | Condition Description | Parameter/Value |
        |----|----------------------|-----------------|
        | **C1** | [Full condition text with details] | [Technical parameter/value] |
        | **C2** | [Full condition text with details] | [Technical parameter/value] |
        | ... | ... | ... |

        ## Test Coverage Matrix

        | Test ID | Test Name | C1 | C2 | C3 | ... | CN | Status | Notes |
        |---------|-----------|----|----|----|----|----|----|--------|
        | **test_01** | [Descriptive name] | ✅ | 🟡 | 🟡 | ... | 🟡 | Complete | [One-sentence description] |
        | **test_02** | [Descriptive name] | 🟡 | ✅ | 🟡 | ... | 🟡 | Complete | [One-sentence description] |
        | **test_03** | [Descriptive name] | 🟡 | 🟡 | ✅ | ... | 🟡 | Complete | [One-sentence description] |
        | **test_04** | [Descriptive name] ⚠️ | ❌ | 🟡 | 🟡 | ... | 🟡 | **FALSE POSITIVE** | [Specific flaw description] |

        ### Legend
        - ✅ **Explicitly tested**: Test directly validates this condition with positive/negative cases
        - 🟡 **Implicitly satisfied**: Condition is set correctly in setup but never varied or validated
        - ❌ **Not covered**: Condition is never mentioned, set, or tested in this test
        - ⚠️ **False positive**: Test has intentional errors or inconsistencies

        ## Coverage Analysis

        ### Tested Conditions (3/N)

        #### ✅ C1: [Condition title]
        - **Test**: test_01/scenario_SKYRADAR-{{arg1}}-01.xml
        - **Coverage**: Complete
        - **Test scenarios**:
          - Baseline: [Description of state where alert NOT generated]
          - Triggered: [Description of state where alert IS generated]
          - Expected: [Summary of expected behavior]

        [Similar format for C2, C3...]

        ### Untested Conditions (4/N) - AI SHOULD DETECT THESE GAPS

        #### ❌ C4: [Condition title]
        - **Status**: NOT TESTED
        - **Gap**: [Specific explanation of what's missing]
        - **Current tests**: [What do existing tests actually test instead?]
        - **Required scenarios**: [What tests would be needed?]
        - **AI Detection Goal**: [What should AI identify?]

        [Similar format for other untested conditions...]

        ## Test Quality Issues

        ### ⚠️ FALSE POSITIVE DETECTED: test_04

        **Test ID**: test_04/scenario_SKYRADAR-{{arg1}}-04.xml
        **Claimed Objective**: [What the test claims to validate]
        **Actual Problem**: [Why this claim is incorrect]

        #### Issues Identified

        1. **[Issue type]**:
           - The test claims: [The description states]
           - **MISSING**: [What XML element is missing or wrong]
           - Result: [What actually happens instead]

        2. **[Issue type]**:
           - [Similar structure...]

        #### What the AI Should Detect

        ```
        ISSUE: FALSE POSITIVE in test_04
        - Description claims: "[the claim]"
        - XML shows: [actual state from lines X-Y]
        - Assertion: [assertion at line Z]
        - Expected: [what should actually happen]
        - SEVERITY: HIGH - Test validates incorrect behavior
        ```

        ## Expected AI Analysis Output

        A competent AI system should detect:

        ```
        REQUIREMENT: SKYRADAR-{{arg1}}
        Total Conditions: N
        Tested Conditions: 3 (X%)
        Untested Conditions: 4 (Y%)

        COVERAGE GAPS DETECTED:
        1. Condition CX: [Description]
        2. Condition CY: [Description]
        ...

        FALSE POSITIVES DETECTED:
        1. test_04: [Specific issues and evidence]

        RECOMMENDATION:
        - [Actionable fix or additional tests needed]
        ```
      </template>
    </step_five>

    <step_six>
      <name>Create Folder Structure and Files</name>
      <structure>
        Create directory: TS_{{arg1}}/

        TS_{{arg1}}/
        ├── CLAUDE.md                              [Generated in Step 5]
        ├── system_dataset/
        │   ├── [reference-config-01].xml         [Config files used by tests]
        │   └── [reference-config-02].xml
        ├── test_01/
        │   └── scenario_SKYRADAR-{{arg1}}-01.xml  [Valid test from Step 3]
        ├── test_02/
        │   └── scenario_SKYRADAR-{{arg1}}-02.xml  [Valid test from Step 3]
        ├── test_03/
        │   └── scenario_SKYRADAR-{{arg1}}-03.xml  [Valid test from Step 3]
        └── test_04/
            └── scenario_SKYRADAR-{{arg1}}-04.xml  [False positive from Step 4]
      </structure>
    </step_six>
  </instructions>

  <validation_checklist>
    ✅ All N conditions extracted from SRS.txt and assigned IDs
    ✅ Requirement summary and conditions table accurate
    ✅ Coverage matrix shows 3-4 conditions as ✅ (explicitly tested)
    ✅ Coverage matrix shows 3-4 conditions as ❌ (untested gaps)
    ✅ test_01, test_02, test_03 have valid XML syntax
    ✅ test_01, test_02, test_03 follow baseline → triggered → verified pattern
    ✅ test_01, test_02, test_03 assertions match actual XML states
    ✅ test_04 has hidden flaw (missing element or wrong assertion)
    ✅ test_04 flaw is documented with specific evidence in CLAUDE.md
    ✅ CLAUDE.md follows exact template structure
    ✅ All untested conditions have specific gap explanations
    ✅ Expected AI analysis output is realistic and detailed
    ✅ Folder structure matches exact naming conventions
  </validation_checklist>

  <output_specification>
    After completing all steps, provide:

    1. **Generation Summary**
       - Requirement: SKYRADAR-{{arg1}}
       - Total conditions: N
       - Coverage: X/N explicitly tested

    2. **Coverage Matrix**
       - Display the matrix showing ✅, 🟡, ❌ for each condition

    3. **Files Created**
       - List: TS_{{arg1}}/CLAUDE.md
       - List: TS_{{arg1}}/test_01/scenario_...
       - List: TS_{{arg1}}/test_02/scenario_...
       - List: TS_{{arg1}}/test_03/scenario_...
       - List: TS_{{arg1}}/test_04/scenario_...

    4. **False Positive Evidence**
       - Test: test_04
       - Issue: [Specific flaw]
       - Location: [Filename and description]

    5. **Next Steps**
       - Suggestion: Use `/validate-coverage TS_{{arg1}}` to verify accuracy
       - Suggestion: Use AI analysis system to detect coverage gaps and false positive
  </output_specification>
</task>
```

---

## Advanced Options

To customize the generated test suite:

- **Coverage percentage**: Generate with 2/7, 3/7, or 4/7 explicit coverage
- **Complexity**: Simple (4 conditions) vs. Complex (7+ conditions)
- **Domain**: Adapt to other SKYRADAR subsystems (STCA, RWY, APP, etc.)
- **False positive type**: Missing state change, wrong assertion, redundancy, OR condition incomplete

## Integration with Validation

After generating a test suite, validate it with:

```
/validate-coverage TS_{{arg1}}
```

This will verify that all claims in CLAUDE.md match actual test implementations and detect any undocumented issues.

## Examples in Repository

Refer to existing test suites for reference:
- `TS_STCA-041/`: STCA conflict suppression (7 conditions, 3/7 tested)
- `TS_MSAW-025/`: Minimum safe altitude warnings (7 conditions, 3/7 tested)
