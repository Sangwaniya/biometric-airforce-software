from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.db.database import get_db
from app.modules.biomax.driver import BiomaxIndigoFaceDriver

router = APIRouter(prefix="/api/biomax", tags=["Biomax Hardware Integration"])

class PunchRequest(BaseModel):
    device_user_pin: str
    verify_mode: int = 15
    in_out_mode: int = 0
    gate_id: str = "GATE-01-MAIN"

class DeviceConnectRequest(BaseModel):
    ip: str = "192.168.1.201"
    port: int = 4370

@router.post("/punch")
def record_biomax_punch(req: PunchRequest, db: Session = Depends(get_db)):
    driver = BiomaxIndigoFaceDriver()
    result = driver.register_punch(
        db=db,
        device_user_pin=req.device_user_pin,
        verify_mode=req.verify_mode,
        in_out_mode=req.in_out_mode,
        gate_id=req.gate_id
    )
    return result

@router.post("/test_connect")
def test_device_connection(req: DeviceConnectRequest):
    driver = BiomaxIndigoFaceDriver(ip=req.ip, port=req.port)
    success = driver.connect()
    driver.disconnect()
    return {
        "device_ip": req.ip,
        "device_port": req.port,
        "online": success,
        "note": "Hardware responded via TCP 4370" if success else "Device offline or simulated environment"
    }
