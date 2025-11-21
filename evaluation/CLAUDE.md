# SKYRADAR Test Coverage Evaluation Dataset

## Project Overview

This project provides a comprehensive evaluation dataset for validating AI-powered test coverage analysis systems. It demonstrates how to:

1. **Analyze test completeness**: Verify that all conditions in a requirement are properly tested
2. **Detect coverage gaps**: Identify missing test cases for specific requirement conditions
3. **Identify quality issues**: Detect tests with incorrect assertions or false positives
4. **Validate test implementations**: Ensure test behavior matches documented claims

The dataset contains multiple requirement specifications with their corresponding test suites, enabling AI systems to learn requirement-to-test mapping across various domains.

## Context

Modern software systems use Software Requirements Specifications (SRS) where each requirement defines functionality with multiple conditions that must ALL be satisfied. Each requirement must have associated tests proving complete condition coverage.

**Primary Domain**: Air Traffic Control Systems (SKYRADAR)
**Test Framework**: XML-based scenario simulation with state transitions

## Project Structure

```
evaluation/
├── CLAUDE.md                          # Project guide (this file)
├── SRS.txt                            # All requirement specifications
├── .claude/
│   ├── agents/
│   │   └── test-coverage-validator.md      # Coverage validation agent
│   └── commands/
│       ├── create-req-srs.md               # ATM requirements generation
│       ├── validate-coverage.md            # Coverage validation
│       └── create-req-test-suite.md        # Test suite generation
│
├── TS_[REQ-CODE]/                     # Test suite folders (multiple)
│   ├── CLAUDE.md                      # Requirement coverage analysis
│   ├── system_dataset/                # Configuration/reference files
│   │   ├── [config-1].xml
│   │   ├── [config-2].xml
│   │   └── ...
│   ├── test_01/                       # Test scenario 1
│   │   └── scenario_[REQ-CODE]-01.xml
│   ├── test_02/                       # Test scenario 2
│   │   └── scenario_[REQ-CODE]-02.xml
│   ├── test_03/                       # Test scenario 3
│   │   └── scenario_[REQ-CODE]-03.xml
│   └── test_04/                       # Test scenario 4 (may contain false positive)
│       └── scenario_[REQ-CODE]-04.xml
│
└── Examples:
    ├── TS_STCA-041/  # STCA conflict suppression (7 conditions)
    └── TS_MSAW-025/  # Minimum safe altitude warnings (7 conditions)
```

## Test Suite Structure

Each test suite folder (`TS_[REQ-CODE]`) contains:

### CLAUDE.md (Coverage Analysis)
Each test suite has a CLAUDE.md file documenting:
- **Requirement summary**: The requirement being tested
- **Conditions list**: All conditions that must be satisfied (typically 5-7)
- **Coverage matrix**: Which tests cover which conditions
- **Coverage legend**: ✅ (explicit), 🟡 (implicit), ❌ (not tested)
- **Tested conditions**: Details on how each tested condition is validated
- **Untested conditions**: Specific gaps with explanations
- **Quality issues**: False positives and their evidence
- **Future tests needed**: Recommendations for additional coverage

### system_dataset/ (Configuration Files)
Shared configuration files that define:
- System parameters (thresholds, limits, ranges)
- Operational areas (zones, sectors, regions)
- System states (modes, statuses, configurations)
- Reference data (phase definitions, mappings, etc.)

These files are referenced by test scenarios and define the baseline system configuration.

### test_[NN]/ (Test Scenarios)
Each test directory contains ONE scenario XML file that:
- **Tests specific conditions**: Validates one or more requirement conditions
- **Contains state transitions**: Shows system behavior changing over time
- **Has expected results**: Assertions defining correct outcomes
- **May be intentionally flawed**: False positives to test AI detection

## Test Framework Elements

### Typical XML Elements

```xml
<!-- Establish initial system state -->
<FlightPlanUpdate/>    <!-- Define flight plans -->
<IdentUpdate/>         <!-- Associate objects with plans -->
<SystemConfigUpdate/>  <!-- Set system parameters/status -->

<!-- Simulate state changes -->
<TrackUpdates/>        <!-- Position/state changes over time -->
<DatapageUpdate/>      <!-- System configuration changes -->
<SystemStatusUpdate/>  <!-- Status transitions -->

<!-- Define expected behavior -->
<TestResult/>          <!-- Assert expected outcome at time T -->
```

### Key Test Patterns

1. **Condition validation**: Vary one condition while keeping others constant
2. **State transitions**: Negative → Positive → Negative (or similar)
3. **Multiple scenarios**: Same test often has 2-3 TestResult assertions at different times
4. **Implicit satisfaction**: Most tests satisfy many conditions implicitly in setup

## Test Coverage Categories

### ✅ Explicitly Tested (Coverage Claim)
- The test directly varies the condition
- Has both positive and negative cases
- Assertions validate the condition's effect

### 🟡 Implicitly Satisfied (Coverage Claim)
- The condition is set correctly in test setup
- But the condition is never varied or tested
- Condition value is assumed constant throughout

### ❌ Not Covered (Coverage Gap)
- The condition is never mentioned in the test
- The condition is never set to a specific value
- No test varies this condition

### ⚠️ False Positive (Quality Issue)
- Test claims to validate something
- But the validation is incorrect
- Often due to missing state changes or wrong assertions

## Creating New Test Specifications

To add a new requirement to the evaluation dataset:

### 1. Write the Requirement Specification
- Add to `SRS.txt` following the existing format
- Define 5-7 conditions that must ALL be satisfied
- Use condition IDs: C1, C2, C3, ...
- Each condition should be testable independently

Example structure:
```
SKYRADAR-[REQ-CODE]: [Short description]
SSS: [Reference ID]
SKYRADAR shall [primary statement] if ALL of the following conditions are met:
• Condition 1, and
• Condition 2, and
• ...
• Condition N.
```

### 2. Design the Test Suite
- Create folder: `TS_[REQ-CODE]/`
- Create `system_dataset/` with configuration files
- Plan 4 tests minimum:
  - test_01, test_02, test_03: Valid tests (each tests 1-2 conditions)
  - test_04: False positive test (intentionally flawed)

### 3. Implement Test Scenarios
- Create `test_[NN]/scenario_[REQ-CODE]-[NN].xml`
- Each test should:
  - Have clear description of what it tests
  - Follow the negative → positive → negative pattern when possible
  - Include proper state transitions
  - Have correct assertions for valid tests
  - Have INTENTIONAL errors for false positive tests

### 4. Document Coverage Analysis
- Create `TS_[REQ-CODE]/CLAUDE.md`
- Include:
  - Requirement summary
  - Conditions list
  - Coverage matrix (3/7 tested, 4/7 gaps)
  - Detailed analysis per tested condition
  - Specific documentation of coverage gaps
  - False positive identification with evidence
  - Expected AI analysis output

## AI Evaluation Goals

An AI analyzing this dataset should be able to:

1. **Parse requirements**: Extract all N conditions from SRS.txt
2. **Analyze tests**: Determine which conditions each test validates
3. **Identify coverage**: Map which conditions are explicitly tested
4. **Detect gaps**: Find which conditions are NOT tested
5. **Validate quality**: Detect false positives and incorrect assertions
6. **Generate reports**: Produce structured coverage analysis
7. **Validate analysis**: Use test-coverage-validator agent to verify findings

## Available Commands and Tools

### SRS Generation

#### /create-req-srs Command
Generates new ATM requirements specifications following EUROCONTROL standards.

- **Usage**: `/create-req-srs <count>` (e.g., `/create-req-srs 3`)
- **Function**: Creates N production-quality requirements for Air Traffic Management
- **Expert Context**: 40+ years EUROCONTROL experience with deep domain expertise
- **Output**: Formatted requirements ready to append to SRS.txt
- **Domains**: CD&R, Separation, Approaches, Arrivals, Departures, Weather, RVSM, RNP, TBS, etc.
- **Standards**: EUROCONTROL, EASA, ICAO compliance

### Test Suite Generation

#### /create-req-test-suite Command
Generates complete test suites for requirements with coverage analysis.

- **Usage**: `/create-req-test-suite <REQ-CODE>` (e.g., `/create-req-test-suite STCA-042`)
- **Function**: Creates 4 test scenarios + CLAUDE.md coverage documentation
- **Output**: Ready-to-use test folder structure with intentional quality issues

### Validation and Analysis

#### test-coverage-validator Agent
Validates that CLAUDE.md analysis claims match actual test implementations.

- **Method**: Line-by-line XML analysis with specific evidence
- **Validates**: Coverage claims, false positives, and gaps
- **Detects**: Undocumented issues and inconsistencies
- **Output**: Comprehensive validation report

#### /validate-coverage Command
Easily launch validation for any test suite.

- **Usage**: `/validate-coverage TS_[REQ-CODE]`
- **Output**: Comprehensive validation report
- **Integration**: Verifies test suite accuracy before deployment

## Usage Scenarios

### Complete Workflow: Generate → Test → Validate

```bash
# 1. Generate new ATM requirements
/create-req-srs 3

# 2. Create test suites for each requirement
/create-req-test-suite SKYRADAR-CD&R-051
/create-req-test-suite SKYRADAR-ARR-052
/create-req-test-suite SKYRADAR-SEP-053

# 3. Validate test suite accuracy
/validate-coverage TS_CD&R-051
/validate-coverage TS_ARR-052
/validate-coverage TS_SEP-053
```

### For AI Training
- Use complete test suites (STCA-041, MSAW-025) as training examples
- Show how requirements map to tests
- Demonstrate coverage gaps and false positives
- Generate new requirements with `/create-req-srs` for expanded training data

### For AI Testing
- Analyze individual test suites
- Produce coverage reports
- Compare against CLAUDE.md ground truth
- Measure detection accuracy on diverse ATM domains

### For Test Development
- Generate ATM-aligned requirements with domain expertise
- Create test suites with controlled coverage levels
- Validate implementations against specifications
- Ensure EUROCONTROL standards compliance

### For Benchmarking
- Compare multiple AI systems on same dataset
- Consistent evaluation criteria across diverse domains
- Multiple difficulty levels (3/7 to 7/7 coverage)
- Real-world ATM operational scenarios

## Additional Resources

### Documentation Files
- **SRS.txt**: Complete requirement specifications
- **CLAUDE.md** (this file): Project guide and workflows
- **TS_[REQ-CODE]/CLAUDE.md**: Per-requirement coverage analysis

### Agents
- **.claude/agents/test-coverage-validator.md**: Validation agent specification

### Commands
- **.claude/commands/create-req-srs.md**: ATM requirements generation command
- **.claude/commands/create-req-test-suite.md**: Test suite generation command
- **.claude/commands/validate-coverage.md**: Coverage validation command

## Best Practices for Test Suites

1. **Use consistent naming**: Follow `scenario_[REQ-CODE]-[NN].xml` pattern
2. **Keep conditions independent**: Each condition testable separately
3. **Include positive/negative cases**: Test both conditions met and not met
4. **Document assumptions**: Make implicit conditions explicit in descriptions
5. **Create intentional flaws**: At least one false positive per suite
6. **Use realistic data**: Make scenarios believable for domain experts
7. **Structure state changes**: Clear transitions between test phases

## Extending the Dataset

### Automated Workflow

Use the command-driven approach for efficient expansion:

```bash
# 1. Generate requirements (automated with domain expertise)
/create-req-srs 3

# 2. Create test suites (automated with quality controls)
/create-req-test-suite SKYRADAR-[CODE]

# 3. Validate coverage (automated verification)
/validate-coverage TS_[CODE]
```

### Manual Approach

To add requirements manually:

1. Add requirement to SRS.txt following the format
2. Create TS_[REQ-CODE]/ folder
3. Design and implement 4 test scenarios
4. Write CLAUDE.md with complete analysis
5. Run `/validate-coverage TS_[REQ-CODE]` to verify accuracy
6. Commit documentation changes

## Current Coverage

### Existing Test Suites
- ✅ **TS_STCA-041**: STCA conflict suppression (7 conditions, 3/7 tested)
- ✅ **TS_MSAW-025**: Minimum safe altitude warnings (7 conditions, 3/7 tested)
- ✅ **TS_RVSM-033**: RVSM non-approval alerts (7 conditions, 3/7 tested, 1 false positive)

### Available Commands for Expansion
- 🚀 `/create-req-srs <count>` - Generate N new ATM requirements
- 🚀 `/create-req-test-suite <CODE>` - Create test suite for any requirement
- ✅ `/validate-coverage <FOLDER>` - Verify test suite accuracy