# Visual Design System & UX Standards (Design.md)
## Centralized eSSL Biometric, ANPR Vehicle Intelligence & Visitor Command Platform

### 1. Design Philosophy
The user interface is engineered for **High-Stress Mission-Critical Defense & Security Environments**:
- **High Visual Contrast**: Legible under harsh direct sunlight at outdoor gate sentry kiosks as well as low-light control rooms.
- **Immediate Information Hierarchy**: Critical security status (Green, Yellow, Red) must be identifiable in under 200 milliseconds.
- **Minimal Cognitive Overhead**: Operational sentry flows (Scan $\rightarrow$ Verify $\rightarrow$ Actuate Barrier) require zero unnecessary clicks.
- **Tactical Dark Aesthetic**: Reduces sentry eye strain during 8-hour continuous guard duty shifts.

---

### 2. Color Palette & Token System

```
  DEEP SLATE (950)        TACTICAL NAVY (900)       OPERATIONAL BLUE         ALL CLEAR GREEN
      #090D16                 #0F172A                 #2563EB                 #10B981
  (Base Background)      (Cards & Panels)        (Actions & Selection)     (Clear / Present)

  WARNING AMBER           DANGER CRIMSON          AIR FORCE GOLD           LED MATRIX BLACK
      #F59E0B                 #EF4444                 #FBBF24                 #000000
 (Expiring Current Month) (Expired / Overstay)   (Officer Insignia)      (Physical Mirror)
```

#### Status Token Mapping:

| Token | Hex Code | Purpose & Semantic Usage |
| :--- | :--- | :--- |
| `status-clear` | `#10B981` | 🟢 Vehicle RC/DL/Insurance all clear; employee present on-duty; barrier unlocked. |
| `status-warning` | `#F59E0B` | 🟡 Document expiring within current month; visitor pass expiring in < 30 mins. |
| `status-danger` | `#EF4444` | 🔴 Document expired; vehicle unregistered/blacklisted; visitor overstayed; unauthorized entry. |
| `status-offline` | `#64748B` | Device disconnected; terminal communication pending. |

#### Security Zone Color Scheme:
- **Zone A (Residential & Admin Area)**: `#10B981` (Green Badge)
- **Zone B (Technical Workshops & Hangars)**: `#F59E0B` (Orange Badge)
- **Zone C (Flight Line, ATC & Operational Area)**: `#EF4444` (Red Badge - Strictly Escorted)

---

### 3. Typography & Font Specifications

- **Primary UI Typeface**: `Inter`, `SF Pro Display`, `system-ui, sans-serif`
  - Body text: 13px / 14px font-medium for high legibility on 1080p and 720p sentry touchscreens.
  - Section headers: 16px / 18px font-bold uppercase with tracking (`tracking-wide`).
- **Data, Plates & Cryptographic Typeface**: `JetBrains Mono`, `Fira Code`, `monospace`
  - Vehicle License Plates: 20px font-black uppercase tracking-wider (`DL01AB1234`).
  - Master IDs & Pass IDs: 13px font-bold (`AF-32`, `VP-20260905-001`).
  - Forensic Hash Chains: 11px font-mono text-slate-400.
- **Physical LED Display Mirror**: `Courier New`, monospace with simulated CRT glow:
  - Font size: 24px - 32px font-black uppercase.
  - Text-shadow: `0 0 10px currentColor` on high-contrast `#000000` acrylic panel.

---

### 4. Layout & Information Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ TOP HEADER: Air Force Crest | Station Code | Air-gapped Badge | CERT-In & DPDP | Live IST   │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ NAVIGATION TABS: Gate Console | Master IDs | Vehicles | Visitor Desk | Command | Audit Logs │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│  ┌───────────────────────────────────────────────────┐  ┌────────────────────────────────┐  │
│  │ GATE CONSOLE (Left 65%)                           │  │ eSSL BIOMETRIC FEED (Right 35%)│  │
│  │                                                   │  │                                │  │
│  │  ┌─────────────────────────────────────────────┐  │  │  ┌──────────────────────────┐  │  │
│  │  │ HARDWARE LED MATRIX MIRROR                  │  │  │  │ eSSL Terminal Status     │  │  │
│  │  │ [DL01AB1234] Wg Cdr Rajesh Sharma           │  │  │  │ uFace 302 :4370 (ONLINE) │  │  │
│  │  │ [GREEN] ALL CLEAR - PROCEED                 │  │  │  └──────────────────────────┘  │  │
│  │  └─────────────────────────────────────────────┘  │  │                                │  │
│  │                                                   │  │  ┌──────────────────────────┐  │  │
│  │  Barrier Status: [OPEN]   [Manual Sentry Bypass]  │  │  │ Live Punches:            │  │  │
│  │                                                   │  │  │ • 14:02 - Wg Cdr Rajesh  │  │  │
│  │  ANPR Camera Lane 1: [Live RTSP Video Stream]     │  │  │ • 14:05 - Ramesh (Cook)  │  │  │
│  │  Vehicle Expiry Timeline: Insurance (8 Mo left)   │  │  └──────────────────────────┘  │  │
│  │                                                   │  │                                │  │
│  └───────────────────────────────────────────────────┘  └────────────────────────────────┘  │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 5. Specialized Component Specifications

#### 5.1. Vehicle Document Expiry Timeline Bar
- A multi-tier horizontal gauge displaying document status:
  - **RC**: Green pill (`Valid till 2028`)
  - **DL**: Green pill (`Valid till 2029`)
  - **Insurance**: Colored countdown badge:
    - $> 6$ months: Emerald Green (`8 Months Left`)
    - $1 - 6$ months: Blue/Cyan (`3 Months Left`)
    - $< 1$ month: Amber Warning (`Expires in 18 Days`)
    - Past date: Pulsing Red (`Expired on 15-Aug-2026!`)
  - **PUC**: Expiry date and validity status.

#### 5.2. Live Presence & On-Premise Metrics Panel
- 4-Card Executive Row:
  - **Estimated Total On-Station**: Large 32px bold number.
  - **Active Employees Present**: Green counter (`42 Present / 6 Absent`).
  - **Active Visitors Inside**: Blue counter (`4 Checked-in`).
  - **Overstay Alarms**: Pulsing crimson card (`1 Overstay Violation`).

#### 5.3. Overstay Alert Table & Visual Alarms
- When a visitor's pass window expires:
  - The row pulses with `bg-rose-950/40 border-rose-600`.
  - Elapsed overstay counter increments in real-time (`+45 MINS OVERSTAY`).
  - Quick action buttons: `Call Host Quarter`, `Dispatch Patrol`, `1-Click Checkout`.

#### 5.4. Thermal Visitor Pass Badge Print Layout
- Sized for standard 4x3 inch thermal badge printers (Zebra, TSC, Evolis):
  - Top: High-contrast station emblem and `INDIAN AIR FORCE - SECURITY VISITOR PASS`.
  - Photo: Visitor portrait decoded lossless from Aadhaar QR code.
  - Visitor Name (Bold uppercase) & Masked Aadhaar (`XXXX-XXXX-1098`).
  - Host details: Name, Rank, Unit, and Residential Quarter.
  - Security Zone: Bold solid color bar (Green for Zone A, Orange for Zone B, Red for Zone C).
  - Bottom: Anti-tamper verification QR code and surrender instructions.
