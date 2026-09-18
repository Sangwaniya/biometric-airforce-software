# Project Requirements Document (PRD)
## Centralized eSSL Biometric, ANPR Vehicle Intelligence & Visitor Command Platform

### 1. Executive Overview & Problem Statement
The objective of this project is to build an enterprise-grade, 100% on-premises, air-gapped Centralized Security & Access Management Platform for an Air Force Station / High-Security Facility. 

The system replaces fragmented setups by integrating:
1. **eSSL Multi-Biometric Hardware** (Face, Fingerprint, and RFID Card all-in-one terminals).
2. **Automated Number Plate Recognition (ANPR)** camera feeds cross-referenced with a locally hosted vehicle registry (RC, Driving License, Insurance, Pollution/PUC, and expiry countdowns).
3. **Visitor & Host Relationship Management** featuring offline Aadhaar QR onboarding, color-coded security zone passes, and real-time host employee linking.
4. **Centralized Workstation Visibility Dashboard** providing real-time intelligence on present vs. absent employees, active on-premise headcounts, vehicles inside the station, overstay alarms, and emergency muster rolls.

---

### 2. Target Users & Stakeholders

| User Role | Description & Primary Objectives |
| :--- | :--- |
| **Station Security Officer / Super Admin** | Full visibility over base security, system policies, user clearance levels, vehicle compliance, and forensic audit logs. |
| **Gate Sentry / Guard Post Operator** | Operates gate entry/exit lanes; monitors ANPR detections, face punches, color-coded LED broadcast alerts (Green/Yellow/Red), and executes manual boom barrier overrides. |
| **Reception / Visitor Desk Operator** | Rapid onboarding of visitors via 2D Aadhaar QR scanning, host verification, RFID badge assignment, and custom pass badge printing. |
| **HR / Administrative Officer** | Monitors daily employee attendance (Present, Absent, Late, On-Duty), department rosters, and dependent/domestic staff validities. |
| **Provost Marshal / Security Auditor** | Investigates overstay violations, blacklisted vehicle attempts, zone breaches, and inspects tamper-evident SHA-256 audit trails. |

---

### 3. Core Functional Requirements

#### 3.1. Employee Master Hierarchy & Dependent Linking
- **Primary Master ID**: Unique centralized identity for each Air Force personnel / employee (e.g. Master ID `32` for Wg Cdr Rajesh Sharma, Service No: `28491-F`).
- **Hierarchical Child Identities**: Directly linked child records:
  - `.1`: Spouse (e.g., `32.1`)
  - `.2`, `.3`: Children / Dependent Parents (e.g., `32.2`)
  - `.D1`, `.D2`: Domestic Staff (Cook, Driver, Maid) with police verification status and time-bound pass expiry.
  - `.G1`: Registered Private Guests.
- **Cascading Security Policy**: If a Master ID is suspended, transferred, or posted out, all associated child IDs (especially domestic staff and guests) are automatically blocked across all eSSL terminals.

#### 3.2. eSSL Hardware Biometric Integration (All-in-One: Face, Fingerprint, RFID)
The centralized server must interface with eSSL hardware (e.g., uFace 302, SilkBio 101TC, MB160, AiFace series) supporting **three flexible communication channels**:
1. **Channel 1 - Direct Standalone SDK**: Direct network communication using eSSL's `zkemkeeper.dll` / Standalone SDK over TCP/UDP port 4370 for real-time event callbacks (`OnAttTransactionEx`) and two-way face/fingerprint template deployment.
2. **Channel 2 - Web API & ADMS HTTP Push**: Native listener supporting eSSL SOAP Web Services (`WebAPIService.asmx`) and HTTP push (`/iclock/cdata`) where devices automatically push punches to the server.
3. **Channel 3 - Direct SQL Database Synchronization**: Real-time bi-directional database connector to eSSL's `eTimeTrackLite` backend database (MS SQL Server / PostgreSQL / MySQL), pulling employees, logs, and device statuses directly.

#### 3.3. Vehicle Validation & ANPR Intelligence
- **ANPR Video Ingestion**: Processes RTSP streams from gate cameras to detect, crop, and normalize vehicle license plates (both civilian HSRP formats like `DL01AB1234` and military defence arrow formats like `↑21D123456A`).
- **Locally Hosted Document Registry**: Each vehicle is mapped to an employee or visitor and tracks:
  - Registration Certificate (RC) number and expiry.
  - Driving License (DL) number, holder name, and expiry.
  - Insurance policy number, insurer, and expiry date.
  - Pollution Under Control (PUC) certificate expiry date.
  - Base Vehicle Entry Pass sticker / UHF RFID tag ID.
- **Document Expiry Analytics**:
  - Exact countdown in days and months for Insurance, PUC, and DL.
  - Identification of documents expiring within the current calendar month, within 30 days, or already expired.
- **Three-Tier Gate Alert Output**:
  - 🟢 **GREEN (All Clear)**: All documents valid beyond current month. Barrier opens.
  - 🟡 **YELLOW (Expiring Soon)**: Valid today, but Insurance or RC expires within current calendar month. LED displays warning; sentry alerted.
  - 🔴 **RED (Expired / Unregistered / Blacklisted)**: Document expired, unregistered vehicle, or security blacklist. Barrier halted; audio alert triggered.
- **Gate LED Display Broadcasting**: Sends structured text and color packets to outdoor gate LED matrix display screens over UDP/TCP.

#### 3.4. Visitor Management & Offline Aadhaar QR Onboarding
- **Rapid Offline Onboarding**: Decodes UIDAI 2048-bit digitally signed QR codes (both V1 XML and V2 compressed binary) completely offline.
- **DPDP-23 Privacy & Zero-Biometric Guarantee**:
  - Strictly **ZERO** visitor biometric capture (no fingerprint or iris scanning).
  - Aadhaar number is masked to last 4 digits (`XXXX-XXXX-1234`).
  - Visitor photograph extracted lossless from the compressed QR stream for badge printing.
- **Host Employee Verification**: Visitor is linked to an active Master ID (host officer/resident), validating host presence and quarter details.
- **Color-Coded Security Zones & RFID Encoding**:
  - **Zone A (Green)**: Residential & Admin Area
  - **Zone B (Orange)**: Technical Area, Workshops, and Hangars
  - **Zone C (Red)**: Flight Line, ATC, and Ammunition Depot (Strict Escort Required)
- **Badge Printing**: Custom thermal badge output featuring visitor photo, host info, validity hours, permitted zone colors, and anti-tamper QR code.

#### 3.5. Workstation Visibility Dashboard & Metrics
- **Real-Time Attendance Intelligence**:
  - **Present vs. Absent**: Live breakdown of employees on-duty vs absent based on today's eSSL punches.
  - **Shift & Department Filters**: Filter by Squadron, Wing, Rank, and Shift timing.
- **On-Premise Headcount & Live Tracking**:
  - Headcount tally of everyone currently inside station perimeter (Employees, Dependents, Visitors, Vehicles).
  - Real-time list of "Entered Premise But Not Exited".
- **Automated Overstay Watchdog**:
  - Real-time countdown timer against approved visitor pass duration.
  - Visual strobe and audio horn trigger when a visitor overstays permitted hours.
  - Displays host quarter, vehicle plate, and phone number for immediate Provost patrol dispatch.
- **Emergency Muster Roll**: One-click generation of an emergency evacuation roll listing all individuals physically inside the facility.

---

### 4. Security, Compliance & Licensing Requirements
1. **100% On-Premises & Air-Gapped**: Fully functional on an isolated LAN without internet access or external cloud services.
2. **AES-256 Encryption**: AES-256-GCM authenticated encryption for all PII fields at rest and TLS 1.3 across the station LAN.
3. **DPDP-23 Compliance**: Strict data minimization, purpose recording, and automated 6-month statutory retention anonymization scheduler.
4. **CERT-In VAPT Certified Architecture**: Hardened against OWASP Top 10, strict CSP, parameterized queries, rate limiting, and tamper-proof sessions.
5. **6-Month Searchable Forensic Audit Ledger**: Append-only log with SHA-256 cryptographic chain verification to prevent retrospective tampering.
6. **Perpetual One-Time Purchase & Anti-Vendor Lock-in**: Full master credentials handover, open REST APIs, and un-obfuscated standard database schema for long-term AMC updates.
