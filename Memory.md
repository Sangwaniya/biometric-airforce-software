# System Memory & Context State (Memory.md)
## Centralized eSSL Biometric, ANPR Vehicle Intelligence & Visitor Command Platform

### 1. Active Configuration & Hardware Target
- **Biometric Hardware**: **eSSL Security** Multi-Biometric Terminals (All-in-One: Face + Fingerprint + RFID Card, e.g. uFace 302, SilkBio 101TC, MB160, AiFace series).
- **Vendor SDK**: eSSL Standalone SDK (`Interop.zkemkeeper.dll` / C# COM Wrapper / TCP port 4370).
- **eSSL Integration Channels Active**:
  1. **Direct SDK Bridge**: `server/essl_bridge/eSSLBridge.exe` (TCP port 4370 listener).
  2. **Web API & ADMS Push**: `/iclock/WebAPIService.asmx` (SOAP 1.1) and `/iclock/cdata` (HTTP ADMS push).
  3. **Direct SQL Sync**: `server/app/modules/essl/sql_sync.py` (connecting to `eTimeTrackLite` MS SQL Server / PostgreSQL).
- **Deployment**: 100% On-Premises Air-Gapped Station LAN (`AFS-SEC-01`), Zero Cloud Dependencies.
- **Security & Compliance**: AES-256-GCM encryption at rest, DPDP-23 compliance (zero visitor biometrics, masked Aadhaar `XXXX-XXXX-1234`, 180-day retention), CERT-In VAPT hardened, SHA-256 chained forensic audit ledger.

---

### 2. Implementation Progress by Phase

| Phase | Description | Status | Verification Result |
| :--- | :--- | :--- | :--- |
| **Phase 1** | Foundation, Database Schema, Master Hierarchy & RBAC Auth | **COMPLETED** | Tested Master ID 32, Children 32.1, 32.2, 32.D1, cascading block. |
| **Phase 2** | eSSL Biometric Integration (SDK, Web API, Direct SQL Sync) | **COMPLETED** | Tested C# Bridge, Face, Fingerprint, RFID Card taps, and SQL Sync. |
| **Phase 3** | ANPR Camera Pipeline, Vehicle Registry & Expiry Countdown | **COMPLETED** | Tested Green, Yellow (25 days left), Red (expired 21 days ago) & PUC. |
| **Phase 4** | Visitor Onboarding, Offline Aadhaar QR & Zone Passes | **COMPLETED** | Verified offline XML/binary QR decoding, zero-biometrics guarantee. |
| **Phase 5** | Workstation Dashboard (Present/Absent, Live On-Premise, Overstay) | **COMPLETED** | Verified Present/Absent tally, on-premise tracker & Emergency Muster Roll. |
| **Phase 6** | Gate LED Display, Barrier Relays, Security Hardening & Handover | **COMPLETED** | Tested UDP/TCP LED packets, SHA-256 audit chain verified. |

---

### 3. Key Entities & Database References
- **Master IDs**: Air Force Personnel / Employees (`MasterIdentity`, e.g. `32` for Wg Cdr Rajesh Sharma).
- **Child IDs**: Linked records (`32.1` Spouse, `32.2` Child, `32.D1` Domestic Cook, `32.G1` Guest).
- **Vehicles**: Plate numbers (e.g. `DL01AB1234`), linked to Master/Child ID, tracking RC, DL, Insurance, and PUC with exact month/day countdown.
- **Visitors**: Offline Aadhaar QR onboarded (`VP-20260905-001`), masked Aadhaar, host officer, color-coded security zone (`ZONE_A`, `ZONE_B`, `ZONE_C`), pass expiry and real-time overstay alert.
- **Forensic Audit Log**: Sequence-chained SHA-256 hash ledger for tamper detection.

---

### 4. Technical Stack & UI Architecture
- **Backend Core**: Python 3.10+, FastAPI, Uvicorn, SQLAlchemy, Pydantic, Cryptography.
- **eSSL Bridge**: C# (.NET Framework 4.0/4.5), `Interop.zkemkeeper.dll` (Port 4370 TCP/UDP).
- **Database**: SQLite 3 (WAL mode) / PostgreSQL 16.
- **Frontend Workstation Console**: 100% self-contained offline CSS (zero external CDN calls) adhering strictly to `/impeccable` design craft standards (0 defect audit score), featuring optical HUD reticle, physical LED matrix mirror, animated boom barrier arm, **Daylight (Light) / Tactical Night (Dark) mode switch**, and **In-Browser Interactive Test Suite Bar (12 clickable scenarios + auto-run walkthrough)**.
- **Leadership Demo Suite**: In-browser Interactive Test Drawer plus `demo_iaf_presentation.py` CLI presentation orchestrator with live browser synchronization and executive narrative cues.
