from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List
from pathlib import Path
import os
import json

from app.core.config import settings, BASE_DIR, PHOTO_DIR, PASS_DIR
from app.db.database import init_db, SessionLocal
from app.modules.compliance.vapt import VAPTSecurityHeadersMiddleware
from app.modules.essl.web_api import router as essl_soap_router
from app.api import (
    identity_router,
    biometric_router,
    essl_router,
    migration_router,
    vehicle_router,
    led_router,
    visitor_router,
    command_router,
    audit_router,
    auth_router
)

# Initialize FastAPI App
app = FastAPI(
    title="Indian Air Force Station Security Management Platform",
    version=settings.VERSION,
    description="Centralized Multi-Biometric, ANPR, Visitor & Command Security System"
)

# CERT-In VAPT Security Headers Middleware
app.add_middleware(VAPTSecurityHeadersMiddleware)

# CORS configuration (Air-gapped on-premise local network)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Directories for Photos and Passes
STATIC_DIR = BASE_DIR / "server" / "static" if (BASE_DIR / "server" / "static").exists() else BASE_DIR / "static"
if not STATIC_DIR.exists():
    STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app.mount("/static/photos", StaticFiles(directory=str(PHOTO_DIR)), name="photos")
app.mount("/static/passes", StaticFiles(directory=str(PASS_DIR)), name="passes")
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Air Force Station Security Platform Gateway"}

# Include Routers
app.include_router(auth_router)
app.include_router(identity_router)
app.include_router(biometric_router)
app.include_router(essl_router)
app.include_router(essl_soap_router)
app.include_router(migration_router)
app.include_router(vehicle_router)
app.include_router(led_router)
app.include_router(visitor_router)
app.include_router(command_router)
app.include_router(audit_router)

# WebSocket Connection Manager for Real-Time Sentry Gate Consoles
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.websocket("/ws/gate")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(json.dumps({"type": "ACK", "received": data}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.on_event("startup")
def on_startup():
    init_db()
    db = SessionLocal()
    try:
        from app.db.models import MasterIdentity, ChildIdentity, Vehicle, VehicleDocument, Visitor
        from app.modules.vehicle.validator import VehicleValidationService
        from datetime import datetime, date, timedelta

        # 1. Seed Master ID 32 if not present
        m = db.query(MasterIdentity).filter(MasterIdentity.master_id == "32").first()
        if not m:
            m = MasterIdentity(
                master_id="32",
                service_number="28491-F",
                rank="Wing Commander",
                full_name="Rajesh Sharma",
                unit="No. 45 Flying Squadron",
                residential_quarter="Quarter B-14, Officers Enclave",
                category="DEFENCE_OFFICER",
                security_clearance_level="LEVEL_3_RESTRICTED",
                phone="+91-9876543210",
                status="ACTIVE"
            )
            db.add(m)
            db.flush()

            # Seed Children (Spouse 32.1, Child 32.2, Domestic Help 32.D1)
            c1 = ChildIdentity(
                master_identity_id=m.id,
                child_id="32.1",
                relationship_type="SPOUSE",
                full_name="Pooja Sharma",
                rfid_card_number="CARD-3201",
                status="ACTIVE"
            )
            c2 = ChildIdentity(
                master_identity_id=m.id,
                child_id="32.2",
                relationship_type="CHILD",
                full_name="Aarav Sharma",
                rfid_card_number="CARD-3202",
                status="ACTIVE"
            )
            c3 = ChildIdentity(
                master_identity_id=m.id,
                child_id="32.D1",
                relationship_type="DOMESTIC_HELP",
                full_name="Ramesh Kumar (Cook)",
                rfid_card_number="CARD-32D1",
                police_verification_status="VERIFIED",
                valid_until=datetime.utcnow() + timedelta(days=120),
                status="ACTIVE"
            )
            db.add_all([c1, c2, c3])
            db.flush()

            # Seed Vehicles with Green, Yellow, and Red statuses
            # Vehicle 1: GREEN (All Clear)
            v_green = Vehicle(
                plate_number="DL01AB1234",
                master_identity_id=m.id,
                vehicle_type="FOUR_WHEELER",
                make_model="Tata Safari (Dark Blue)",
                status="ACTIVE"
            )
            db.add(v_green)
            db.flush()
            doc_green = VehicleDocument(
                vehicle_id=v_green.id,
                rc_number="RC-DL01AB1234",
                rc_expiry="2028-10-15",
                dl_number="DL-1420110012345",
                dl_expiry="2029-05-20",
                insurance_policy_number="POL-BAJAJ-889900",
                insurance_company="Bajaj Allianz",
                insurance_expiry="2027-11-30", # ~14 Months Left -> GREEN
                puc_expiry="2027-04-10",
                computed_status="GREEN",
                status_reason="All documents clear & valid"
            )
            db.add(doc_green)

            # Vehicle 2: YELLOW (Expiring current month)
            today = date.today()
            v_yellow = Vehicle(
                plate_number="HR26DQ5555",
                master_identity_id=m.id,
                vehicle_type="TWO_WHEELER",
                make_model="Royal Enfield 350",
                status="ACTIVE"
            )
            db.add(v_yellow)
            db.flush()
            _, month_end = VehicleValidationService.get_current_month_range(today)
            doc_yellow = VehicleDocument(
                vehicle_id=v_yellow.id,
                rc_number="RC-HR26DQ5555",
                rc_expiry="2029-01-01",
                insurance_policy_number="POL-ICICI-112233",
                insurance_company="ICICI Lombard",
                insurance_expiry=month_end.strftime("%Y-%m-%d"), # Expiring this month -> YELLOW
                puc_expiry="2027-01-01",
                computed_status="YELLOW",
                status_reason=f"Insurance expires on {month_end.strftime('%Y-%m-%d')} (this month)"
            )
            db.add(doc_yellow)

            # Vehicle 3: RED (Expired Insurance)
            v_red = Vehicle(
                plate_number="UP16AX9999",
                master_identity_id=m.id,
                vehicle_type="FOUR_WHEELER",
                make_model="Hyundai Creta",
                status="ACTIVE"
            )
            db.add(v_red)
            db.flush()
            doc_red = VehicleDocument(
                vehicle_id=v_red.id,
                rc_number="RC-UP16AX9999",
                rc_expiry="2028-01-01",
                insurance_policy_number="POL-NEWINDIA-774411",
                insurance_company="New India Assurance",
                insurance_expiry="2026-08-15", # Expired in past -> RED
                computed_status="RED",
                status_reason="Insurance expired on 2026-08-15"
            )
            db.add(doc_red)

            # Seed sample active and overstayed visitors
            v_vis1 = Visitor(
                visitor_pass_id="VP-20260905-001",
                full_name="Vikramaditya Rao",
                masked_aadhaar="XXXX-XXXX-8821",
                phone="+91-9811223344",
                purpose_of_visit="Squadron Technical Review",
                host_master_id=m.id,
                assigned_rfid_card="RFID-9001",
                permitted_zones='["ZONE_A", "ZONE_B"]',
                entry_time=datetime.utcnow() - timedelta(hours=3),
                expected_exit_time=datetime.utcnow() - timedelta(minutes=45), # OVERSTAYED!
                status="OVERSTAYED",
                overstay_alert_sent=True,
                consent_recorded=True
            )
            v_vis2 = Visitor(
                visitor_pass_id="VP-20260905-002",
                full_name="Praveen Nair (HAL Rep)",
                masked_aadhaar="XXXX-XXXX-4412",
                phone="+91-9988776655",
                purpose_of_visit="Avionics Consultation",
                host_master_id=m.id,
                assigned_rfid_card="RFID-9002",
                permitted_zones='["ZONE_A", "ZONE_B"]',
                entry_time=datetime.utcnow() - timedelta(minutes=30),
                expected_exit_time=datetime.utcnow() + timedelta(hours=3), # Valid active
                status="CHECKED_IN",
                overstay_alert_sent=False,
                consent_recorded=True
            )
            db.add_all([v_vis1, v_vis2])

            db.commit()
    finally:
        db.close()

@app.get("/health")
def health_check():
    return {
        "status": "ONLINE",
        "station": settings.STATION_CODE,
        "mode": "AIR_GAPPED_ON_PREM",
        "hardware_integration": "MULTI_BIOMETRIC_ACTIVE",
        "version": settings.VERSION
    }
