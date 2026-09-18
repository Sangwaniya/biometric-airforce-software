from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.db.database import get_db
from app.modules.essl.driver import eSSLMultiBiometricDriver
from app.modules.essl.sql_sync import eSSLDirectSQLSync

router = APIRouter(prefix="/api/essl", tags=["Biometric Terminal Hardware (Compatibility Router)"])

class eSSLPunchRequest(BaseModel):
    device_user_pin: str
    verify_mode: int = 15 # 15 = Face, 1 = Fingerprint, 4 = RFID Card
    in_out_mode: int = 0  # 0 = Check-in, 1 = Check-out
    gate_id: str = "GATE-01-MAIN"

class eSSLDeviceConnectRequest(BaseModel):
    ip: str = "192.168.1.201"
    port: int = 4370

class eSSLSQLSyncRequest(BaseModel):
    sync_type: str = "EMPLOYEES" # EMPLOYEES or PUNCHES
    records: List[Dict[str, Any]]

@router.post("/punch")
def record_essl_punch(req: eSSLPunchRequest, db: Session = Depends(get_db)):
    driver = eSSLMultiBiometricDriver()
    return driver.register_punch(
        db=db,
        device_user_pin=req.device_user_pin,
        verify_mode=req.verify_mode,
        in_out_mode=req.in_out_mode,
        gate_id=req.gate_id
    )

@router.post("/test_connect")
def test_device_connection(req: eSSLDeviceConnectRequest):
    driver = eSSLMultiBiometricDriver(ip=req.ip, port=req.port)
    success = driver.connect()
    driver.disconnect()
    return {
        "device_ip": req.ip,
        "device_port": req.port,
        "online": success,
        "protocol": "Multi-Biometric Standalone Protocol (Port 4370 TCP)",
        "note": "Biometric Terminal acknowledged connection" if success else "Operating in local simulation mode"
    }

@router.post("/sync_sql")
def sync_direct_sql_records(req: eSSLSQLSyncRequest, db: Session = Depends(get_db)):
    if req.sync_type == "EMPLOYEES":
        return eSSLDirectSQLSync.sync_employees_from_sql(db=db, sql_employee_records=req.records)
    else:
        return eSSLDirectSQLSync.sync_punches_from_sql(db=db, sql_log_records=req.records)
