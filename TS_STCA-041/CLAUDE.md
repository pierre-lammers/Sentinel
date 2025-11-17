# Test Coverage Analysis - SKYRADAR-STCA-041

## Requirement Summary

**SKYRADAR-STCA-041**: Suppression of STCA conflicts due to NTZ processing

SKYRADAR shall flag STCA conflicts as suppressed for tracks located in NOZ if ALL of the following conditions are met:

### Conditions List

| ID | Condition Description | Parameter/Value |
|----|----------------------|-----------------|
| **C1** | The associated NTZ area is active | `isActive="true"` |
| **C2** | The status of the NTZ areas manager is equal to OPERATIONAL | `status="OPERATIONAL"` |
| **C3** | The heading gap between each aircraft and the runway axis is lower than CSP: MAX_DELTA_HEADING | MAX_DELTA_HEADING = 20° |
| **C4** | The current distance between the aircraft is kept above VSP: MinimalDistance (safety distance) | MinimalDistance = 0 |
| **C5** | Each track is located within a different NOZ associated with an offline defined "parallel approach pair" of runways | NOZ areas: 02L, 02R |
| **C6** | The "parallel approach pair" is in INDEPENDENT mode | `modeOnStartup="INDEPENDENT"` |
| **C7** | The flag STCA_PARALLEL_APP_FPL_CHECK_FLAG is set to false OR the runway of each track's coupled FPL (if assigned) matches the runway linked to the NOZ where the track is located | Flag = false OR FPL runway matches NOZ |

## Test Coverage Matrix

| Test ID | Test Name | C1 | C2 | C3 | C4 | C5 | C6 | C7 | Status | Notes |
|---------|-----------|----|----|----|----|----|----|-------|--------|-------|
| **test_01** | NTZ area active/inactive | ✅ | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 | ❌ | Complete | Tests condition C1. Uses `status="AVAILABLE"` (not OPERATIONAL) but doesn't explicitly test C2 |
| **test_02** | NTZ manager status | 🟡 | ✅ | 🟡 | 🟡 | 🟡 | 🟡 | ✅ | Complete | Tests condition C2. Sets `STCA_PARALLEL_APP_FPL_CHECK_FLAG=false` (C7) |
| **test_03** | Heading gap validation | 🟡 | 🟡 | ✅ | 🟡 | 🟡 | 🟡 | ✅ | Complete | Tests condition C3 with multiple heading scenarios |
| **test_04** | NTZ manager operational ⚠️ | 🟡 | ❌ | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 | **FALSE POSITIVE** | Claims to test C2 but has incorrect assertions. REDUNDANT with test_02 |

### Legend
- ✅ **Explicitly tested**: The test directly validates this condition (positive and negative cases)
- 🟡 **Implicitly satisfied**: The condition is met in the test setup but not explicitly validated
- ❌ **Not covered**: The condition is not tested or validated
- ⚠️ **False positive**: Test has incorrect assertions or doesn't test what it claims

## Coverage Analysis

### Tested Conditions (3/7)

#### ✅ C1: NTZ Area Active Status
- **Test**: test_01/scenario_STCA-041-01.xml
- **Coverage**: Complete
- **Test scenarios**:
  - NTZ inactive → No suppression (expected)
  - NTZ active → Suppression (expected)
  - NTZ inactive again → No suppression (expected)

#### ✅ C2: NTZ Manager Operational Status
- **Test**: test_02/scenario_STCA-041-02.xml
- **Coverage**: Complete
- **Test scenarios**:
  - Status = AVAILABLE → No suppression (expected)
  - Status = OPERATIONAL → Suppression (expected)
  - Status = DEGRADED → No suppression (expected)

#### ✅ C3: Heading Gap < MAX_DELTA_HEADING (20°)
- **Test**: test_03/scenario_STCA-041-03.xml
- **Coverage**: Complete
- **Test scenarios**:
  - Heading gap ~58° → No suppression (expected)
  - Heading gap ~11° → Suppression (expected)
  - Heading gap ~74° → No suppression (expected)
- **Technical details**:
  - Runway axis heading = 90° (East)
  - Aircraft heading calculated from `atan2(cartSpeedX, cartSpeedY)`

### Untested Conditions (4/7) - AI SHOULD DETECT THESE GAPS

#### ❌ C4: Minimal Distance Above Threshold
- **Status**: NOT TESTED
- **Gap**: No test validates that aircraft distance must be above MinimalDistance (0)
- **Required test scenarios**:
  - Distance below MinimalDistance → No suppression
  - Distance above MinimalDistance → Suppression (if all other conditions met)
- **AI Detection Goal**: The AI should identify this missing test coverage

#### ❌ C5: Tracks in Different NOZ Areas
- **Status**: NOT TESTED
- **Gap**: No test validates that each track must be in a different NOZ
- **Current tests**: All tests place tracks in correct NOZ (02L and 02R) but never test violations
- **Required test scenarios**:
  - Both tracks in same NOZ → No suppression
  - Tracks in different NOZ of parallel approach pair → Suppression
  - Track in NOZ not part of parallel approach pair → No suppression
- **AI Detection Goal**: The AI should identify this as an implicit assumption never validated

#### ❌ C6: Parallel Approach Pair in INDEPENDENT Mode
- **Status**: NOT TESTED
- **Gap**: No test validates the mode requirement
- **Current tests**: All use `modeOnStartup="INDEPENDENT"` in configuration but never test other modes
- **Required test scenarios**:
  - Mode = DEPENDENT → No suppression
  - Mode = INDEPENDENT → Suppression
  - Mode = SEGREGATED → No suppression (if applicable)
- **AI Detection Goal**: The AI should detect that this condition is never varied/tested

#### ❌ C7: FPL Check Flag / Runway Matching
- **Status**: PARTIALLY TESTED
- **Gap**: Only tested in test_02 with flag=false, not the runway matching alternative
- **Current coverage**:
  - test_02 sets flag to false → Condition satisfied
  - test_03 sets flag to false → Condition satisfied
  - test_01 sets flag to true AND provides matching FPL runways, but not explicitly tested
- **Required test scenarios**:
  - Flag = false → Suppression (✅ covered in test_02)
  - Flag = true AND FPL runway matches NOZ → Suppression (⚠️ not explicitly tested)
  - Flag = true AND FPL runway does NOT match NOZ → No suppression (❌ NOT covered)
  - Flag = true AND no FPL assigned → behavior unclear (❌ NOT covered)
- **AI Detection Goal**: The AI should detect incomplete coverage of this OR condition

## Expected AI Analysis Output

A competent AI system analyzing this test suite should produce a report similar to:

```
REQUIREMENT: SKYRADAR-STCA-041
Total Conditions: 7
Tested Conditions: 3 (42.9%)
Untested Conditions: 4 (57.1%)

COVERAGE GAPS DETECTED:
1. Condition C4 (Minimal Distance): NO TESTS FOUND
2. Condition C5 (Different NOZ Areas): NO TESTS FOUND
3. Condition C6 (INDEPENDENT Mode): NO TESTS FOUND
4. Condition C7 (FPL Check): PARTIALLY TESTED (flag=false case only)

FALSE POSITIVES DETECTED:
1. test_04 (scenario_STCA-041-04.xml):
   - Claims to test C2 (NTZ manager OPERATIONAL status)
   - PROBLEM: Missing BnsUpdate to change status to OPERATIONAL
   - PROBLEM: Assertion expects isSuppressed="true" but status is AVAILABLE (should be false)
   - SEVERITY: HIGH - Test validates incorrect behavior

REDUNDANCY DETECTED:
1. test_04 attempts to test condition C2, which is already covered by test_02
   - test_02 provides complete coverage of C2 (AVAILABLE → OPERATIONAL → DEGRADED)
   - test_04 is redundant and should be removed or repurposed

RECOMMENDATION:
- Fix or remove test_04 (false positive)
- Create additional test scenarios to cover conditions C4, C5, C6, and complete C7 testing
```

## Test Quality Issues

### ⚠️ FALSE POSITIVE DETECTED: test_04

**Test ID**: test_04/scenario_STCA-041-04.xml
**Claimed Objective**: "Verifies that SKYRADAR properly suppresses STCA conflicts when NTZ manager transitions from AVAILABLE to OPERATIONAL status"
**Actual Problem**: **The test does NOT actually test what it claims**

#### Issues Identified

1. **Missing State Change**:
   - The test claims at time 12 the NTZ manager transitions to OPERATIONAL
   - **MISSING**: The `<BnsUpdate>` tag that would change status to OPERATIONAL is absent
   - Result: Status remains AVAILABLE throughout the entire test

2. **Incorrect Assertion**:
   - Line 97: `<TestResult ... resultDescription="... NTZ manager is OPERATIONAL">`
   - Line 98: `<Alerts ... isSuppressed="true">`
   - **PROBLEM**: Assertion claims suppression occurs because manager is OPERATIONAL
   - **REALITY**: Manager status is still AVAILABLE, so suppression should NOT occur
   - This is a **false positive assertion**

3. **Test Redundancy**:
   - This test claims to test condition C2 (NTZ manager OPERATIONAL status)
   - Condition C2 is already properly tested by test_02
   - test_04 adds no value and is redundant

#### What the AI Should Detect

A competent AI analyzing this test should identify:

```
ISSUE: FALSE POSITIVE in test_04
- Description claims: "NTZ manager is set to OPERATIONAL"
- XML shows: No BnsUpdate at time 12 to change status
- Last status update: AVAILABLE (line 58)
- Assertion: isSuppressed="true" (line 98)
- Expected: isSuppressed="false" (because status is AVAILABLE, not OPERATIONAL)

SEVERITY: HIGH - Test passes but validates incorrect behavior

RECOMMENDATION: Either fix the missing BnsUpdate or correct the assertion to isSuppressed="false"

ADDITIONAL ISSUE: REDUNDANT TEST
- test_04 claims to test condition C2
- Condition C2 already tested by test_02
- test_04 provides no additional coverage
```

#### Code Location of the Error

**Missing BnsUpdate** (should be between lines 78-79):
```xml
<!-- MISSING: The BnsUpdate that should change status to OPERATIONAL is MISSING here! -->
<!-- This should be: <BnsUpdate time="12"><BnsPRM status="OPERATIONAL"/></BnsUpdate> -->
```

**Incorrect Assertion** (line 97-98):
```xml
<TestResult resultTimeInMilliSec="13000" resultDescription="... NTZ manager is OPERATIONAL.">
    <Alerts alertType="CONFLICT" trackNum="1" isSuppressed="true" >
```
Status is AVAILABLE, so `isSuppressed` should be `"false"`, not `"true"`.

### Valid Tests (test_01, test_02, test_03)

The first three tests have:
- ✅ Correct assertions matching their stated objectives
- ✅ Valid XML structure with proper state transitions
- ✅ Consistent test scenarios (negative → positive → negative)
- ✅ Accurate descriptions

## Future Test Scenarios Needed

To achieve 100% coverage, the following test scenarios should be created:

1. **test_05**: Minimal distance validation (C4)
2. **test_06**: NOZ area separation (C5)
3. **test_07**: Parallel approach mode (C6)
4. **test_08**: FPL runway matching with flag=true (C7 completion)

Additionally, consider creating:
- **test_09**: Combined condition test (multiple conditions varying simultaneously)
- **test_10**: Edge cases (boundary values for heading, distance, etc.)
