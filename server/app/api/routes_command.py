from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.db.database import get_db
from app.modules.command.tracker import StationCommandTracker
from app.modules.command.overstay import OverstayAlertEngine

router = APIRouter(prefix="/api/command", tags=["Command Dashboard, Presence & Overstay Engine"])

class CheckoutRequest(BaseModel):
    identifier: str # Pass ID or RFID Card Number
    gate_id: str = "GATE-01-MAIN"
    sentry_id: str = "SENTRY-01"

@router.get("/status")
def get_station_status(unit: Optional[str] = None, db: Session = Depends(get_db)):
    return StationCommandTracker.get_live_station_status(db, unit_filter=unit)

@router.get("/muster_roll")
def get_emergency_muster_roll(db: Session = Depends(get_db)):
    return StationCommandTracker.generate_emergency_muster_roll(db)

@router.post("/evaluate_overstays")
def evaluate_overstays(db: Session = Depends(get_db)):
    alerts = OverstayAlertEngine.evaluate_overstays(db)
    return {
        "status": "EVALUATED",
        "new_alerts_count": len(alerts),
        "alerts": alerts
    }

@router.post("/checkout")
def checkout_visitor(req: CheckoutRequest, db: Session = Depends(get_db)):
    try:
        return OverstayAlertEngine.checkout_visitor(
            db=db,
            identifier=req.identifier,
            gate_id=req.gate_id,
            actor_id=req.sentry_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
