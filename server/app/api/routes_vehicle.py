from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.db.database import get_db
from app.db.models import Vehicle, VehicleDocument, MasterIdentity
from app.modules.vehicle.validator import VehicleValidationService
from app.modules.vehicle.anpr import ANPREngine
from app.modules.led_display.controller import GateLEDDisplayController

router = APIRouter(prefix="/api/vehicle", tags=["Vehicle Validation & ANPR"])

class VehicleRegisterRequest(BaseModel):
    plate_number: str
    master_id: Optional[str] = None
    vehicle_type: str = "FOUR_WHEELER"
    make_model: Optional[str] = None
    color: Optional[str] = None
    rfid_tag_id: Optional[str] = None
    # Documents
    rc_number: Optional[str] = None
    rc_expiry: Optional[str] = None
    dl_number: Optional[str] = None
    dl_holder_name: Optional[str] = None
    dl_expiry: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    insurance_company: Optional[str] = None
    insurance_expiry: str # Mandatory YYYY-MM-DD
    puc_expiry: Optional[str] = None
    station_pass_expiry: Optional[str] = None

class PlateValidationRequest(BaseModel):
    plate_number: str
    gate_id: str = "GATE-01-MAIN"
    gate_type: str = "ENTRY"
    broadcast_led: bool = True

@router.post("/register")
def register_vehicle(req: VehicleRegisterRequest, db: Session = Depends(get_db)):
    clean_plate = ANPREngine.normalize_plate(req.plate_number)
    existing = db.query(Vehicle).filter(Vehicle.plate_number == clean_plate).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Vehicle plate '{clean_plate}' already registered")

    master_fk = None
    if req.master_id:
        m = db.query(MasterIdentity).filter(MasterIdentity.master_id == req.master_id).first()
        if m:
            master_fk = m.id

    new_veh = Vehicle(
        plate_number=clean_plate,
        master_identity_id=master_fk,
        vehicle_type=req.vehicle_type,
        make_model=req.make_model,
        color=req.color,
        rfid_tag_id=req.rfid_tag_id,
        status="ACTIVE"
    )
    db.add(new_veh)
    db.flush()

    new_doc = VehicleDocument(
        vehicle_id=new_veh.id,
        rc_number=req.rc_number,
        rc_expiry=req.rc_expiry,
        dl_number=req.dl_number,
        dl_holder_name=req.dl_holder_name,
        dl_expiry=req.dl_expiry,
        insurance_policy_number=req.insurance_policy_number,
        insurance_company=req.insurance_company,
        insurance_expiry=req.insurance_expiry,
        puc_expiry=req.puc_expiry,
        station_pass_expiry=req.station_pass_expiry
    )
    # Precompute status
    eval_res = VehicleValidationService.evaluate_status(new_doc)
    new_doc.computed_status = eval_res["status_color"]
    new_doc.status_reason = eval_res["reason"]

    db.add(new_doc)
    db.commit()
    db.refresh(new_veh)

    return {
        "id": new_veh.id,
        "plate_number": new_veh.plate_number,
        "status_color": new_doc.computed_status,
        "status_reason": new_doc.status_reason
    }

@router.post("/validate")
def validate_plate(req: PlateValidationRequest, db: Session = Depends(get_db)):
    result = VehicleValidationService.validate_plate_and_broadcast(
        db=db,
        raw_plate=req.plate_number,
        gate_id=req.gate_id,
        gate_type=req.gate_type
    )

    if req.broadcast_led:
        led = GateLEDDisplayController()
        led.broadcast_alert(
            plate=result["plate_number"],
            owner=result["owner"],
            status_color=result["status_color"],
            message=result["status_message"]
        )

    return result

@router.post("/anpr_scan_frame")
async def anpr_scan_frame(file: UploadFile = File(...), db: Session = Depends(get_db)):
    contents = await file.read()
    detection = ANPREngine.process_frame(contents)
    if not detection["success"]:
        return detection

    # Cross-check detected plate immediately
    val = VehicleValidationService.validate_plate_and_broadcast(db=db, raw_plate=detection["plate"])
    return {
        "anpr_detection": detection,
        "gate_validation": val
    }

@router.get("/list")
def list_vehicles(db: Session = Depends(get_db)):
    vehicles = db.query(Vehicle).all()
    out = []
    for v in vehicles:
        owner_str = f"{v.master.rank} {v.master.full_name}" if v.master else "Unlinked"
        status_c = v.documents.computed_status if v.documents else "RED"
        reason = v.documents.status_reason if v.documents else "No docs"
        puc_str = f"Valid ({v.documents.puc_expiry})" if (v.documents and v.documents.puc_expiry) else "Certified"
        out.append({
            "id": v.id,
            "plate_number": v.plate_number,
            "owner": owner_str,
            "owner_name": owner_str,
            "type": v.vehicle_type,
            "vehicle_type": v.vehicle_type,
            "status_color": status_c,
            "status_reason": reason,
            "insurance_status_reason": reason,
            "puc_status_reason": puc_str
        })
    return out
