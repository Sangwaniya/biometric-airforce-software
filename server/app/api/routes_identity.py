from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.db.database import get_db
from app.db.models import MasterIdentity, ChildIdentity
from app.modules.identity.hierarchy import HierarchyService

router = APIRouter(prefix="/api/identity", tags=["Core Identification & Master ID Hierarchy"])

class MasterCreateRequest(BaseModel):
    master_id: str
    service_number: str
    rank: str
    full_name: str
    unit: str
    residential_quarter: Optional[str] = None
    category: str = "DEFENCE_OFFICER"
    security_clearance_level: str = "LEVEL_1"
    phone: Optional[str] = None

class ChildCreateRequest(BaseModel):
    master_id: str
    relationship_type: str # SPOUSE, CHILD, DEPENDENT_PARENT, DOMESTIC_HELP, GUEST
    full_name: str
    dob: Optional[str] = None
    gender: Optional[str] = None
    rfid_card_number: Optional[str] = None
    police_verification_status: str = "EXEMPT"

class StatusUpdateRequest(BaseModel):
    new_status: str # ACTIVE, SUSPENDED, POSTED_OUT
    reason: str
    cascade: bool = True

@router.post("/master")
def create_master(req: MasterCreateRequest, db: Session = Depends(get_db)):
    return HierarchyService.create_master_identity(
        db=db,
        master_id=req.master_id,
        service_number=req.service_number,
        rank=req.rank,
        full_name=req.full_name,
        unit=req.unit,
        residential_quarter=req.residential_quarter,
        category=req.category,
        security_clearance_level=req.security_clearance_level,
        phone=req.phone
    )

@router.post("/child")
def create_child(req: ChildCreateRequest, db: Session = Depends(get_db)):
    return HierarchyService.create_child_identity(
        db=db,
        master_id=req.master_id,
        relationship_type=req.relationship_type,
        full_name=req.full_name,
        dob=req.dob,
        gender=req.gender,
        rfid_card_number=req.rfid_card_number,
        police_verification_status=req.police_verification_status
    )

@router.get("/tree/{master_id}")
def get_tree(master_id: str, db: Session = Depends(get_db)):
    return HierarchyService.get_hierarchy_tree(db=db, master_id=master_id)

@router.get("/masters")
def list_masters(query: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(MasterIdentity)
    if query:
        q = q.filter(
            (MasterIdentity.master_id.contains(query)) |
            (MasterIdentity.full_name.contains(query)) |
            (MasterIdentity.service_number.contains(query))
        )
    return q.all()

@router.patch("/master/{master_id}/status")
def update_status(master_id: str, req: StatusUpdateRequest, db: Session = Depends(get_db)):
    return HierarchyService.set_master_status(
        db=db,
        master_id=master_id,
        new_status=req.new_status,
        reason=req.reason,
        cascade=req.cascade
    )
