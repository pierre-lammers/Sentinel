# Create New SRS Requirements Command

Generates new, production-quality Software Requirements Specifications (SRS) for Air Traffic Management systems following EUROCONTROL standards.

## Usage

```
/create-req-srs <count>
```

## Parameters

- `<count>`: Number of new requirements to generate (e.g., 1, 3, 5)

## Examples

```
/create-req-srs 1
/create-req-srs 3
/create-req-srs 5
```

## What This Command Does

This command launches a specialized ATM requirements expert agent that will:

1. Generate N new requirement specifications for Air Traffic Management systems
2. Ensure each requirement follows EUROCONTROL standards and best practices
3. Define 5-7 testable conditions per requirement
4. Add all requirements to SRS.txt with proper formatting
5. Provide documentation of each requirement with safety/operational context

## Implementation

You are launching the ATM-requirements-expert agent to generate **{{arg1}}** new requirements.

Use the Task tool with subagent_type="general-purpose" to execute the following optimized prompt:

```xml
<atm_requirements_generation>
  <expert_context>
    <role>You are a world-class Air Traffic Management (ATM) requirements engineer</role>
    <experience>40+ years at EUROCONTROL with deep expertise in:</experience>
    <expertise_areas>
      <area>Air Traffic Flow Management (ATFM)</area>
      <area>Safety Assessment and certification (EASA, Eurocontrol)</area>
      <area>ICAO PANS-ATM and regional procedures</area>
      <area>Performance-based navigation and advanced procedures</area>
      <area>Conflict Detection and Resolution (CD&R)</area>
      <area>Automated Contingency Management</area>
      <area>Separation Management and monitoring</area>
      <area>Dynamic Airspace Configuration</area>
      <area>Weather impact management</area>
      <area>Safety regulatory compliance</area>
    </expertise_areas>
    <standards>EUROCONTROL standards, EASA certification rules, ICAO Annex 11, PANS-ATM</standards>
  </expert_context>

  <task_definition>
    <objective>
      Generate {{arg1}} new, comprehensive requirements for an Air Traffic Management system
      following EUROCONTROL standards and best practices. Each requirement must be
      testable, measurable, and aligned with operational safety requirements.
    </objective>

    <constraints>
      <constraint>Each requirement must have 5-7 conditions (bullet points) that ALL must be satisfied</constraint>
      <constraint>Conditions must be independent and individually testable</constraint>
      <constraint>Requirements must cover diverse ATM operational domains</constraint>
      <constraint>Safety impact must be explicitly stated (true/false)</constraint>
      <constraint>Verification method and level must be specified</constraint>
      <constraint>Follow exact format from SRS.txt (first read the file to understand format)</constraint>
      <constraint>Use realistic EUROCONTROL terminology and operational concepts</constraint>
      <constraint>Requirements must be implementable in an ATC software system</constraint>
    </constraints>
  </task_definition>

  <thinking_process>
    <step_1_analyze_existing>
      <instruction>
        First, read the SRS.txt file completely to understand:
        1. Exact formatting and structure
        2. Existing requirement codes (SKYRADAR-STCA-041, SKYRADAR-MSAW-025)
        3. How conditions are written (format, specificity, measurability)
        4. Safety impact patterns
        5. Verification methods and levels
      </instruction>
    </step_1_analyze_existing>

    <step_2_domain_selection>
      <thinking>
        Based on EUROCONTROL ATM expertise, identify diverse functional domains:

        Possible ATM domains for new requirements:
        - Conflict Detection & Resolution (CD&R)
        - Separation Assurance
        - Approach procedures (parallel approaches, curved approaches)
        - Arrival Management (AMAN)
        - Departure Management (DMAN)
        - Airspace design and dynamic sectorization
        - Weather impact mitigation
        - Wake vortex separation
        - Runway sequencing
        - Ground delay programs
        - Dynamic airspace configuration
        - Continuous descent approaches
        - Approach spacing tools
        - Time-based separation (TBS)
        - Required Navigation Performance (RNP)
        - Reduced Vertical Separation Minimum (RVSM)
        - Oceanic clearance and separation

        Select {{arg1}} distinct domains ensuring:
        - No overlap with existing requirements (STCA-041, MSAW-025)
        - Progression from well-known to more advanced concepts
        - Mix of safety-critical and operational requirements
        - Real-world applicability
      </thinking>
    </step_2_domain_selection>

    <step_3_requirements_generation>
      <thinking>
        For EACH requirement to be generated:

        1. SELECT FUNCTIONAL DOMAIN
           - Choose from the list above, ensuring diversity
           - Pick something not already covered

        2. DEFINE REQUIREMENT CODE
           - Format: SKYRADAR-[FUNCTIONAL_AREA]-[NUMBER]
           - Functional areas: CD&R, SEP (Separation), APP (Approach), ARR (Arrival), DEP (Departure),
                               WX (Weather), RWY (Runway), RVSM, RNP, TBS (Time-based separation), etc.
           - Numbers should be sequential and unique

        3. DEFINE PRIMARY FUNCTIONAL STATEMENT
           - Clear, implementable functional requirement
           - Start with "SKYRADAR shall [verb] [object] [conditions]"
           - Align with EUROCONTROL operational procedures

        4. DEFINE 5-7 CONDITIONS
           - Each condition is a separate bullet point
           - Conditions are joined with "and" (ALL must be satisfied)
           - Include specific parameters, thresholds, ranges
           - Use realistic EUROCONTROL values (e.g., separation standards 1000ft vertical, 3NM horizontal)
           - Make conditions independently testable
           - Examples:
             * "The conflict detection system is in OPERATIONAL status"
             * "The predicted separation between aircraft is less than the current separation standard (3NM horizontal)"
             * "The warning horizon exceeds 5 minutes"
             * "Both aircraft have valid position reports within the last 30 seconds"
             * "Neither aircraft has an emergency flag active (7500, 7600, 7700)"

        5. SAFETY IMPACT
           - Determine if true or false based on consequence severity
           - Most CD&R requirements should be true
           - Most alerting/filtering requirements should be true

        6. VERIFICATION METHOD & LEVEL
           - Method: Test (test scenarios), Review (document inspection), Analysis (algorithmic analysis)
           - Level: RL (Requirement Level), DL (Design Level), IL (Implementation Level)
           - Most should be "Test" and "RL"
      </thinking>
    </step_3_requirements_generation>

    <step_4_condition_specification>
      <condition_quality_checklist>
        ✅ Is the condition specific (not vague)?
        ✅ Does it include measurable parameters or thresholds?
        ✅ Can it be tested independently?
        ✅ Is it realistic for EUROCONTROL/EASA certification?
        ✅ Does it use standardized terminology?
        ✅ Is it necessary for the requirement to be satisfied?
        ✅ Is it sufficient (combined with others) to define complete behavior?
      </condition_quality_checklist>
    </step_4_condition_specification>

    <step_5_format_validation>
      <instruction>
        Verify each requirement follows the exact format:

        SKYRADAR-[CODE]: [Short description]
        SSS: ATCS-SSS-REQ-[6-digit number]
        Derived status [derived/not_derived]
        Derived rationale [explanation if derived]
        Safety impact [true/false]
        Verification method [method]
        Verification level [level]
        (SDS rules [rule]) [comment]
        SKYRADAR shall [requirement statement] if ALL of the following conditions are met:
        • [Condition 1], and
        • [Condition 2], and
        ...
        • [Condition N].

        [blank line separator]
      </instruction>
    </step_5_format_validation>
  </thinking_process>

  <execution_steps>
    <step_1>
      <action>Read /Users/pierrelammers/Desktop/evaluation/SRS.txt completely</action>
      <purpose>Understand exact formatting, existing requirements, and code patterns</purpose>
    </step_1>

    <step_2>
      <action>Design {{arg1}} new requirements covering diverse ATM domains</action>
      <think_aloud>
        "I need to select {{arg1}} distinct ATM domains that don't overlap with:
        - SKYRADAR-STCA-041: STCA conflicts (Separation)
        - SKYRADAR-MSAW-025: Minimum Safe Altitude Warning

        For {{arg1}} requirement(s), I'll choose from:
        [List domains selected...]

        This ensures:
        - Domain diversity
        - Real-world applicability
        - Progressive complexity
        - EUROCONTROL alignment"
      </think_aloud>
    </step_2>

    <step_3>
      <action>For each requirement, define: Code, Statement, 5-7 Conditions, Safety Impact, Verification</action>
      <think_aloud_per_requirement>
        "REQUIREMENT {{N}}:
        - Domain: [Selected domain]
        - Code: SKYRADAR-[CODE]-###
        - Safety critical: [Yes/No based on operational impact]

        PRIMARY STATEMENT:
        SKYRADAR shall [specific functional statement]

        CONDITIONS (all must be satisfied):
        C1: [Specific, measurable condition with parameters]
        C2: [Specific, measurable condition with parameters]
        ...

        This requirement is crucial for [operational context] because [safety/operational reason]"
      </think_aloud_per_requirement>
    </step_3>

    <step_4>
      <action>Compile all {{arg1}} requirements in SRS.txt format</action>
      <output_format>
        Provide the complete text ready to append to SRS.txt:

        =================================================================================

        SKYRADAR-[CODE]: [Title]
        SSS: ATCS-SSS-REQ-######
        Derived status [status]
        Derived rationale [rationale]
        Safety impact [true/false]
        Verification method [method]
        Verification level [level]
        (SDS rules [rule]) [comment]
        SKYRADAR shall [statement] if ALL of the following conditions are met:
        • [Condition 1], and
        • [Condition 2], and
        ...
        • [Condition N].
      </output_format>
    </step_4>

    <step_5>
      <action>Output structured summary with all requirements for user review</action>
      <include>
        - Count of requirements generated
        - List of functional domains covered
        - Summary table with codes, titles, and condition counts
        - Formatted text ready to append to SRS.txt
        - Instructions for user to review and add to SRS.txt
      </include>
    </step_5>
  </execution_steps>

  <output_format>
    ## Generated Requirements Summary

    **Requirements Generated**: {{arg1}}
    **Domains Covered**: [List of diverse ATM domains]

    ### Requirements Overview

    | Code | Title | Conditions | Safety | Domain |
    |------|-------|-----------|--------|--------|
    | SKYRADAR-[CODE-1] | [Title] | 5-7 | [true/false] | [Domain] |
    | SKYRADAR-[CODE-2] | [Title] | 5-7 | [true/false] | [Domain] |
    | ... | ... | ... | ... | ... |

    ### Formatted Requirements (Ready for SRS.txt)

    [Complete formatted text of all {{arg1}} requirements following exact SRS.txt format]

    ### How to Use

    1. Review the requirements above for accuracy and alignment
    2. Copy the "Formatted Requirements" section
    3. Append to /Users/pierrelammers/Desktop/evaluation/SRS.txt before the final summary
    4. Optionally create test suites with: `/create-req-test-suite SKYRADAR-[CODE]`

    ### Quality Assurance Checklist

    - ✅ All {{arg1}} requirements have 5-7 conditions
    - ✅ Conditions are specific and measurable
    - ✅ Format matches existing SRS.txt requirements
    - ✅ Functional domains are diverse and non-overlapping
    - ✅ Safety impact is explicitly stated
    - ✅ Verification methods and levels are specified
    - ✅ EUROCONTROL standards compliance
    - ✅ Operational reality and implementability
  </output_format>

  <quality_standards>
    <standard>Each condition must be testable with clear pass/fail criteria</standard>
    <standard>Conditions must use EUROCONTROL standard terminology and values</standard>
    <standard>Requirements must be based on real ATM operational procedures</standard>
    <standard>Safety impact determination must be accurate and justified</standard>
    <standard>Verification methods must be realistic for the requirement type</standard>
    <standard>Requirements must be implementable in modern ATC systems</standard>
    <standard>No requirement should have duplicate or redundant conditions</standard>
    <standard>Requirements should cover the full range of ATM operational domains</standard>
  </quality_standards>
</atm_requirements_generation>
```

---

## Advanced Usage

### Generate Multiple Batches

```
/create-req-srs 3   # Generate 3 requirements
/create-req-srs 5   # Generate 5 more requirements
```

### Integration with Test Suite Generation

After generating requirements, create test suites:

```
/create-req-test-suite SKYRADAR-CD&R-051
/create-req-test-suite SKYRADAR-ARR-052
```

## EUROCONTROL Standards Reference

This command generates requirements following:

- **EASA Specifications**: AMC 20-25D and certification documentation
- **ICAO Standards**: Annex 11, PANS-ATM (Doc 4444)
- **EUROCONTROL Standards**:
  - Performance Review System (PRS)
  - SESAR specifications
  - European ATC Harmonisation roadmap
- **Safety Criteria**: SMS principles (Safety Management System)
- **Operational Requirements**: ICAO Doc 9830, Vol IV

## Example ATM Domains Covered

- **Separation Assurance**: Conflict Detection & Resolution, Separation Management
- **Approach Procedures**: Parallel approaches, Continuous Descent Approaches (CDA)
- **Arrival Management**: AMAN functions, sequence management, spacing
- **Departure Management**: DMAN functions, departure sequencing
- **Vertical Separation**: RVSM monitoring and enforcement
- **Navigation Performance**: RNP procedure adherence
- **Time-based Separation**: TBS implementation and monitoring
- **Weather Impact**: Weather hazard detection, convective weather avoidance
- **Wake Vortex**: Wake separation enforcement, hazard warnings
- **Runway Operations**: Runway occupancy, sequential use, capacity management

---

## Examples in Repository

Refer to existing requirements for reference:
- `SKYRADAR-STCA-041`: STCA conflict suppression (7 conditions, 3/7 tested)
- `SKYRADAR-MSAW-025`: Minimum safe altitude warnings (7 conditions, 3/7 tested)

