# Test Coverage Analysis - SKYRADAR-MSAW-025

## Requirement Summary

**SKYRADAR-MSAW-025**: Generation of Minimum Safe Altitude Warning alerts

SKYRADAR shall generate MSAW (Minimum Safe Altitude Warning) alerts for tracks if ALL of the following conditions are met:

### Conditions List

| ID | Condition Description | Parameter/Value |
|----|----------------------|-----------------|
| **C1** | The MSAW system status is equal to OPERATIONAL | `status="OPERATIONAL"` |
| **C2** | The track altitude is below the MSA (Minimum Safe Altitude) threshold defined for the current sector | MSA varies by sector (3000ft for APPROACH_ZONE_01) |
| **C3** | The track is in APPROACH or DEPARTURE flight phase | `flightPhase="APPROACH"` or `"DEPARTURE"` |
| **C4** | The track vertical speed indicates descent or level flight (not climbing above MIN_CLIMB_RATE) | MIN_CLIMB_RATE = 500 ft/min |
| **C5** | The track is located within a monitored airspace zone where MSAW is active | Zone: APPROACH_ZONE_01, DEPARTURE_ZONE_01 |
| **C6** | The track has valid altitude data with quality indicator equal to HIGH or MEDIUM | `altitudeQuality="HIGH"` or `"MEDIUM"` |
| **C7** | The flag MSAW_EMERGENCY_OVERRIDE is set to false OR the track's transponder squawk code is NOT in the emergency range (7500, 7600, 7700) | Flag = false OR squawk NOT emergency |

## Test Coverage Matrix

| Test ID | Test Name | C1 | C2 | C3 | C4 | C5 | C6 | C7 | Status | Notes |
|---------|-----------|----|----|----|----|----|----|-------|--------|-------|
| **test_01** | Altitude threshold validation | 🟡 | ✅ | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 | Complete | Tests condition C2. Sets `status="OPERATIONAL"` (C1) implicitly |
| **test_02** | MSAW system status | ✅ | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 | Complete | Tests condition C1 with multiple status transitions |
| **test_03** | Flight phase validation | 🟡 | 🟡 | ✅ | 🟡 | 🟡 | 🟡 | 🟡 | Complete | Tests condition C3 with CRUISE vs APPROACH phases |
| **test_04** | MSAW operational transition ⚠️ | ❌ | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 | **FALSE POSITIVE** | Claims to test C1 but has incorrect assertions. REDUNDANT with test_02 |

### Legend
- ✅ **Explicitly tested**: The test directly validates this condition (positive and negative cases)
- 🟡 **Implicitly satisfied**: The condition is met in the test setup but not explicitly validated
- ❌ **Not covered**: The condition is not tested or validated
- ⚠️ **False positive**: Test has incorrect assertions or doesn't test what it claims

## Coverage Analysis

### Tested Conditions (3/7)

#### ✅ C1: MSAW System Status OPERATIONAL
- **Test**: test_02/scenario_MSAW-025-02.xml
- **Coverage**: Complete
- **Test scenarios**:
  - Status = STANDBY → No alert (expected)
  - Status = OPERATIONAL → Alert generated (expected)
  - Status = DEGRADED → No alert (expected)

#### ✅ C2: Altitude Below MSA Threshold
- **Test**: test_01/scenario_MSAW-025-01.xml
- **Coverage**: Complete
- **Test scenarios**:
  - Altitude 3500ft > MSA 3000ft → No alert (expected)
  - Altitude 2500ft < MSA 3000ft → Alert generated (expected)
  - Altitude 3500ft > MSA 3000ft → No alert (expected)
- **Technical details**:
  - MSA threshold = 3000ft for APPROACH_ZONE_01
  - Track altitude read from `baroAltitude` field

#### ✅ C3: Flight Phase APPROACH or DEPARTURE
- **Test**: test_03/scenario_MSAW-025-03.xml
- **Coverage**: Complete
- **Test scenarios**:
  - Flight phase = CRUISE → No alert (expected)
  - Flight phase = APPROACH → Alert generated (expected)
  - Flight phase = CRUISE → No alert (expected)
- **Technical details**:
  - Flight phase determined from `flightPhase` attribute
  - Valid phases for MSAW: APPROACH, DEPARTURE
  - Invalid phase: CRUISE

### Untested Conditions (4/7) - AI SHOULD DETECT THESE GAPS

#### ❌ C4: Vertical Speed Not Climbing Above MIN_CLIMB_RATE
- **Status**: NOT TESTED
- **Gap**: No test validates that high climb rate prevents MSAW alerts
- **Current tests**: All tests use descent or low climb rates (rocRodRate between -450 and 600 ft/min)
- **Required test scenarios**:
  - Vertical speed climbing > MIN_CLIMB_RATE (500 ft/min) → No alert
  - Vertical speed climbing < MIN_CLIMB_RATE → Alert generated (if other conditions met)
  - Vertical speed descending → Alert generated (if other conditions met)
- **AI Detection Goal**: The AI should identify this missing test coverage

#### ❌ C5: Track in Monitored MSAW Zone
- **Status**: NOT TESTED
- **Gap**: No test validates zone activation requirement
- **Current tests**: All tests place tracks in APPROACH_ZONE_01 which is active by default
- **Required test scenarios**:
  - Track in inactive MSAW zone → No alert
  - Track in active MSAW zone → Alert generated
  - Track outside any MSAW zone → No alert
- **AI Detection Goal**: The AI should detect that zone activation is never varied/tested

#### ❌ C6: Altitude Quality Indicator
- **Status**: NOT TESTED
- **Gap**: No test validates altitude quality requirement
- **Current tests**: All use `altitudeQuality="HIGH"` but never test other quality levels
- **Required test scenarios**:
  - Altitude quality = LOW → No alert
  - Altitude quality = MEDIUM → Alert generated
  - Altitude quality = HIGH → Alert generated
  - Altitude quality = INVALID → No alert
- **AI Detection Goal**: The AI should detect that this condition is never varied/tested

#### ❌ C7: Emergency Override Flag / Squawk Code
- **Status**: PARTIALLY TESTED
- **Gap**: Only tested with emergencyOverride=false, not the squawk code alternative
- **Current coverage**:
  - All tests set emergencyOverride to false → Condition satisfied
  - No tests vary squawk codes or test emergency codes
- **Required test scenarios**:
  - Flag = false → Alert generated (✅ covered in all tests)
  - Flag = true AND squawk NOT emergency (e.g., 1200) → Alert generated (❌ NOT covered)
  - Flag = true AND squawk IS emergency (7500/7600/7700) → No alert (❌ NOT covered)
- **AI Detection Goal**: The AI should detect incomplete coverage of this OR condition

## Expected AI Analysis Output

A competent AI system analyzing this test suite should produce a report similar to:

```
REQUIREMENT: SKYRADAR-MSAW-025
Total Conditions: 7
Tested Conditions: 3 (42.9%)
Untested Conditions: 4 (57.1%)

COVERAGE GAPS DETECTED:
1. Condition C4 (Vertical Speed): NO TESTS FOUND
2. Condition C5 (MSAW Zone Active): NO TESTS FOUND
3. Condition C6 (Altitude Quality): NO TESTS FOUND
4. Condition C7 (Emergency Override): PARTIALLY TESTED (flag=false case only)

FALSE POSITIVES DETECTED:
1. test_04 (scenario_MSAW-025-04.xml):
   - Claims to test C1 (MSAW system OPERATIONAL status)
   - PROBLEM: Missing MsawSystemUpdate to change status to OPERATIONAL
   - PROBLEM: Assertion expects alertGenerated="true" but status is STANDBY (should be false)
   - SEVERITY: HIGH - Test validates incorrect behavior

REDUNDANCY DETECTED:
1. test_04 attempts to test condition C1, which is already covered by test_02
   - test_02 provides complete coverage of C1 (STANDBY → OPERATIONAL → DEGRADED)
   - test_04 is redundant and should be removed or repurposed

RECOMMENDATION:
- Fix or remove test_04 (false positive)
- Create additional test scenarios to cover conditions C4, C5, C6, and complete C7 testing
```

## Test Quality Issues

### ⚠️ FALSE POSITIVE DETECTED: test_04

**Test ID**: test_04/scenario_MSAW-025-04.xml
**Claimed Objective**: "Verifies that SKYRADAR properly generates MSAW alerts when MSAW system transitions from STANDBY to OPERATIONAL status"
**Actual Problem**: **The test does NOT actually test what it claims**

#### Issues Identified

1. **Missing State Change**:
   - The test claims at time 12 the MSAW system transitions to OPERATIONAL
   - **MISSING**: The `<MsawSystemUpdate>` tag that would change status to OPERATIONAL is absent
   - Result: Status remains STANDBY throughout the entire test

2. **Incorrect Assertion**:
   - Line 97: `<TestResult ... resultDescription="... MSAW system is OPERATIONAL ...">`
   - Line 98: `<Alerts ... alertGenerated="true">`
   - **PROBLEM**: Assertion claims alert is generated because system is OPERATIONAL
   - **REALITY**: System status is still STANDBY, so alert should NOT be generated
   - This is a **false positive assertion**

3. **Test Redundancy**:
   - This test claims to test condition C1 (MSAW system OPERATIONAL status)
   - Condition C1 is already properly tested by test_02
   - test_04 adds no value and is redundant

#### What the AI Should Detect

A competent AI analyzing this test should identify:

```
ISSUE: FALSE POSITIVE in test_04
- Description claims: "MSAW system is set to OPERATIONAL"
- XML shows: No MsawSystemUpdate at time 12 to change status
- Last status update: STANDBY (line 55)
- Assertion: alertGenerated="true" (line 98)
- Expected: alertGenerated="false" (because status is STANDBY, not OPERATIONAL)

SEVERITY: HIGH - Test passes but validates incorrect behavior

RECOMMENDATION: Either fix the missing MsawSystemUpdate or correct the assertion to alertGenerated="false"

ADDITIONAL ISSUE: REDUNDANT TEST
- test_04 claims to test condition C1
- Condition C1 already tested by test_02
- test_04 provides no additional coverage
```

#### Code Location of the Error

**Missing MsawSystemUpdate** (should be between lines 78-79):
```xml
<!-- MISSING: The MsawSystemUpdate that should change status to OPERATIONAL is MISSING here! -->
<!-- This should be: <MsawSystemUpdate time="12"><MsawStatus status="OPERATIONAL" emergencyOverride="false"/></MsawSystemUpdate> -->
```

**Incorrect Assertion** (line 97-100):
```xml
<TestResult resultTimeInMilliSec="15000" resultDescription="MSAW alert is generated because MSAW system is OPERATIONAL.">
    <Alerts alertType="MSAW" trackNum="1" alertGenerated="true">
```
Status is STANDBY, so `alertGenerated` should be `"false"`, not `"true"`.

### Valid Tests (test_01, test_02, test_03)

The first three tests have:
- ✅ Correct assertions matching their stated objectives
- ✅ Valid XML structure with proper state transitions
- ✅ Consistent test scenarios (negative → positive → negative)
- ✅ Accurate descriptions

## Future Test Scenarios Needed

To achieve 100% coverage, the following test scenarios should be created:

1. **test_05**: Vertical speed validation (C4)
2. **test_06**: MSAW zone activation (C5)
3. **test_07**: Altitude quality indicator (C6)
4. **test_08**: Emergency override with squawk codes (C7 completion)

Additionally, consider creating:
- **test_09**: Combined condition test (multiple conditions varying simultaneously)
- **test_10**: Edge cases (boundary values for altitude, vertical speed, etc.)
