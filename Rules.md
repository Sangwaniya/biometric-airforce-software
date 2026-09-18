# Rules & Engineering Boundaries (Rules.md)
## Centralized eSSL Biometric, ANPR Vehicle Intelligence & Visitor Command Platform

### 1. Vendor & Hardware Directives
- **Strict eSSL Focus**: All biometric device drivers, SDK references, and network listeners must explicitly target **eSSL Security** hardware (uFace, SilkBio, MB series, AiFace). All legacy Biomax terminology must be eliminated.
- **Tri-Mode Ingestion Support**:
  - Direct Standalone SDK (`zkemkeeper.dll` / TCP port 4370).
  - Web API & ADMS Push (`WebAPIService.asmx` SOAP + `/iclock/cdata` HTTP).
  - Direct SQL Connector (`eTimeTrackLite` MS SQL / PostgreSQL / MySQL).

---

### 2. Air-Gapped Network & Security Boundaries
- **100% On-Premises Isolation**: The platform must operate fully air-gapped without any internet connection.
- **No External Cloud Dependencies**:
  - NEVER make outbound requests to external APIs, telemetry, or analytics servers.
  - NEVER rely on external CDNs for runtime dependencies; all styles, fonts, and scripts must be local or fully offline-functional.
- **Data Protection & Encryption (FIPS / CERT-In)**:
  - Sensitive PII (names, contact details, facial photos, addresses) must be encrypted at rest using **AES-256-GCM**.
  - Passwords must be hashed using PBKDF2-HMAC-SHA256 (100,000 iterations).
  - Station LAN communications must support TLS 1.3 with internal Station Root CA.

---

### 3. Privacy & DPDP-23 Strict Rules
- **Zero Visitor Biometric Capture**:
  - NEVER capture, scan, or store visitor fingerprints or iris scans.
  - Aadhaar QR parsing must ONLY extract demographic information and the embedded photo for the physical visitor pass.
- **Aadhaar Data Masking**:
  - NEVER store unmasked 12-digit Aadhaar numbers in the database or logs.
  - Always store and display in masked format: `XXXX-XXXX-<last4>`.
- **Statutory Retention Purge**:
  - Visitor PII older than 180 days (6 months) must be automatically anonymized, retaining only non-identifiable numerical counts for historical auditing.

---

### 4. Software Stack: Whitelist & Blacklist

| Category | Allowed / Whitelisted | Prohibited / Blacklisted |
| :--- | :--- | :--- |
| **Backend** | Python 3.10+, FastAPI, Uvicorn, SQLAlchemy, Pydantic, C# .NET Framework (Standalone SDK bridge) | Django (unnecessary overhead), Flask, Ruby, PHP |
| **Database** | PostgreSQL 16, SQLite 3 (WAL mode) | MongoDB, Firebase, Supabase Cloud, DynamoDB |
| **Computer Vision** | OpenCV-Python, ONNX Runtime, NumPy, Torch/YOLO (local edge weights) | Cloud Vision APIs (AWS Rekognition, Google Cloud Vision, Azure Cognitive) |
| **Frontend** | Clean HTML5/Tailwind/CSS, React 18, Vite, TypeScript | External CDN script dependencies requiring live internet |
| **Hardware SDK** | `Interop.zkemkeeper.dll` (eSSL Standalone SDK), Socket Protocol (Port 4370) | Unverified proprietary third-party cloud bridges |

---

### 5. Resilience & Fault Tolerance
- **Hardware Disconnection Handling**:
  - If an eSSL terminal loses network connection, the server must log the failure without crashing and auto-reconnect via exponential backoff.
  - Offline punches stored on the device must automatically sync when connection is restored.
- **ANPR Stream Failure**:
  - If an ANPR camera stream drops, the Sentry Console must immediately notify the operator (`CAMERA SIGNAL LOST`) and provide an instant manual plate entry fallback with mandatory Sentry ID logging.
- **Audit Ledger Integrity**:
  - The forensic audit log is append-only. No deletion or updating of audit rows is permitted under any circumstances.
  - Every log must maintain an unbroken SHA-256 hash chain:
    $$\text{Hash}_n = \text{SHA-256}(\text{Hash}_{n-1} \parallel \text{Seq} \parallel \text{Timestamp} \parallel \text{PayloadHash})$$

---

### 6. Coding & Verification Standards
- **Parameterized Queries**: All database queries must use SQLAlchemy ORM or parameterized prepared statements. Raw string concatenation in SQL is strictly forbidden.
- **Input Sanitization**: All inputs (vehicle plates, names, phone numbers) must be strictly validated and sanitized against XSS and injection attacks.
- **Automated Regression Testing**: Every feature must have an automated test asserting its behavior before deployment.
