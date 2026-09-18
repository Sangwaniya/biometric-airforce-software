from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.modules.led_display.controller import GateLEDDisplayController

router = APIRouter(prefix="/api/led", tags=["Gate LED Display Output"])

class LEDManualBroadcastRequest(BaseModel):
    plate_number: str
    owner: str = "Air Force Personnel"
    status_color: str = "GREEN" # GREEN, YELLOW, RED
    message: str = "ALL CLEAR - PROCEED"
    display_ip: str = "192.168.1.180"
    display_port: int = 5005

@router.post("/broadcast")
def manual_led_broadcast(req: LEDManualBroadcastRequest):
    controller = GateLEDDisplayController(display_ip=req.display_ip, display_port=req.display_port)
    return controller.broadcast_alert(
        plate=req.plate_number,
        owner=req.owner,
        status_color=req.status_color,
        message=req.message
    )

@router.get("/last")
def get_last_broadcast():
    controller = GateLEDDisplayController()
    return controller.last_broadcast or {"message": "No broadcast recorded yet"}
