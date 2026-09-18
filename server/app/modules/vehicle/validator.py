import calendar
from datetime import datetime, date
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import Vehicle, VehicleDocument, MasterIdentity, GateTransaction

class VehicleValidationService:
    """Evaluates vehicle RC, DL, Insurance, Pollution (PUC), and station pass validity
       against the local database and determines Green / Yellow / Red gate alerts,
       including exact countdown in months and days until document expiration.
    """

    @staticmethod
    def get_current_month_range(ref_date: Optional[date] = None):
        ref = ref_date or date.today()
        _, last_day = calendar.monthrange(ref.year, ref.month)
        month_end = date(ref.year, ref.month, last_day)
        return ref, month_end

    @staticmethod
    def calculate_expiry_countdown(date_str: Optional[str], ref_date: Optional[date] = None) -> Dict[str, Any]:
        """Calculates exact days and fractional months until expiration date."""
        today = ref_date or date.today()
        if not date_str:
            return {
                "date": None,
                "days_remaining": None,
                "months_remaining": None,
                "status": "MISSING",
                "label": "Document Not Uploaded"
            }

        try:
            exp = datetime.strptime(date_str, "%Y-%m-%d").date()
            delta_days = (exp - today).days
            months_remaining = round(delta_days / 30.4375, 1)

            if delta_days < 0:
                return {
                    "date": date_str,
                    "days_remaining": delta_days,
                    "months_remaining": months_remaining,
                    "status": "EXPIRED",
                    "label": f"EXPIRED ({abs(delta_days)} days ago)"
                }
            elif delta_days <= 30:
                return {
                    "date": date_str,
                    "days_remaining": delta_days,
                    "months_remaining": months_remaining,
                    "status": "EXPIRING_SOON",
                    "label": f"Expires in {delta_days} Days"
                }
            else:
                return {
                    "date": date_str,
                    "days_remaining": delta_days,
                    "months_remaining": months_remaining,
                    "status": "VALID",
                    "label": f"{months_remaining} Months Left"
                }
        except ValueError:
            return {
                "date": date_str,
                "days_remaining": None,
                "months_remaining": None,
                "status": "INVALID_FORMAT",
                "label": "Invalid Date Format"
            }

    @staticmethod
    def evaluate_status(doc: VehicleDocument, current_date: Optional[date] = None) -> Dict[str, Any]:
        today, month_end = VehicleValidationService.get_current_month_range(current_date)
        
        ins_info = VehicleValidationService.calculate_expiry_countdown(doc.insurance_expiry, today)
        puc_info = VehicleValidationService.calculate_expiry_countdown(doc.puc_expiry, today)
        rc_info = VehicleValidationService.calculate_expiry_countdown(doc.rc_expiry, today)
        dl_info = VehicleValidationService.calculate_expiry_countdown(doc.dl_expiry, today)

        reasons_red = []
        reasons_yellow = []

        # 1. Insurance Check
        if ins_info["status"] in ["EXPIRED", "MISSING"]:
            reasons_red.append(f"Insurance {ins_info['label']}")
        elif ins_info["days_remaining"] is not None:
            exp_date = datetime.strptime(doc.insurance_expiry, "%Y-%m-%d").date()
            if exp_date <= month_end:
                reasons_yellow.append(f"Insurance expires {doc.insurance_expiry} ({ins_info['label']})")

        # 2. Pollution (PUC) Check
        if puc_info["status"] == "EXPIRED":
            reasons_red.append(f"PUC Pollution {puc_info['label']}")
        elif puc_info["days_remaining"] is not None:
            exp_date = datetime.strptime(doc.puc_expiry, "%Y-%m-%d").date()
            if exp_date <= month_end:
                reasons_yellow.append(f"PUC Pollution expires {doc.puc_expiry} ({puc_info['label']})")

        # 3. RC Check
        if rc_info["status"] == "EXPIRED":
            reasons_red.append(f"RC {rc_info['label']}")
        elif rc_info["days_remaining"] is not None:
            exp_date = datetime.strptime(doc.rc_expiry, "%Y-%m-%d").date()
            if exp_date <= month_end:
                reasons_yellow.append(f"RC expires {doc.rc_expiry} ({rc_info['label']})")

        # 4. DL Check
        if dl_info["status"] == "EXPIRED":
            reasons_red.append(f"DL {dl_info['label']}")

        # Status decision
        if reasons_red:
            status_color = "RED"
            reason = " | ".join(reasons_red)
        elif reasons_yellow:
            status_color = "YELLOW"
            reason = " | ".join(reasons_yellow)
        else:
            status_color = "GREEN"
            reason = f"All clear (Insurance: {ins_info['label']}, PUC: {puc_info['label']})"

        return {
            "status_color": status_color,
            "reason": reason,
            "evaluated_at": today.isoformat(),
            "countdown_analytics": {
                "insurance": ins_info,
                "pollution_puc": puc_info,
                "rc": rc_info,
                "dl": dl_info
            }
        }

    @staticmethod
    def validate_plate_and_broadcast(
        db: Session,
        raw_plate: str,
        gate_id: str = "GATE-01-MAIN",
        gate_type: str = "ENTRY"
    ) -> Dict[str, Any]:
        """Validates plate against local database, returns LED text, expiry countdown, and gate transaction."""
        normalized_plate = "".join(filter(str.isalnum, raw_plate.upper()))
        vehicle = db.query(Vehicle).filter(Vehicle.plate_number == normalized_plate).first()
        
        status_color = "RED"
        status_message = f"UNREGISTERED VEHICLE: {normalized_plate}"
        owner_name = "Unregistered"
        owner_rank = ""
        barrier_open = False
        analytics = None

        if vehicle:
            if vehicle.status == "BLACKLISTED":
                status_color = "RED"
                status_message = "SECURITY ALERT: VEHICLE BLACKLISTED"
            else:
                owner = vehicle.master
                if owner:
                    owner_name = owner.full_name
                    owner_rank = owner.rank

                if not vehicle.documents:
                    status_color = "RED"
                    status_message = "NO DOCUMENTS ON FILE"
                else:
                    eval_result = VehicleValidationService.evaluate_status(vehicle.documents)
                    status_color = eval_result["status_color"]
                    analytics = eval_result["countdown_analytics"]
                    
                    if status_color == "GREEN":
                        status_message = f"ALL CLEAR: {normalized_plate} ({owner_rank} {owner_name})"
                        barrier_open = True
                    elif status_color == "YELLOW":
                        status_message = f"WARNING: {eval_result['reason']}"
                        barrier_open = True
                    else:
                        status_message = f"HALT: {eval_result['reason']}"
                        barrier_open = False
                        
                    # Update document cache
                    vehicle.documents.computed_status = status_color
                    vehicle.documents.status_reason = status_message
                    db.commit()

        # Record gate transaction
        tx = GateTransaction(
            timestamp=datetime.utcnow(),
            gate_id=gate_id,
            gate_type=gate_type,
            channel="ANPR_CAMERA",
            identifier=normalized_plate,
            matched_entity_type="VEHICLE" if vehicle else "UNKNOWN",
            matched_entity_id=vehicle.id if vehicle else None,
            matched_entity_name=f"{owner_rank} {owner_name}".strip(),
            status_color=status_color,
            status_message=status_message,
            barrier_actuated=barrier_open,
            sentry_override=False,
            sentry_id="ANPR-AUTO-01"
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)

        # LED Display formatted lines
        led_lines = [
            f"VEH: {normalized_plate}",
            f"{owner_rank} {owner_name}"[:24],
            f"[{status_color}] {status_message}"[:30]
        ]

        return {
            "transaction_id": tx.id,
            "plate_number": normalized_plate,
            "status_color": status_color,
            "status_message": status_message,
            "owner": f"{owner_rank} {owner_name}".strip(),
            "barrier_actuated": barrier_open,
            "analytics": analytics,
            "led_display": {
                "line_1": led_lines[0],
                "line_2": led_lines[1],
                "line_3": led_lines[2],
                "color": status_color
            }
        }
