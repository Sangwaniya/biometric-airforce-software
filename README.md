# Indian Air Force Station Security Management Platform

**Station Security Management, Multi-Biometric Access Control & ANPR Gateway**  
*100% On-Premises | Air-Gapped | Multi-Biometric (Face + Fingerprint + RFID) | CERT-In VAPT & DPDP-23 Compliant*

---

## Overview

The **Indian Air Force Station Security Management Platform** is an enterprise-grade, defense-ready security operations system designed for military station gates, sentry posts, and perimeter checkpoints. It unifies multi-biometric terminal integration, ANPR vehicle document intelligence, hierarchical personnel credentials, visitor lifecycle tracking, and automated emergency roll calls into a high-security, air-gapped web console.

---

## Key Capabilities

1. **Multi-Biometric Ingestion Layer**
   - Direct TCP socket driver (`port 4370`) and Web API integration for hardware terminals (eSSL, Biomax Indigo Face 8, ZKTeco).
   - High-throughput multi-modal punch ingestion (Visible Light Facial Recognition, Optical Fingerprint, and 13.56MHz/125kHz RFID).
   - Real-time WebSocket broadcasting to sentry gate monitors (`/ws/gate`).

2. **Master-Dependent Identity Hierarchy**
   - Root personnel structure: Air Force personnel retain a unique Master ID (e.g., `32`).
   - Dependent sub-identities:
     - Family members: `32.1` (Spouse), `32.2` (Child).
     - Domestic & contractor passes: `32.D1` (Cook), `32.D2` (Driver).
   - Immediate cascading security revocation: revoking or transferring Master ID `32` immediately invalidates dependent gate clearances.

3. **ANPR & Vehicle Document Intelligence**
   - Instant license plate OCR validation with three-tier traffic light barrier logic:
     - 🟢 **GREEN**: All documents valid (RC, DL, Insurance, PUC) > 30 days -> Automated Barrier Open.
     - 🟡 **YELLOW**: Valid with upcoming expiry (<= 30 days) -> Barrier Open + Sentry Warning Notice.
     - 🔴 **RED**: Expired document or unregistered plate -> Barrier Halted + Sentry Alert.

4. **Visitor Management & DPDP-23 Compliance**
   - Offline 2D Aadhaar QR code parser with cryptographic validation.
   - Privacy-preserving zero-biometric storage: Aadhaar numbers are masked (`XXXX-XXXX-1234`) with zero cloud transmissions.
   - Automated Overstay Engine: actively tracks visitor pass validity and issues alerts if visitors overstay station clearance.

5. **Live Station Tracking & Emergency Evacuation Roll**
   - Real-time presence ledger ("Entered but not exited") across all station gates.
   - One-click Emergency Evacuation Muster Roll generation accounting for all personnel, dependents, and visitors on base.

6. **Forensic Audit Ledger & Defense Security**
   - Tamper-evident SHA-256 cryptographic chain across all security transactions.
   - AES-256-GCM data encryption at rest.
   - Hardened CERT-In VAPT security headers (`X-Frame-Options`, `Content-Security-Policy`, `HSTS`, `X-Content-Type-Options`).

---

## Project Structure

```
Biometric-af-software/
│
├── server/                           # Main Application Backend & UI
│   ├── app/                          # FastAPI core application
│   │   ├── api/                      # REST API routes (identity, vehicle, visitor, etc.)
│   │   ├── core/                     # Security, config, audit loggers
│   │   ├── db/                       # SQLAlchemy models & SQLite/Postgres DB setup
│   │   └── modules/                  # Business logic (biometric, vehicle, compliance)
│   ├── biomax_bridge/                # Biomax C# standalone COM bridge & build scripts
│   ├── essl_bridge/                  # eSSL C# standalone COM bridge & build scripts
│   ├── static/                       # Workstation web console UI (Single Page App)
│   └── data/                         # Local database, passes, photos, and logs (git-ignored)
│
├── tests/                            # Comprehensive system integration tests
│   └── test_system.py                # 10-point end-to-end regression test suite
│
├── demo_iaf_presentation.py          # Interactive Executive Live Demo runner
├── run_platform.py                   # Main server launcher script
├── start_station_server.bat          # Windows one-click desktop launcher
├── requirements.txt                  # Python dependencies
└── Architecture.md                   # Detailed technical design & protocol architecture
```

---

## Getting Started

### Prerequisites

- **Python**: Version 3.10 or higher
- **Operating System**: Windows 10/11 or Windows Server (recommended for hardware COM bridge), Linux (supported in headless server mode)
- **Network**: Local Station LAN (no internet connection required; 100% air-gapped)

---

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Sangwaniya/biometric-airforce-software.git
   cd biometric-airforce-software
   ```

2. **Create and activate a virtual environment (optional but recommended)**:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

### Running the Server

#### Option A: Command Line
```bash
python run_platform.py
```

#### Option B: Windows Batch Launcher
Double-click `start_station_server.bat` in the root folder.

Upon startup, the database is automatically initialized and pre-seeded with baseline sample entities (Master ID `32`, vehicles, and sentry gates).

---

### Accessing the Web Consoles

Once the server is running:

| Service | URL | Description |
| :--- | :--- | :--- |
| **Station Workstation Console** | [http://127.0.0.1:8000](http://127.0.0.1:8000) | Live sentry gate monitor, attendance matrix & vehicle scanner |
| **Interactive API Documentation** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Swagger UI for exploring and testing API endpoints |
| **Terminal ADMS Push Endpoint** | `http://127.0.0.1:8000/iclock/cdata` | Push endpoint for eSSL/ZKTeco hardware terminals |
| **Biometric SOAP Web Service** | `http://127.0.0.1:8000/iclock/WebAPIService.asmx` | XML SOAP service for terminal sync |
| **Real-Time Sentry WebSocket** | `ws://127.0.0.1:8000/ws/gate` | Sentry post live stream |

---

## Running Automated Tests

A comprehensive 10-point test suite validates the health check, Master-Child hierarchy, vehicle document verification, biometric punches, Aadhaar QR parsing, overstay monitoring, and SHA-256 audit ledger integrity:

```bash
python tests/test_system.py
```

---

## Running the Live Executive Presentation Demo

To demonstrate system capabilities to leadership or inspect live gate animations:

```bash
python demo_iaf_presentation.py
```

This interactive runner provides:
- **Option 1**: Automated End-to-End Walkthrough (Full narrative presentation).
- **Option 2**: Interactive Capability Selector (Trigger individual vehicle checks, biometric punches, or emergency muster rolls).
- **Option 3**: Stress Test (Simulate peak gate traffic rush).

---

## Security & Compliance Specifications

- **Air-Gapped Operation**: Zero external API calls, tracking scripts, or CDN dependencies. All CSS/JS/fonts are self-contained.
- **Data Protection**: DPDP-23 compliant masking on sensitive IDs and Aadhaar numbers.
- **Forensic Audit**: Immutable cryptographic SHA-256 chaining prevents retroactive tampering with gate entry records.
- **Session Security**: Shift-based authentication with PBKDF2 password salting.

---

## License

Proprietary — Indian Air Force Station Security Management System.
