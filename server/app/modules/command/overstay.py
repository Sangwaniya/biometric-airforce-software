from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.db.models import Visitor, GateTransaction
from app.core.audit import AuditService

class OverstayAlertEngine:
    """Monitors visitors who have not checked out beyond permitted hours
       and generates automated alert dispatches for gate sentries & Provost Marshal.
    """

    @staticmethod
    def evaluate_overstays(db: Session, actor_id: str = "SYSTEM_WATCHDOG") -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        active_visitors = db.query(Visitor).filter(
            Visitor.status == "CHECKED_IN"
        ).all()

        new_alerts = []
        for v in active_visitors:
            if v.expected_exit_time and v.expected_exit_time < now:
                v.status = "OVERSTAYED"
                v.overstay_alert_sent = True
                db.commit()

                overstay_duration = int((now - v.expected_exit_time).total_seconds() // 60)
                alert_info = {
                    "pass_id": v.visitor_pass_id,
                    "visitor_name": v.full_name,
                    "phone": v.phone,
                    "host_master_id": v.host.master_id,
                    "host_name": f"{v.host.rank} {v.host.full_name}",
                    "host_quarter": v.host.residential_quarter,
                    "rfid_card": v.assigned_rfid_card,
                    "overstay_minutes": overstay_duration,
                    "timestamp": now.isoformat()
                }

                # Record alert in forensic audit log
                AuditService.record_event(
                    db=db,
                    actor_id=actor_id,
                    actor_role="WATCHDOG",
                    action="TRIGGER_OVERSTAY_ALERT",
                    resource_type="VISITOR_OVERSTAY",
                    resource_id=v.visitor_pass_id,
                    details=alert_info
                )

                new_alerts.append(alert_info)

        return new_alerts

    @staticmethod
    def checkout_visitor(db: Session, identifier: str, gate_id: str = "GATE-01-MAIN", actor_id: str = "SENTRY-01") -> Dict[str, Any]:
        """Checks out visitor by Visitor Pass ID or RFID Card Number."""
        visitor = db.query(Visitor).filter(
            (Visitor.visitor_pass_id == identifier) |
            (Visitor.assigned_rfid_card == identifier)
        ).first()

        if not visitor:
            raise ValueError(f"Visitor with Pass/RFID '{identifier}' not found")

        if visitor.status == "CHECKED_OUT":
            return {"status": "ALREADY_CHECKED_OUT", "pass_id": visitor.visitor_pass_id}

        now = datetime.utcnow()
        old_status = visitor.status
        visitor.status = "CHECKED_OUT"
        visitor.actual_exit_time = now
        db.commit()

        # Gate transaction
        tx = GateTransaction(
            timestamp=now,
            gate_id=gate_id,
            gate_type="EXIT",
            channel="VISITOR_PASS",
            identifier=visitor.visitor_pass_id,
            matched_entity_type="VISITOR",
            matched_entity_id=visitor.id,
            matched_entity_name=visitor.full_name,
            status_color="GREEN",
            status_message=f"VISITOR EXIT PROCESSED - Pass surrendered",
            barrier_actuated=True,
            sentry_override=False,
            sentry_id=actor_id
        )
        db.add(tx)
        db.commit()

        AuditService.record_event(
            db=db,
            actor_id=actor_id,
            actor_role="SENTRY",
            action="VISITOR_CHECKOUT",
            resource_type="VISITOR_PASS",
            resource_id=visitor.visitor_pass_id,
            details={
                "previous_status": old_status,
                "rfid_surrendered": visitor.assigned_rfid_card,
                "exit_time": now.isoformat()
            }
        )

        return {
            "status": "SUCCESS",
            "pass_id": visitor.visitor_pass_id,
            "visitor_name": visitor.full_name,
            "exit_time": now.isoformat(),
            "rfid_card": visitor.assigned_rfid_card
        }
