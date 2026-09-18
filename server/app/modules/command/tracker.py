from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import Visitor, GateTransaction, MasterIdentity, Vehicle, ChildIdentity

class StationCommandTracker:
    """Workstation Command & Visibility Dashboard Engine:
       - Present vs. Absent daily employee attendance
       - Live on-premise presence (who entered the premise and didn't exit)
       - Automated Overstay detection
       - Emergency Muster Roll
    """

    @staticmethod
    def get_live_station_status(db: Session, unit_filter: Optional[str] = None) -> Dict[str, Any]:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # 1. Total Registered Employees (Master Identities)
        masters_query = db.query(MasterIdentity).filter(MasterIdentity.status == "ACTIVE")
        if unit_filter:
            masters_query = masters_query.filter(MasterIdentity.unit == unit_filter)
        all_masters = masters_query.all()
        total_employees = len(all_masters)

        # 2. Today's eSSL punches to determine Present vs Absent
        today_punches = db.query(GateTransaction).filter(
            GateTransaction.timestamp >= today_start
        ).all()

        # Build presence mapping per master ID
        # An employee is PRESENT if their last gate transaction today was an ENTRY
        employee_last_tx = {}
        for tx in sorted(today_punches, key=lambda x: x.timestamp):
            if tx.matched_entity_type == "MASTER" and tx.matched_entity_id:
                employee_last_tx[tx.matched_entity_id] = tx

        present_masters = []
        absent_masters = []
        for m in all_masters:
            last_tx = employee_last_tx.get(m.id)
            if last_tx:
                # If they punched in today
                is_currently_inside = (last_tx.gate_type == "ENTRY")
                present_masters.append({
                    "id": m.id,
                    "master_id": m.master_id,
                    "service_number": m.service_number,
                    "rank": m.rank,
                    "full_name": m.full_name,
                    "unit": m.unit,
                    "quarter": m.residential_quarter,
                    "first_punch": last_tx.timestamp.strftime("%H:%M:%S"),
                    "last_gate": last_tx.gate_id,
                    "is_on_premise": is_currently_inside,
                    "attendance_status": "PRESENT"
                })
            else:
                absent_masters.append({
                    "id": m.id,
                    "master_id": m.master_id,
                    "service_number": m.service_number,
                    "rank": m.rank,
                    "full_name": m.full_name,
                    "unit": m.unit,
                    "attendance_status": "ABSENT"
                })

        # 3. Who Entered Premise But Didn't Exit (Active on-premise tracker)
        on_premise_people = []

        # A) On-premise Employees
        for p in present_masters:
            if p["is_on_premise"]:
                on_premise_people.append({
                    "category": "EMPLOYEE",
                    "identifier": p["master_id"],
                    "name": f"{p['rank']} {p['full_name']}",
                    "details": p["unit"],
                    "entry_time": p["first_punch"],
                    "quarter": p["quarter"],
                    "status": "ON_PREMISE"
                })

        # B) Active Visitors (Checked in and not checked out)
        active_visitors = db.query(Visitor).filter(
            Visitor.status.in_(["CHECKED_IN", "OVERSTAYED"])
        ).all()

        now = datetime.utcnow()
        overstayed_visitors = []
        for v in active_visitors:
            is_overstay = (v.status == "OVERSTAYED") or (v.expected_exit_time and v.expected_exit_time < now)
            overstay_mins = max(0, int((now - v.expected_exit_time).total_seconds() // 60)) if is_overstay else 0
            
            vis_entry = {
                "category": "VISITOR",
                "identifier": v.visitor_pass_id,
                "name": v.full_name,
                "details": f"Host: {v.host.rank} {v.host.full_name} ({v.host.unit})",
                "entry_time": v.entry_time.strftime("%H:%M:%S"),
                "expected_exit": v.expected_exit_time.strftime("%H:%M:%S"),
                "quarter": v.host.residential_quarter,
                "rfid_card": v.assigned_rfid_card,
                "phone": v.phone,
                "is_overstay": is_overstay,
                "overstay_minutes": overstay_mins,
                "status": "OVERSTAYED" if is_overstay else "ON_PREMISE"
            }
            on_premise_people.append(vis_entry)
            if is_overstay:
                overstayed_visitors.append(vis_entry)

        # 4. Active Vehicles On-Premise
        # Group vehicle transactions to check entered vs exited today
        vehicle_txs = [tx for tx in today_punches if tx.channel in ["ANPR_CAMERA", "ANPR_VEHICLE"]]
        vehicle_last_seen = {}
        for tx in sorted(vehicle_txs, key=lambda x: x.timestamp):
            vehicle_last_seen[tx.identifier] = tx

        active_vehicles = []
        for plate, tx in vehicle_last_seen.items():
            if tx.gate_type == "ENTRY":
                active_vehicles.append({
                    "plate_number": plate,
                    "owner": tx.matched_entity_name,
                    "entry_time": tx.timestamp.strftime("%H:%M:%S"),
                    "gate_id": tx.gate_id,
                    "status_color": tx.status_color
                })

        # 5. Summary Metrics
        return {
            "station_code": "AFS-SEC-01",
            "timestamp": now.isoformat(),
            "metrics": {
                "total_employees": total_employees,
                "employees_present": len(present_masters),
                "employees_absent": len(absent_masters),
                "total_on_premise_headcount": len(on_premise_people),
                "active_visitors": len(active_visitors),
                "overstayed_visitors_count": len(overstayed_visitors),
                "active_vehicles_count": len(active_vehicles)
            },
            "present_employees": present_masters,
            "absent_employees": absent_masters,
            "on_premise_people": on_premise_people,
            "overstayed_visitors": overstayed_visitors,
            "active_vehicles": active_vehicles
        }

    @staticmethod
    def generate_emergency_muster_roll(db: Session) -> Dict[str, Any]:
        """Generates real-time Emergency Evacuation Muster Roll of all living persons verified on base."""
        status = StationCommandTracker.get_live_station_status(db)
        return {
            "station": "AIR FORCE STATION COMMAND POST",
            "report_type": "EMERGENCY MUSTER ROLL & EVACUATION MANIFEST",
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "total_headcount": status["metrics"]["total_on_premise_headcount"],
            "personnel_count": len(status["present_employees"]),
            "visitor_count": status["metrics"]["active_visitors"],
            "manifest": status["on_premise_people"]
        }
