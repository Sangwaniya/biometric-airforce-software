# Implementation Roadmap & Phases (Phases.md)
## Centralized eSSL Biometric, ANPR Vehicle Intelligence & Visitor Command Platform

To ensure methodical delivery and rigorous verification, development is divided into 6 manageable execution phases:

---

### Phase 1: Foundation, Database Architecture & Security Engine
- **Objective**: Establish the core on-premises runtime, relational database models, cryptographic engines, and Role-Based Access Control (RBAC).
- **Deliverables**:
  - Relational database schema (`master_identities`, `child_identities`, `vehicles`, `vehicle_documents`, `visitors`, `gate_transactions`, `forensic_audit_logs`).
  - Master ID hierarchy management (Master ID e.g. `32`, Spouse `.1`, Child `.2`, Domestic Staff `.D1`, Guest `.G1`).
  - Cascading status propagation engine (suspending Master ID automatically revokes child/staff passes).
  - AES-256-GCM encryption at rest for sensitive PII.
  - Append-only SHA-256 chained forensic audit ledger.
  - Authentication router with PBKDF2 hashing and local JWT session tokens.
- **Verification Gate**:
  - Automated unit tests asserting Master/Child ID creation, cascading blocks, and cryptographic chain verification.

---

### Phase 2: eSSL Biometric Integration Layer (Tri-Mode Ingestion)
- **Objective**: Implement communication interfaces with eSSL All-in-One Biometric Terminals (Face, Fingerprint, RFID Card).
- **Deliverables**:
  - **Mode 1 (Direct SDK)**: Background C# .NET Bridge (`eSSLBridge.exe`) compiled with `Interop.zkemkeeper.dll` listening on TCP port 4370.
  - **Mode 2 (Web API & ADMS Push)**:
    - SOAP 1.1 Web Service (`/iclock/WebAPIService.asmx`) implementing `AddEmployee`, `BlockUnblockUser`, `GetTransactionsLog`, and `GetCommandStatus`.
    - HTTP ADMS Push endpoint (`/iclock/cdata`) receiving live punches from eSSL terminals.
  - **Mode 3 (Direct SQL Sync)**: Connector to eSSL's `eTimeTrackLite` MS SQL Server/PostgreSQL database to pull employees and attendance logs.
  - Two-way user and face/fingerprint template synchronization.
- **Verification Gate**:
  - Verification of real-time punch ingestion (< 500ms), biometric template upload, and fallback handling when devices go offline.

---

### Phase 3: ANPR Camera Pipeline, Vehicle Registry & Expiry Engine
- **Objective**: Deploy the edge license plate recognition pipeline and automated vehicle document compliance verification.
- **Deliverables**:
  - RTSP video stream ingestion from gate entry/exit cameras.
  - Edge ANPR engine (YOLOv8 + CRNN OCR) supporting Indian civilian (HSRP) and military defence arrow plate formats.
  - Vehicle document registry: RC, Driving License (DL), Insurance, and Pollution Under Control (PUC).
  - Document expiry engine:
    - Calculates countdown in days and months.
    - Evaluates Three-Tier Gate Status:
      - 🟢 **GREEN**: All documents valid beyond current month.
      - 🟡 **YELLOW**: Insurance or RC expiring within current calendar month.
      - 🔴 **RED**: Document expired, unregistered vehicle, or blacklisted.
- **Verification Gate**:
  - Test suite validating Green, Yellow, and Red scenarios and plate normalization accuracy.

---

### Phase 4: Visitor Onboarding, Offline Aadhaar QR & Zone Passes
- **Objective**: Deliver fast, privacy-compliant visitor onboarding and physical credential issuance.
- **Deliverables**:
  - 100% offline UIDAI 2048-bit QR parser (extracts Name, DOB, Gender, Address, and compressed photo without internet).
  - DPDP-23 compliance filter: Zero visitor biometric capture, masked Aadhaar (`XXXX-XXXX-1234`).
  - Host employee validation: Links visitor to active Master ID and validates host presence/quarters.
  - Security Zone assignment: Zone A (Green - Residential), Zone B (Orange - Technical), Zone C (Red - Flight Line).
  - Printable visitor badge generator with anti-tamper QR code and RFID card encoder.
- **Verification Gate**:
  - Offline QR parsing test against real sample Aadhaar vectors, asserting zero biometric storage and badge preview accuracy.

---

### Phase 5: Workstation Dashboard, Live Presence & Overstay Watchdog
- **Objective**: Build the central monitoring workstation with real-time intelligence and automated security alerting.
- **Deliverables**:
  - **Present vs. Absent Matrix**: Live attendance breakdown of on-duty personnel based on today's eSSL punches.
  - **Who Entered But Has Not Exited**: Live on-premise tracker displaying all active employees, dependents, visitors, and vehicles currently inside the perimeter.
  - **Automated Overstay Watchdog**:
    - Real-time countdown against visitor pass duration.
    - Automated red-alert generation with visual strobe and audio horn trigger.
    - Displays host quarter, vehicle plate, and phone number for immediate Provost patrol dispatch.
  - **Emergency Muster Roll**: 1-click export of everyone physically inside the station perimeter during emergencies.
  - Dynamic filters: Filter by Squadron, Wing, Rank, Gate ID, and Document Status.
- **Verification Gate**:
  - Live simulation of visitor check-in, overstay trigger, and check-out with headcounts updating in real-time.

---

### Phase 6: Gate Hardware Outputs, Security Hardening & Handover
- **Objective**: Connect physical gate outputs, enforce CERT-In VAPT hardening, and prepare handover documentation.
- **Deliverables**:
  - Outdoor Gate LED Matrix driver (UDP/TCP/Serial) broadcasting multi-line Green/Yellow/Red alerts.
  - Boom barrier relay actuator with dry contact trigger on Green and Sentry manual bypass logging.
  - CERT-In VAPT hardening: CSP, HSTS, X-Frame-Options headers, rate limiting, and SQLi protection.
  - 180-day automated DPDP-23 retention cleanup task.
  - 1-Click Windows batch launcher (`start_station_server.bat`) and system openness handover manifest.
- **Verification Gate**:
  - End-to-end regression test suite execution, hardware communication verification, and security audit report generation.
