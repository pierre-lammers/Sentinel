# Software Requirements Specification

## SKYRADAR Air Traffic Control System
### Version 1.0

---

**Document Information**

| Field | Value |
|-------|-------|
| Project Name | SKYRADAR Advanced ATC System |
| Document Version | 1.0 |
| Date | December 16, 2025 |
| Status | Draft |
| Prepared By | System Engineering Team |

---

**Revision History**

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2025-12-16 | Engineering Team | Initial SRS document with 8 core safety requirements |

---

## Table of Contents

1. [Introduction](#1-introduction)
   - 1.1 [Purpose](#11-purpose)
   - 1.2 [Document Conventions](#12-document-conventions)
   - 1.3 [Intended Audience](#13-intended-audience)
   - 1.4 [Product Scope](#14-product-scope)
   - 1.5 [References](#15-references)
2. [Overall Description](#2-overall-description)
   - 2.1 [Product Perspective](#21-product-perspective)
   - 2.2 [Product Features](#22-product-features)
   - 2.3 [User Classes and Characteristics](#23-user-classes-and-characteristics)
   - 2.4 [Operating Environment](#24-operating-environment)
   - 2.5 [Design and Implementation Constraints](#25-design-and-implementation-constraints)
   - 2.6 [Assumptions and Dependencies](#26-assumptions-and-dependencies)
3. [System Features](#3-system-features)
4. [Functional Requirements](#4-functional-requirements)
   - 4.1 [Conflict Detection and Resolution](#41-conflict-detection-and-resolution)
   - 4.2 [Terrain and Altitude Monitoring](#42-terrain-and-altitude-monitoring)
   - 4.3 [Airspace Compliance Monitoring](#43-airspace-compliance-monitoring)
   - 4.4 [Traffic Flow Management](#44-traffic-flow-management)
   - 4.5 [Separation Assurance](#45-separation-assurance)
   - 4.6 [Navigation Performance Monitoring](#46-navigation-performance-monitoring)
   - 4.7 [Data Link Communications](#47-data-link-communications)
   - 4.8 [Departure Management](#48-departure-management)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [Appendices](#6-appendices)

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) document defines the functional and non-functional requirements for the SKYRADAR Air Traffic Control System. The document is intended to serve as a contractual agreement between stakeholders and the development team, ensuring all safety-critical and operational requirements are clearly specified and verifiable.

The SKYRADAR system provides advanced air traffic management capabilities including conflict detection, terrain awareness, airspace compliance monitoring, and automated traffic flow optimization for modern Air Traffic Control (ATC) operations.

### 1.2 Document Conventions

This document follows IEEE 830-1998 standard formatting conventions:

- **Requirement Priority Levels:**
  - HIGH: Safety-critical requirements (Safety impact = true)
  - MEDIUM: Operational efficiency requirements (Safety impact = false)

- **Requirement Identifiers:** Format `SKYRADAR-[SUBSYSTEM]-[NNN]`

- **Verification Methods:**
  - Test: Formal testing procedures
  - RL: Requirements Level verification

- **Derivation Status:**
  - Partially: Requirements partially derived from parent specifications

- **Typography:**
  - `CSP:` = Configuration System Parameter
  - `VSP:` = Variable System Parameter
  - **Bold** = Key terms and headings
  - *Italics* = References to external documents

### 1.3 Intended Audience

This document is intended for:

- **System Engineers:** Overall system architecture and integration
- **Software Developers:** Implementation of safety-critical algorithms
- **Test Engineers:** Verification and validation planning
- **Safety Assessors:** Safety case development and certification
- **Air Traffic Controllers:** Operational concept validation
- **Regulatory Authorities:** Certification and compliance review
- **Project Managers:** Planning and resource allocation

### 1.4 Product Scope

SKYRADAR is a next-generation Air Traffic Control automation system designed to enhance safety and efficiency in terminal and en-route airspace operations. The system provides:

**Primary Benefits:**
- Enhanced separation assurance through multi-layered conflict detection
- Improved terrain clearance monitoring for approach/departure operations
- Automated traffic flow optimization for arrivals and departures
- Advanced navigation performance monitoring for precision procedures
- Real-time compliance monitoring for specialized airspace operations

**Key Objectives:**
- Reduce controller workload through intelligent automation
- Improve safety margins through predictive alerting
- Optimize airspace capacity through dynamic sequencing
- Support advanced procedures (RNP, CPDLC, Time-Based Separation)
- Ensure compliance with international aviation standards (ICAO, FAA, EASA)

### 1.5 References

| Reference ID | Document | Version |
|--------------|----------|---------|
| SSS | ATCS System Specification | REQ-005855 to REQ-007585 |
| ICAO-PANS-ATM | ICAO Procedures for Air Navigation Services - Air Traffic Management | Doc 4444 |
| ICAO-Annex11 | ICAO Annex 11 - Air Traffic Services | Amendment 51 |
| EUROCAE-ED87 | Minimum Aviation System Performance Standards for STCA | ED-87C |
| RTCA-DO-318 | Minimum Operational Performance Standards for RVSM | DO-318 |
| FAA-JO-7110 | FAA Air Traffic Control Procedures | Order 7110.65Z |

---

## 2. Overall Description

### 2.1 Product Perspective

SKYRADAR operates as a core component within a larger Air Traffic Control ecosystem:

```
┌─────────────────────────────────────────────────────────────┐
│                    ATC Ecosystem                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐     ┌─────────────┐ │
│  │   Radar      │─────▶│   SKYRADAR   │────▶│  Controller │ │
│  │   Sensors    │      │    System    │     │  Workstation│ │
│  └──────────────┘      └──────────────┘     └─────────────┘ │
│                              │                                │
│  ┌──────────────┐           │              ┌─────────────┐  │
│  │   Flight     │───────────┤              │   CPDLC     │  │
│  │   Plans      │           │              │   Gateway   │  │
│  └──────────────┘           │              └─────────────┘  │
│                              │                                │
│  ┌──────────────┐           │              ┌─────────────┐  │
│  │  Weather     │───────────┤              │  Recording  │  │
│  │  Data        │           └─────────────▶│  System     │  │
│  └──────────────┘                          └─────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**External Interfaces:**
- Surveillance data from primary/secondary radar and ADS-B
- Flight plan data from Flight Data Processing System
- Meteorological data from weather information systems
- Controller inputs via Human-Machine Interface (HMI)
- CPDLC messages via data link gateway

### 2.2 Product Features

The SKYRADAR system provides eight major feature categories:

| Feature Category | Description | Safety Critical |
|------------------|-------------|-----------------|
| **STCA** - Short Term Conflict Alert | Detects and alerts potential aircraft conflicts with specialized logic for parallel approaches | No |
| **MSAW** - Minimum Safe Altitude Warning | Monitors terrain clearance during approach/departure phases | Yes |
| **RVSM** - Reduced Vertical Separation | Ensures aircraft compliance with RVSM approval requirements | Yes |
| **AMAN** - Arrival Manager | Optimizes arrival sequences using time-based separation | No |
| **Wake Vortex** | Monitors dynamic wake turbulence separation based on atmospheric conditions | Yes |
| **RNP** - Required Navigation Performance | Validates containment within RNP approach procedures | Yes |
| **CPDLC** - Controller-Pilot Data Link | Manages timeout and reversion for data link clearances | Yes |
| **DMAN** - Departure Manager | Monitors compliance with departure slot allocations | No |

**Feature Interaction Diagram:**

```
                    ┌─────────────────┐
                    │  Surveillance   │
                    │  Track Data     │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐         ┌────▼────┐        ┌────▼────┐
    │  STCA   │         │  MSAW   │        │  RVSM   │
    │ Conflict│         │ Terrain │        │Airspace │
    │Detection│         │Clearance│        │ Compliance
    └─────────┘         └─────────┘        └─────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Alert Manager  │
                    │  (Prioritization)│
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Controller    │
                    │   Display       │
                    └─────────────────┘
```

### 2.3 User Classes and Characteristics

| User Class | Description | Technical Expertise | Usage Frequency |
|------------|-------------|---------------------|-----------------|
| **Air Traffic Controllers** | Primary operators who use alerts to maintain separation and safety | Medium (ATC trained) | Continuous |
| **Supervisors** | Monitor system status and override parameters | High (Senior controllers) | Intermittent |
| **System Engineers** | Configure parameters (CSP/VSP) and monitor performance | Very High (Engineering) | Daily (maintenance) |
| **Safety Analysts** | Review alert logs and safety metrics | High (Safety domain) | Weekly/Monthly |
| **Maintenance Technicians** | Perform system health checks and diagnostics | High (Technical) | As needed |

### 2.4 Operating Environment

**Hardware Platform:**
- Fault-tolerant server architecture with redundancy
- Real-time processing capabilities (<100ms latency)
- Minimum 32GB RAM, multi-core processors (8+ cores)
- Redundant network interfaces (1Gbps+)

**Software Environment:**
- Real-time operating system (e.g., VxWorks, Linux RT)
- Database system for configuration and historical data
- Network protocols: ASTERIX, ICAO AIDC, CPDLC ATN

**Operational Environment:**
- 24/7/365 availability requirement
- Temperature-controlled server room (18-24°C)
- UPS backup power (minimum 30 minutes)
- Geographic redundancy for disaster recovery

### 2.5 Design and Implementation Constraints

**Regulatory Constraints:**
- Must comply with ICAO Standards and Recommended Practices (SARPs)
- Must meet EUROCAE ED-87C STCA performance standards
- Must satisfy DO-178C software development assurance level (DAL-B for safety-critical functions)

**Technical Constraints:**
- Maximum alert latency: 2 seconds from track update to alert display
- Minimum alert accuracy: 95% detection rate, <5% false alert rate
- System availability: 99.999% uptime requirement

**Operational Constraints:**
- Must integrate with existing ATC infrastructure
- Must support incremental deployment and rollback
- Must maintain compatibility with legacy flight plan formats

### 2.6 Assumptions and Dependencies

**Assumptions:**
1. Surveillance data quality meets minimum ICAO standards
2. Flight plan data is available and updated in real-time
3. Controllers are trained on SKYRADAR alert interpretation
4. Meteorological data is available with <5 minute update rate
5. Aircraft transponder data includes Mode S capabilities

**Dependencies:**
1. Radar surveillance system provides track updates at 4-5 second intervals
2. Flight Data Processing System provides current flight plan data
3. Weather information system provides wind, temperature, humidity data
4. Aeronautical database provides runway, airspace, and procedure definitions
5. Time synchronization via NTP or GPS for accurate time-based operations

---

## 3. System Features

This section provides a high-level summary of the eight major system features. Detailed functional requirements are specified in Section 4.

### 3.1 Short Term Conflict Alert (STCA)

Detects potential conflicts between aircraft and provides early warning to controllers. Includes specialized logic for suppressing nuisance alerts during parallel approach operations with Normal Operating Zones (NOZ) and No Transgression Zones (NTZ).

**Priority:** MEDIUM
**Safety Impact:** False (operational efficiency)

### 3.2 Minimum Safe Altitude Warning (MSAW)

Monitors aircraft altitude relative to terrain and obstacles during critical phases of flight (approach and departure). Generates alerts when aircraft descend below minimum safe altitude thresholds.

**Priority:** HIGH
**Safety Impact:** True (terrain collision prevention)

### 3.3 RVSM Non-Approval Alert

Monitors aircraft operating in Reduced Vertical Separation Minimum (RVSM) airspace to ensure only RVSM-approved aircraft operate at RVSM flight levels. Alerts controllers when non-approved aircraft enter RVSM airspace.

**Priority:** HIGH
**Safety Impact:** True (vertical separation assurance)

### 3.4 Arrival Manager (AMAN)

Optimizes arrival sequences by calculating time-based separation and adjusting aircraft positions within the arrival flow. Helps maximize runway throughput while maintaining required separation standards.

**Priority:** MEDIUM
**Safety Impact:** False (flow optimization)

### 3.5 Wake Vortex Separation Monitoring

Monitors separation between aircraft pairs considering wake turbulence categories and atmospheric conditions. Uses dynamic separation minima based on real-time weather data (crosswind, temperature, humidity).

**Priority:** HIGH
**Safety Impact:** True (wake turbulence encounter prevention)

### 3.6 RNP Approach Containment Monitoring

Validates that aircraft executing RNP (Required Navigation Performance) approaches remain within the defined containment area. Alerts when lateral deviation exceeds twice the RNP value for the procedure.

**Priority:** HIGH
**Safety Impact:** True (obstacle clearance during precision approaches)

### 3.7 CPDLC Message Timeout and Reversion

Monitors Controller-Pilot Data Link Communications (CPDLC) message acknowledgments and triggers voice communication reversion when safety-critical messages are not acknowledged within timeout thresholds.

**Priority:** HIGH
**Safety Impact:** True (clearance delivery assurance)

### 3.8 Departure Manager (DMAN)

Monitors departure slot compliance by comparing actual take-off times with assigned Target Take-Off Times (TTOT). Helps controllers maintain departure flow efficiency and comply with flow management restrictions.

**Priority:** MEDIUM
**Safety Impact:** False (departure flow optimization)

---

## 4. Functional Requirements

### 4.1 Conflict Detection and Resolution

#### 4.1.1 STCA - Suppression During Parallel Approaches

**Requirement ID:** SKYRADAR-STCA-041
**Parent Requirement:** ATCS-SSS-REQ-005855
**Derivation Status:** Partially
**Safety Impact:** No
**Verification Method:** Test
**Verification Level:** RL

**Requirement Statement:**

SKYRADAR shall flag STCA conflicts as suppressed for tracks located in NOZ if ALL of the following conditions are met:

| Condition # | Condition Description | Parameter Type |
|-------------|----------------------|----------------|
| 1 | The associated NTZ area is active | System State |
| 2 | The status of the NTZ areas manager is equal to OPERATIONAL | System State |
| 3 | The heading gap between each aircraft and the runway axis is lower than MAX_DELTA_HEADING | CSP |
| 4 | The current distance between the aircraft is kept above MinimalDistance (safety distance) | VSP |
| 5 | Each track is located within a different NOZ associated with an offline defined "parallel approach pair" of runways | Configuration |
| 6 | The "parallel approach pair" is in INDEPENDENT mode | System State |
| 7 | STCA_PARALLEL_APP_FPL_CHECK_FLAG is false OR the runway of each track's coupled FPL (if assigned) matches the runway linked to the NOZ where the track is located | Flag/Data |

**Rationale:** Alert inhibition on approach with NOZ and NTZ Areas prevents nuisance alerts during normal parallel approach operations while maintaining safety through geometric and procedural checks.

**SDS Rules Reference:** HLR_10 [cmats_snp] Partial derivation shall be avoided

---

### 4.2 Terrain and Altitude Monitoring

#### 4.2.1 MSAW - Minimum Safe Altitude Warning Generation

**Requirement ID:** SKYRADAR-MSAW-025
**Parent Requirement:** ATCS-SSS-REQ-006142
**Derivation Status:** Partially
**Safety Impact:** Yes
**Verification Method:** Test
**Verification Level:** RL

**Requirement Statement:**

SKYRADAR shall generate MSAW (Minimum Safe Altitude Warning) alerts for tracks if ALL of the following conditions are met:

| Condition # | Condition Description | Parameter Type |
|-------------|----------------------|----------------|
| 1 | The MSAW system status is equal to OPERATIONAL | System State |
| 2 | The track altitude is below the MSA (Minimum Safe Altitude) threshold defined for the current sector | Database/Track |
| 3 | The track is in APPROACH or DEPARTURE flight phase | Track State |
| 4 | The track vertical speed indicates descent or level flight (not climbing above MIN_CLIMB_RATE) | VSP/Track |
| 5 | The track is located within a monitored airspace zone where MSAW is active | Configuration |
| 6 | The track has valid altitude data with quality indicator equal to HIGH or MEDIUM | Track Quality |
| 7 | MSAW_EMERGENCY_OVERRIDE is false OR the track's transponder squawk code is NOT in emergency range (7500, 7600, 7700) | Flag/Track |

**Rationale:** Terrain clearance monitoring for approach and departure operations prevents controlled flight into terrain (CFIT) by alerting controllers when aircraft descend below safe altitudes.

**SDS Rules Reference:** HLR_15 [cmats_snp] Partial derivation shall be avoided

**Performance Requirements:**
- Alert generation latency: <2 seconds
- MSA threshold accuracy: ±50 feet
- False alert rate: <3% of total alerts

---

### 4.3 Airspace Compliance Monitoring

#### 4.3.1 RVSM - Non-Approval Alert Generation

**Requirement ID:** SKYRADAR-RVSM-033
**Parent Requirement:** ATCS-SSS-REQ-006500
**Derivation Status:** Partially
**Safety Impact:** Yes
**Verification Method:** Test
**Verification Level:** RL

**Requirement Statement:**

SKYRADAR shall generate RVSM (Reduced Vertical Separation Minimum) Non-Approval alerts for tracks if ALL of the following conditions are met:

| Condition # | Condition Description | Parameter Type |
|-------------|----------------------|----------------|
| 1 | The RVSM monitoring system status is equal to OPERATIONAL | System State |
| 2 | The track flight level is within RVSM airspace range (between RVSM_MIN_FL and RVSM_MAX_FL) | CSP/Track |
| 3 | The track RVSM approval status indicator is set to NOT_APPROVED or UNKNOWN | Track Data |
| 4 | The track altitude source quality indicator is equal to HIGH or MEDIUM | Track Quality |
| 5 | The track is located within an RVSM designated airspace zone where monitoring is active | Configuration |
| 6 | The track flight plan indicates IFR (Instrument Flight Rules) operation | Flight Plan |
| 7 | RVSM_EMERGENCY_EXCEPTION is false OR the track's transponder squawk code is NOT in emergency range (7500, 7600, 7700) | Flag/Track |

**Rationale:** RVSM compliance monitoring for flight operations in reduced vertical separation airspace ensures that only properly equipped and approved aircraft operate in RVSM airspace, maintaining the safety case for 1000ft vertical separation.

**SDS Rules Reference:** HLR_12 [cmats_snp] Partial derivation shall be avoided

**RVSM Airspace Characteristics:**

| Parameter | Typical Value | Notes |
|-----------|--------------|-------|
| RVSM_MIN_FL | FL290 | 29,000 feet |
| RVSM_MAX_FL | FL410 | 41,000 feet |
| Standard Vertical Separation | 1000 feet | Within RVSM airspace |
| Non-RVSM Separation | 2000 feet | Below FL290 or above FL410 |

---

### 4.4 Traffic Flow Management

#### 4.4.1 AMAN - Time-Based Arrival Sequencing

**Requirement ID:** SKYRADAR-ARR-044
**Parent Requirement:** ATCS-SSS-REQ-007125
**Derivation Status:** Partially
**Safety Impact:** No
**Verification Method:** Test
**Verification Level:** RL

**Requirement Statement:**

SKYRADAR shall automatically adjust arrival sequence positions for tracks if ALL of the following conditions are met:

| Condition # | Condition Description | Parameter Type |
|-------------|----------------------|----------------|
| 1 | The AMAN (Arrival Manager) system status is equal to OPERATIONAL | System State |
| 2 | The track is in ARRIVAL flight phase with valid time-to-threshold prediction | Track State |
| 3 | The track is located within the Extended Terminal Maneuvering Area (E-TMA) boundary defined for the arrival airport | Configuration |
| 4 | The calculated arrival delay is greater than AMAN_MIN_DELAY_THRESHOLD (typically 120 seconds) | CSP/Calculation |
| 5 | The track has an assigned arrival runway with active AMAN sequencing enabled | Configuration |
| 6 | The potential sequence position change would not violate minimum time-based separation with preceding or following traffic (TBS_MIN_SEPARATION_TIME) | VSP/Safety Check |

**Rationale:** Automated arrival sequencing with time-based separation for traffic flow optimization improves runway throughput and reduces delay while maintaining safety separation.

**SDS Rules Reference:** HLR_18 [cmats_snp] Partial derivation shall be avoided

**AMAN Performance Targets:**

| Metric | Target Value |
|--------|-------------|
| Delay Reduction | 15-30% compared to manual sequencing |
| Sequence Stability | <2 position changes per flight |
| Throughput Improvement | 5-10% increased runway acceptance rate |

---

### 4.5 Separation Assurance

#### 4.5.1 Wake Vortex - Dynamic Separation Monitoring

**Requirement ID:** SKYRADAR-WV-045
**Parent Requirement:** ATCS-SSS-REQ-007240
**Derivation Status:** Partially
**Safety Impact:** Yes
**Verification Method:** Test
**Verification Level:** RL

**Requirement Statement:**

SKYRADAR shall generate wake vortex separation infringement alerts for track pairs if ALL of the following conditions are met:

| Condition # | Condition Description | Parameter Type |
|-------------|----------------------|----------------|
| 1 | The wake vortex monitoring system status is equal to OPERATIONAL | System State |
| 2 | Both tracks are in APPROACH or DEPARTURE flight phase on the same runway or parallel runways separated by less than WV_PARALLEL_RWY_DISTANCE (typically 760 meters) | CSP/Track |
| 3 | The leading aircraft wake turbulence category is HEAVY or SUPER and the following aircraft category is at least two categories lower (per ICAO RECAT standards) | Track Data |
| 4 | The measured separation distance between the two tracks is below the dynamic wake vortex separation minimum calculated based on current meteorological conditions (crosswind, temperature, humidity from WEATHER_DATA_SOURCE) | VSP/Calculation |
| 5 | Both tracks have valid position and altitude data with quality indicator equal to HIGH | Track Quality |
| 6 | WV_TIME_BASED_MODE is true AND time-based separation is below WV_MIN_TIME_SEPARATION, OR flag is false AND distance-based separation is below WV_MIN_DISTANCE_SEPARATION | VSP/Flag |
| 7 | WV_EMERGENCY_OVERRIDE is false OR neither track's transponder squawk code is in emergency range (7500, 7600, 7700) | Flag/Track |

**Rationale:** Dynamic wake turbulence separation reduction based on atmospheric conditions and aircraft characteristics allows for optimized separation standards while maintaining safety.

**SDS Rules Reference:** HLR_22 [cmats_snp] Partial derivation shall be avoided

**ICAO RECAT Wake Turbulence Categories:**

| Category | Aircraft Examples | Wake Characteristic |
|----------|------------------|---------------------|
| SUPER (J) | A380 | Extreme wake |
| HEAVY (H) | B747, B777, A330 | Strong wake |
| UPPER MEDIUM (UM) | B767, A310 | Moderate wake |
| LOWER MEDIUM (LM) | B737, A320 | Light wake |
| SMALL (S) | Regional jets | Minimal wake |

**Dynamic Separation Matrix:**

| Leader → Follower | Strong Crosswind (>15kt) | Moderate Crosswind (5-15kt) | Light Crosswind (<5kt) |
|-------------------|--------------------------|----------------------------|------------------------|
| SUPER → HEAVY | 4 NM | 5 NM | 6 NM |
| HEAVY → MEDIUM | 3 NM | 4 NM | 5 NM |
| HEAVY → SMALL | 4 NM | 5 NM | 6 NM |

---

### 4.6 Navigation Performance Monitoring

#### 4.6.1 RNP - Approach Containment Validation

**Requirement ID:** SKYRADAR-RNP-046
**Parent Requirement:** ATCS-SSS-REQ-007355
**Derivation Status:** Partially
**Safety Impact:** Yes
**Verification Method:** Test
**Verification Level:** RL

**Requirement Statement:**

SKYRADAR shall generate RNP (Required Navigation Performance) containment violation alerts for tracks if ALL of the following conditions are met:

| Condition # | Condition Description | Parameter Type |
|-------------|----------------------|----------------|
| 1 | The RNP monitoring system status is equal to OPERATIONAL | System State |
| 2 | The track is executing an RNP approach procedure with approach type indicator set to RNP or RNP_AR (Authorization Required) | Track/Procedure |
| 3 | The track flight plan indicates the aircraft RNP capability value is adequate for the published procedure (aircraft RNP ≤ procedure required RNP from RNP_PROCEDURE_DATABASE) | CSP/Flight Plan |
| 4 | The track lateral deviation from the published RNP approach path exceeds the RNP containment limit (deviation > 2 × RNP value for more than RNP_DEVIATION_TIME_THRESHOLD seconds) | VSP/Calculation |
| 5 | The track is located within the RNP procedure coverage volume defined in the approach chart (typically final approach segment beyond FAF) | Configuration |
| 6 | The track GNSS integrity status indicator is equal to AVAILABLE with horizontal protection level (HPL) less than the alert limit for the RNP value | Track Data |
| 7 | RNP_VISUAL_OVERRIDE is false OR the track has not reported visual conditions with the runway in sight to ATC | Flag/Track |

**Rationale:** Monitoring of Required Navigation Performance approach path containment and precision for advanced procedure compliance ensures obstacle clearance in terminal areas with reduced obstacle clearance areas.

**SDS Rules Reference:** HLR_25 [cmats_snp] Partial derivation shall be avoided

**RNP Approach Types:**

| RNP Type | Required RNP Value | Typical Application | Authorization |
|----------|-------------------|---------------------|---------------|
| RNP APCH | 0.3 NM | Standard terminal approaches | Basic GNSS |
| RNP AR APCH | 0.1 - 0.3 NM | Complex terrain airports | Special authorization |
| RNP 0.1 | 0.1 NM | Precision-like approaches | Advanced authorization |

**Containment Monitoring:**

```
         ┌─────────────────────────────────┐
         │   RNP Approach Path             │
         │                                 │
    ─ ─ ─│─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─
         │                                 │
    ─ ─ ┼─ ─ ─ ─ ─ ─X─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─   ← RNP containment (1×)
         │           │                     │
    ─ ─ ─│─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─  ← Alert threshold (2×)
         │           └─ Aircraft position  │
         │                                 │
         └─────────────────────────────────┘
```

---

### 4.7 Data Link Communications

#### 4.7.1 CPDLC - Message Timeout and Voice Reversion

**Requirement ID:** SKYRADAR-CPDLC-047
**Parent Requirement:** ATCS-SSS-REQ-007470
**Derivation Status:** Partially
**Safety Impact:** Yes
**Verification Method:** Test
**Verification Level:** RL

**Requirement Statement:**

SKYRADAR shall generate CPDLC message timeout alerts and trigger voice communication reversion for tracks if ALL of the following conditions are met:

| Condition # | Condition Description | Parameter Type |
|-------------|----------------------|----------------|
| 1 | The CPDLC system status is equal to OPERATIONAL | System State |
| 2 | The track has an active CPDLC connection with logon status set to CONNECTED and data authority is CURRENT | Track State |
| 3 | A CPDLC uplink message of type CLEARANCE or INSTRUCTION has been transmitted to the aircraft with message status equal to SENT | Message State |
| 4 | The elapsed time since message transmission exceeds the response timeout threshold (CPDLC_RESPONSE_TIMEOUT: typically 60s for clearances, 30s for time-critical instructions) | CSP/Timer |
| 5 | No CPDLC downlink response (WILCO, UNABLE, STANDBY, or ROGER) has been received from the aircraft for the pending message | Message State |
| 6 | The message criticality level is set to HIGH or SAFETY_CRITICAL requiring mandatory acknowledgment | Message Attribute |
| 7 | CPDLC_VOICE_BACKUP_ENABLED is true AND the controller position has active voice communication capability with frequency assigned to the track's current sector | Flag/Configuration |

**Rationale:** Controller-Pilot Data Link Communications timeout monitoring and voice reversion alerting for safety-critical clearances ensures communication loop closure and prevents loss of clearance delivery.

**SDS Rules Reference:** HLR_28 [cmats_snp] Partial derivation shall be avoided

**CPDLC Message Types and Timeouts:**

| Message Type | Criticality | Response Timeout | Voice Reversion |
|-------------|-------------|------------------|-----------------|
| Altitude Clearance | SAFETY_CRITICAL | 30 seconds | Mandatory |
| Heading Instruction | HIGH | 30 seconds | Mandatory |
| Speed Instruction | HIGH | 60 seconds | Mandatory |
| Route Clearance | MEDIUM | 60 seconds | Optional |
| Information | LOW | N/A | Not required |

**Communication State Diagram:**

```
    ┌─────────┐
    │ IDLE    │
    └────┬────┘
         │ Send message
         ▼
    ┌─────────┐          Timeout
    │ SENT    ├──────────────────┐
    └────┬────┘                  │
         │ Response received     │
         ▼                       ▼
    ┌─────────┐            ┌─────────┐
    │ ACKED   │            │ TIMEOUT │
    └─────────┘            └────┬────┘
                                │ Trigger voice
                                ▼
                           ┌─────────┐
                           │ VOICE   │
                           │REVERSION│
                           └─────────┘
```

---

### 4.8 Departure Management

#### 4.8.1 DMAN - Departure Slot Compliance

**Requirement ID:** SKYRADAR-DMAN-048
**Parent Requirement:** ATCS-SSS-REQ-007585
**Derivation Status:** Partially
**Safety Impact:** No
**Verification Method:** Test
**Verification Level:** RL

**Requirement Statement:**

SKYRADAR shall generate departure sequence slot violation alerts for tracks if ALL of the following conditions are met:

| Condition # | Condition Description | Parameter Type |
|-------------|----------------------|----------------|
| 1 | The DMAN (Departure Manager) system status is equal to OPERATIONAL | System State |
| 2 | The track has an assigned Target Take-Off Time (TTOT) with departure sequence position allocated by DMAN | Track Data |
| 3 | The track is in DEPARTURE_GROUND or DEPARTURE_TAXI flight phase with valid ground position data | Track State |
| 4 | The calculated actual take-off time prediction exceeds the assigned TTOT by more than DMAN_SLOT_TOLERANCE (typically ±5 minutes) | CSP/Calculation |
| 5 | The departure runway assigned to the track has active DMAN sequencing enabled with current departure demand exceeding DMAN_ACTIVATION_THRESHOLD (typically 8 departures per hour) | VSP/Configuration |
| 6 | The track departure route or initial departure fix matches one of the DMAN managed flow constraint points defined in DMAN_REGULATED_ROUTES | CSP/Flight Plan |

**Rationale:** Automated departure sequence monitoring and Target Off-Block Time (TOBT) compliance for flow management optimization helps maintain airport departure capacity and comply with ATFM slots.

**SDS Rules Reference:** HLR_31 [cmats_snp] Partial derivation shall be avoided

**DMAN Sequencing Parameters:**

| Parameter | Typical Value | Purpose |
|-----------|--------------|---------|
| TTOT Tolerance | ±5 minutes | Acceptable deviation window |
| Activation Threshold | 8 departures/hour | Minimum traffic to enable DMAN |
| Sequence Update Interval | 60 seconds | Frequency of TTOT recalculation |
| Maximum Delay Absorption | 15 minutes | Maximum taxi delay allowed |

---

## 5. Non-Functional Requirements

### 5.1 Performance Requirements

| Req ID | Description | Target Value | Measurement Method |
|--------|-------------|--------------|-------------------|
| NFR-001 | Alert Generation Latency | <2 seconds | Time from track update to alert display |
| NFR-002 | Track Processing Capacity | 500 tracks simultaneous | Maximum concurrent aircraft |
| NFR-003 | System Response Time | <500ms | User interface responsiveness |
| NFR-004 | Database Query Performance | <100ms | Configuration parameter retrieval |
| NFR-005 | Alert Update Rate | 4-5 seconds | Synchronized with radar update rate |

### 5.2 Safety Requirements

| Req ID | Description | Target Value |
|--------|-------------|--------------|
| NFR-101 | Safety-Critical Alert Reliability | 99.9% detection rate |
| NFR-102 | False Alert Rate | <5% of total alerts |
| NFR-103 | System Failure Detection Time | <10 seconds |
| NFR-104 | Redundancy Switch-Over Time | <2 seconds |
| NFR-105 | Data Integrity | 100% (checksums and validation) |

### 5.3 Reliability and Availability

| Req ID | Description | Target Value |
|--------|-------------|--------------|
| NFR-201 | System Availability | 99.999% uptime |
| NFR-202 | Mean Time Between Failures (MTBF) | >8760 hours (1 year) |
| NFR-203 | Mean Time To Repair (MTTR) | <30 minutes |
| NFR-204 | Backup System Sync Time | <5 seconds |

### 5.4 Maintainability

| Req ID | Description | Requirement |
|--------|-------------|------------|
| NFR-301 | Parameter Modification | Runtime configuration without system restart |
| NFR-302 | Software Update Window | <4 hours for major updates |
| NFR-303 | Diagnostic Logging | Comprehensive event logging with severity levels |
| NFR-304 | Remote Monitoring | Web-based system health dashboard |

### 5.5 Security Requirements

| Req ID | Description | Requirement |
|--------|-------------|------------|
| NFR-401 | Access Control | Role-based authentication (RBAC) |
| NFR-402 | Audit Trail | All configuration changes logged |
| NFR-403 | Data Encryption | TLS 1.3 for network communications |
| NFR-404 | Password Policy | Minimum 12 characters, complexity requirements |

---

## 6. Appendices

### 6.1 Glossary of Terms

| Term | Definition |
|------|------------|
| **AMAN** | Arrival Manager - automated system for optimizing arrival sequences |
| **CPDLC** | Controller-Pilot Data Link Communications |
| **CSP** | Configuration System Parameter - offline configured parameter |
| **DMAN** | Departure Manager - automated system for departure sequencing |
| **E-TMA** | Extended Terminal Maneuvering Area |
| **FAF** | Final Approach Fix |
| **GNSS** | Global Navigation Satellite System |
| **HPL** | Horizontal Protection Level |
| **IFR** | Instrument Flight Rules |
| **MSAW** | Minimum Safe Altitude Warning |
| **NOZ** | Normal Operating Zone (parallel approaches) |
| **NTZ** | No Transgression Zone (parallel approaches) |
| **RECAT** | Reduced Wake Turbulence Separation |
| **RNP** | Required Navigation Performance |
| **RNP AR** | RNP Authorization Required |
| **RVSM** | Reduced Vertical Separation Minimum |
| **STCA** | Short Term Conflict Alert |
| **TBS** | Time-Based Separation |
| **TOBT** | Target Off-Block Time |
| **TTOT** | Target Take-Off Time |
| **VSP** | Variable System Parameter - runtime adjustable parameter |

### 6.2 Acronyms

| Acronym | Expansion |
|---------|-----------|
| ADS-B | Automatic Dependent Surveillance-Broadcast |
| ATC | Air Traffic Control |
| ATFM | Air Traffic Flow Management |
| CFIT | Controlled Flight Into Terrain |
| DAL | Development Assurance Level |
| EASA | European Union Aviation Safety Agency |
| EUROCAE | European Organisation for Civil Aviation Equipment |
| FAA | Federal Aviation Administration |
| FPL | Flight Plan |
| HMI | Human-Machine Interface |
| ICAO | International Civil Aviation Organization |
| MSA | Minimum Safe Altitude |
| NM | Nautical Mile |
| PANS-ATM | Procedures for Air Navigation Services - Air Traffic Management |
| RTCA | Radio Technical Commission for Aeronautics |
| SARPS | Standards and Recommended Practices |
| SRS | Software Requirements Specification |

### 6.3 Requirements Traceability Matrix

| SKYRADAR Req ID | Parent SSS Req | Feature Area | Safety Critical | Verification Status |
|----------------|----------------|--------------|-----------------|---------------------|
| SKYRADAR-STCA-041 | ATCS-SSS-REQ-005855 | Conflict Detection | No | Pending |
| SKYRADAR-MSAW-025 | ATCS-SSS-REQ-006142 | Terrain Monitoring | Yes | Pending |
| SKYRADAR-RVSM-033 | ATCS-SSS-REQ-006500 | Airspace Compliance | Yes | Pending |
| SKYRADAR-ARR-044 | ATCS-SSS-REQ-007125 | Flow Management | No | Pending |
| SKYRADAR-WV-045 | ATCS-SSS-REQ-007240 | Separation Assurance | Yes | Pending |
| SKYRADAR-RNP-046 | ATCS-SSS-REQ-007355 | Navigation Performance | Yes | Pending |
| SKYRADAR-CPDLC-047 | ATCS-SSS-REQ-007470 | Data Link | Yes | Pending |
| SKYRADAR-DMAN-048 | ATCS-SSS-REQ-007585 | Flow Management | No | Pending |

### 6.4 Configuration Parameters Reference

#### Configuration System Parameters (CSP)

| Parameter Name | Type | Range | Default | Description |
|----------------|------|-------|---------|-------------|
| MAX_DELTA_HEADING | Float | 0-45° | 20° | Maximum heading deviation for parallel approach |
| RVSM_MIN_FL | Integer | 0-999 | 290 | RVSM airspace lower boundary (FL) |
| RVSM_MAX_FL | Integer | 0-999 | 410 | RVSM airspace upper boundary (FL) |
| AMAN_MIN_DELAY_THRESHOLD | Integer | 0-600s | 120s | Minimum delay to trigger AMAN sequencing |
| WV_PARALLEL_RWY_DISTANCE | Float | 0-2000m | 760m | Max runway spacing for wake vortex monitoring |
| CPDLC_RESPONSE_TIMEOUT | Integer | 10-300s | 60s | CPDLC message acknowledgment timeout |
| DMAN_SLOT_TOLERANCE | Integer | 0-600s | 300s | TTOT deviation tolerance (±5 minutes) |

#### Variable System Parameters (VSP)

| Parameter Name | Type | Range | Default | Description |
|----------------|------|-------|---------|-------------|
| MinimalDistance | Float | 0.5-10 NM | 3.0 NM | Minimum safety distance (STCA) |
| MIN_CLIMB_RATE | Integer | 0-1000 ft/min | 300 ft/min | Minimum climb rate threshold (MSAW) |
| TBS_MIN_SEPARATION_TIME | Integer | 60-240s | 90s | Minimum time-based separation |
| WEATHER_DATA_SOURCE | Enum | MET/METAR/TAF | MET | Weather data source selection |
| WV_MIN_TIME_SEPARATION | Integer | 60-180s | 120s | Wake vortex minimum time separation |
| WV_MIN_DISTANCE_SEPARATION | Float | 2-8 NM | 5 NM | Wake vortex minimum distance separation |
| RNP_DEVIATION_TIME_THRESHOLD | Integer | 5-60s | 15s | RNP deviation persistence time |
| DMAN_ACTIVATION_THRESHOLD | Integer | 1-20/hr | 8/hr | Minimum departure rate for DMAN |

---

**Document Control**

| Attribute | Value |
|-----------|-------|
| Classification | Internal Use Only |
| Distribution | Engineering Team, Safety Assessment, Certification Authority |
| Review Cycle | Quarterly or upon major requirement changes |
| Approval Required | System Engineering Manager, Safety Manager, Chief Engineer |
| Next Review Date | 2025-03-16 |

---

*End of Software Requirements Specification*
