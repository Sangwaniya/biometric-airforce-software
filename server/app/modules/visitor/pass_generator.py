import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.db.models import Visitor, MasterIdentity
from app.core.audit import AuditService

SECURITY_ZONES = {
    "ZONE_A": {
        "name": "Residential & Admin Area",
        "color_code": "GREEN",
        "description": "Family Quarters, CSD Canteen, Station Hospital, Admin HQ"
    },
    "ZONE_B": {
        "name": "Technical & Maintenance Area",
        "color_code": "ORANGE",
        "description": "Squadron Hangars, Mechanical Transport, Electronics Workshop"
    },
    "ZONE_C": {
        "name": "Operational & Restricted Area",
        "color_code": "RED",
        "description": "Flight Line, ATC Tower, Ammunition Depot, Restricted Ops"
    }
}

class VisitorPassService:
    @staticmethod
    def generate_pass_id() -> str:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        millis = str(int(datetime.utcnow().timestamp() * 1000))[-4:]
        return f"VP-{date_str}-{millis}"

    @staticmethod
    def onboard_visitor(
        db: Session,
        full_name: str,
        host_master_id: str,
        purpose_of_visit: str,
        masked_aadhaar: str,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        photo_path: Optional[str] = None,
        permitted_zones: Optional[List[str]] = None,
        duration_hours: int = 4,
        assigned_rfid_card: Optional[str] = None,
        actor_id: str = "RECEPTION-01"
    ) -> Visitor:
        # Validate Host Personnel
        host = db.query(MasterIdentity).filter(MasterIdentity.master_id == host_master_id).first()
        if not host:
            raise ValueError(f"Host Master ID '{host_master_id}' does not exist")
        if host.status != "ACTIVE":
            raise ValueError(f"Host Personnel '{host.rank} {host.full_name}' is currently {host.status}")

        zones = permitted_zones or ["ZONE_A"]
        now = datetime.utcnow()
        expected_exit = now + timedelta(hours=duration_hours)
        pass_id = VisitorPassService.generate_pass_id()

        visitor = Visitor(
            visitor_pass_id=pass_id,
            full_name=full_name,
            masked_aadhaar=masked_aadhaar,
            phone=phone,
            address=address,
            photo_path=photo_path,
            purpose_of_visit=purpose_of_visit,
            host_master_id=host.id,
            assigned_rfid_card=assigned_rfid_card or f"RFID-{pass_id[-4:]}",
            permitted_zones=json.dumps(zones),
            entry_time=now,
            expected_exit_time=expected_exit,
            status="CHECKED_IN",
            overstay_alert_sent=False,
            consent_recorded=True
        )

        db.add(visitor)
        db.commit()
        db.refresh(visitor)

        AuditService.record_event(
            db=db,
            actor_id=actor_id,
            actor_role="RECEPTION",
            action="ISSUE_VISITOR_PASS",
            resource_type="VISITOR_PASS",
            resource_id=pass_id,
            details={
                "visitor_name": full_name,
                "host_id": host_master_id,
                "zones": zones,
                "rfid": visitor.assigned_rfid_card,
                "valid_until": expected_exit.isoformat()
            }
        )

        return visitor

    @staticmethod
    def get_printable_badge_data(db: Session, pass_id: str) -> Dict[str, Any]:
        visitor = db.query(Visitor).filter(Visitor.visitor_pass_id == pass_id).first()
        if not visitor:
            raise ValueError(f"Visitor pass '{pass_id}' not found")

        host = visitor.host
        zones = json.loads(visitor.permitted_zones or '["ZONE_A"]')
        zone_details = [SECURITY_ZONES.get(z, {"name": z, "color_code": "GREEN"}) for z in zones]

        return {
            "badge_title": "INDIAN AIR FORCE STATION",
            "badge_type": "OFFICIAL VISITOR PASS",
            "pass_id": visitor.visitor_pass_id,
            "visitor_name": visitor.full_name.upper(),
            "masked_aadhaar": visitor.masked_aadhaar,
            "photo_url": f"/api/visitor/photo/{visitor.id}" if visitor.photo_path else None,
            "host_info": {
                "name": f"{host.rank} {host.full_name}",
                "unit": host.unit,
                "quarter": host.residential_quarter,
                "master_id": host.master_id
            },
            "valid_from": visitor.entry_time.strftime("%d-%b-%Y %H:%M HRS"),
            "valid_until": visitor.expected_exit_time.strftime("%d-%b-%Y %H:%M HRS"),
            "rfid_card": visitor.assigned_rfid_card,
            "permitted_zones": zone_details,
            "primary_zone_color": zone_details[0]["color_code"] if zone_details else "GREEN",
            "security_instruction": "Pass must be worn prominently at all times. Surrender pass and RFID badge at sentry gate prior to exit."
        }
