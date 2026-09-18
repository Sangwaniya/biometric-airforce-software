from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import os
from app.db.database import get_db
from app.db.models import Visitor, MasterIdentity
from app.modules.visitor.aadhaar_qr import AadhaarQRParser
from app.modules.visitor.pass_generator import VisitorPassService, SECURITY_ZONES

router = APIRouter(prefix="/api/visitor", tags=["Visitor Management & Aadhaar Onboarding"])

class AadhaarScanRequest(BaseModel):
    raw_qr_data: str

class VisitorOnboardRequest(BaseModel):
    full_name: str
    host_master_id: str
    purpose_of_visit: str
    masked_aadhaar: str
    phone: Optional[str] = None
    address: Optional[str] = None
    photo_path: Optional[str] = None
    permitted_zones: Optional[List[str]] = None
    duration_hours: int = 4
    assigned_rfid_card: Optional[str] = None

@router.post("/parse_aadhaar_qr")
def parse_aadhaar_qr(req: AadhaarScanRequest):
    return AadhaarQRParser.parse_qr_data(req.raw_qr_data)

@router.post("/onboard")
def onboard_visitor(req: VisitorOnboardRequest, db: Session = Depends(get_db)):
    try:
        visitor = VisitorPassService.onboard_visitor(
            db=db,
            full_name=req.full_name,
            host_master_id=req.host_master_id,
            purpose_of_visit=req.purpose_of_visit,
            masked_aadhaar=req.masked_aadhaar,
            phone=req.phone,
            address=req.address,
            photo_path=req.photo_path,
            permitted_zones=req.permitted_zones,
            duration_hours=req.duration_hours,
            assigned_rfid_card=req.assigned_rfid_card
        )
        return VisitorPassService.get_printable_badge_data(db=db, pass_id=visitor.visitor_pass_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/badge/{pass_id}")
def get_pass_badge(pass_id: str, db: Session = Depends(get_db)):
    try:
        return VisitorPassService.get_printable_badge_data(db=db, pass_id=pass_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/zones")
def list_security_zones():
    return SECURITY_ZONES

@router.get("/active")
def list_active_visitors(db: Session = Depends(get_db)):
    visitors = db.query(Visitor).filter(Visitor.status.in_(["CHECKED_IN", "OVERSTAYED"])).all()
    out = []
    for v in visitors:
        out.append({
            "pass_id": v.visitor_pass_id,
            "name": v.full_name,
            "phone": v.phone,
            "host": f"{v.host.rank} {v.host.full_name}",
            "host_quarter": v.host.residential_quarter,
            "entry_time": v.entry_time.isoformat(),
            "expected_exit": v.expected_exit_time.isoformat(),
            "status": v.status,
            "rfid_card": v.assigned_rfid_card
        })
    return out
