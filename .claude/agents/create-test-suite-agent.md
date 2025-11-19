# Create Test Suite Agent

This agent generates complete test suites for SKYRADAR requirements with comprehensive coverage analysis, including intentional quality issues for AI evaluation.

## Agent Purpose

Generate production-ready test suite folders with:
- 4 test scenario XML files following SKYRADAR domain patterns
- Complete CLAUDE.md coverage analysis and documentation
- Coverage matrix with explicit testing (✅), implicit coverage (🟡), and gaps (❌)
- Intentional false positive in test_04 for AI detection capability

## Usage

This agent is launched by the `/create-req-test-suite` command and should NOT be called directly.

The command structure is:

```
/create-req-test-suite <REQ-CODE>
```

Example:
```
/create-req-test-suite MSAW-026
```

## Agent Execution Flow

### Input

- `requirement_code`: The SKYRADAR requirement code (e.g., "MSAW-026", "STCA-043")
- `srs_file`: Path to the SRS.txt containing all requirement specifications
- `base_path`: Base directory for file creation

### Processing Steps

1. **Extract Requirement** → Parse SRS.txt for SKYRADAR-[REQ-CODE]
2. **Identify Conditions** → Extract all N conditions from requirement
3. **Plan Coverage** → Design which conditions will be tested
4. **Generate Tests** → Create 4 valid scenario XML files
5. **Create Documentation** → Generate CLAUDE.md with coverage analysis
6. **Verify Structure** → Validate folder structure and file relationships

### Output

- Created folder: `TS_<REQ-CODE>/`
- Generated files:
  - `TS_<REQ-CODE>/CLAUDE.md`
  - `TS_<REQ-CODE>/system_dataset/[configs].xml`
  - `TS_<REQ-CODE>/test_01/scenario_SKYRADAR-<REQ-CODE>-01.xml`
  - `TS_<REQ-CODE>/test_02/scenario_SKYRADAR-<REQ-CODE>-02.xml`
  - `TS_<REQ-CODE>/test_03/scenario_SKYRADAR-<REQ-CODE>-03.xml`
  - `TS_<REQ-CODE>/test_04/scenario_SKYRADAR-<REQ-CODE>-04.xml`

## Optimized Prompt for Claude

The following prompt is used internally by this agent. It demonstrates best practices:

### Prompt Structure

```xml
<task>
  <objective>[Clear goal statement]</objective>
  <context>[Reference materials and constraints]</context>
  <instructions>[Step-by-step guidance]</instructions>
  <thinking>[Chain of thought structure]</thinking>
  <output_format>[Expected structure]</output_format>
  <validation>[Quality criteria]</validation>
</task>
```

### Key Prompt Engineering Techniques Used

1. **XML Tagging** - Clear hierarchical structure separates:
   - Objective (what needs to be done)
   - Context (reference materials, constraints)
   - Instructions (step-by-step process)
   - Thinking (reasoning process)
   - Output format (expected structure)
   - Validation (quality criteria)

2. **Clarity & Directiveness**:
   - Starts with unambiguous objective
   - Uses imperative language
   - Provides specific, measurable criteria

3. **Few-Shot Examples**:
   - References existing test suites (TS_MSAW-025, TS_STCA-041)
   - Shows XML structure with actual examples
   - Demonstrates coverage matrix format

4. **Chain of Thought**:
   - Explicit `<thinking>` section
   - Step-by-step reasoning guidance
   - Intermediate checkpoints

5. **Structured Output**:
   - Clear template for each file type
   - Precise specifications for coverage matrix
   - Detailed format for false positive documentation

### Constraint Handling

The prompt explicitly handles:

- **Requirement Extraction**: "Read SRS.txt and locate SKYRADAR-[REQ-CODE]"
- **Condition Identification**: "Extract ALL bullet points as conditions C1, C2, ..."
- **Coverage Design**: "3-4 conditions explicitly tested, 3-4 gaps remaining"
- **XML Validation**: "Valid XML syntax with proper state transitions"
- **False Positive Requirement**: "test_04 must have hidden flaw + clear documentation"
- **File Organization**: "Follow exact folder structure with specific naming"

## Template Sections

### Requirement Extraction Template

```
SKYRADAR-[REQ-CODE]: [Title]
SSS: [Reference]
Safety Impact: [true/false]

CONDITIONS EXTRACTED:
C1: [Full text with parameter details]
C2: [Full text with parameter details]
...
CN: [Full text with parameter details]

VERIFICATION DETAILS:
- Total conditions: N
- Method: [Test/Review/etc]
- Level: [RL/SIL/etc]
```

### Coverage Matrix Template

```markdown
| Test ID | Test Name | C1 | C2 | C3 | ... | CN | Status | Notes |
|---------|-----------|----|----|----|----|-------|--------|-------|
| test_01 | [Name] | ✅ | 🟡 | 🟡 | ... | 🟡 | Complete | Tests C1 |
| test_02 | [Name] | 🟡 | ✅ | 🟡 | ... | 🟡 | Complete | Tests C2 |
| test_03 | [Name] | 🟡 | 🟡 | ✅ | ... | 🟡 | Complete | Tests C3 |
| test_04 | [Name] ⚠️ | ❌ | 🟡 | 🟡 | ... | 🟡 | FALSE POSITIVE | [Flaw] |

COVERAGE SUMMARY: 3/N tested, 4/N gaps
```

### XML Test Scenario Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ScenarioDefinition
    scenarioId="scenario_SKYRADAR-[REQ-CODE]-[NN]"
    scenarioDescription="[CLEAR DESCRIPTION OF WHAT THIS TEST VALIDATES]">

  <!-- SETUP PHASE: Establish initial system state -->
  <FlightPlanUpdate time="0">
    <FlightPlan trackNum="1" ... />
  </FlightPlanUpdate>

  <IdentUpdate time="1000">
    <Ident trackNum="1" ... />
  </IdentUpdate>

  <!-- CONFIG PHASE: Set system parameters -->
  <SystemConfigUpdate time="2000">
    [System configuration for this test scenario]
  </SystemConfigUpdate>

  <!-- BASELINE PHASE: Establish baseline state (NO alert) -->
  <TrackUpdates time="5000">
    [Initial track state that should NOT trigger alert]
  </TrackUpdates>

  <TestResult resultTimeInMilliSec="5000"
              resultDescription="[BASELINE VALIDATION]">
    <Alerts alertType="[TYPE]" trackNum="1" alertGenerated="false"/>
  </TestResult>

  <!-- TRANSITION PHASE: Change condition to trigger alert -->
  <SystemStatusUpdate time="10000">
    [Status change that should trigger alert]
  </SystemStatusUpdate>

  <TrackUpdates time="12000">
    [Track state confirming condition change]
  </TrackUpdates>

  <!-- VERIFICATION PHASE: Verify alert generation -->
  <TestResult resultTimeInMilliSec="15000"
              resultDescription="[CONDITION TRIGGERED VALIDATION]">
    <Alerts alertType="[TYPE]" trackNum="1" alertGenerated="true"/>
  </TestResult>
</ScenarioDefinition>
```

### False Positive Techniques

The prompt guides creation of realistic false positives using:

**Technique 1: Missing State Change**
- Claim: "System transitions to OPERATIONAL"
- Reality: Missing `<SystemStatusUpdate>` tag
- Effect: Status remains STANDBY, but assertion expects alert

**Technique 2: Wrong Assertion**
- Claim: "Alert should be generated"
- Reality: State contradicts claim, but assertion says alertGenerated="true"
- Effect: Test passes with wrong expected result

**Technique 3: Incomplete OR Condition**
- Claim: "Tests emergency override condition"
- Reality: Only tests flag=false case, not squawk codes
- Effect: Partial coverage hidden as complete

**Technique 4: Test Redundancy**
- Claim: "Validates new condition"
- Reality: Duplicate of existing test
- Effect: False coverage claim with no new information

## Quality Assurance

The agent validates:

```
✅ Extraction:
   - All N conditions identified from requirement
   - Parameters and values documented
   - Safety impact noted

✅ Test Design:
   - Coverage plan shows 3-4 explicit tests
   - Gaps clearly identified (3-4 conditions)
   - False positive justified

✅ XML Files:
   - Valid XML syntax (well-formed)
   - Proper state transitions (negative → positive → negative)
   - Correct assertions matching actual states
   - Realistic domain values

✅ Documentation:
   - CLAUDE.md follows template structure
   - Coverage matrix is accurate
   - False positive clearly documented with evidence
   - Expected AI analysis output is realistic

✅ Folder Structure:
   - Proper naming convention: TS_[REQ-CODE]
   - All required directories created
   - All required files generated
```

## Integration Points

This agent works with:

- **SRS.txt**: Source of requirement specifications
- **TS_MSAW-025/**: Example test suite for reference
- **TS_STCA-041/**: Example test suite for reference
- **/validate-coverage**: Command to verify generated test suite accuracy
- **test-coverage-validator agent**: Validates test implementation

## Customization Options

The agent can be configured for:

- **Coverage Level**: 2/7, 3/7, 4/7 explicit coverage
- **Condition Count**: 5-7 typical, can be 4-8
- **False Positive Type**: Choose from 4 techniques
- **Domain Specificity**: Adapt XML elements to different SKYRADAR subsystems
- **Complexity**: Simple vs. complex scenarios

## Error Handling

If extraction fails:
- Requirement not found: "SKYRADAR-[REQ-CODE] not found in SRS.txt"
- Invalid format: "Requirement format does not match specification"
- Missing conditions: "Cannot extract all conditions from requirement"

If generation fails:
- File creation: "Cannot create TS_[REQ-CODE] folder"
- XML validation: "Generated XML is not well-formed"
- Documentation: "CLAUDE.md structure is incomplete"

## Best Practices Applied

1. **XML Tagging**: Hierarchical structure for clarity
2. **Few-Shot Examples**: Real examples from existing test suites
3. **Chain of Thought**: Explicit reasoning steps
4. **Clarity**: Unambiguous, direct language
5. **Constraint Specification**: Precise requirements and criteria
6. **Output Structure**: Template-based formatting
7. **Validation**: Explicit quality criteria
8. **Error Handling**: Defined failure modes
