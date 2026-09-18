from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import MasterIdentity, ChildIdentity, GateTransaction
from app.modules.essl.driver import eSSLMultiBiometricDriver

class eSSLDirectSQLSync:
    """Channel 3: Direct SQL Integration for eSSL eTimeTrackLite databases.
       Directly queries and synchronizes with eTimeTrackLite MS SQL Server,
       PostgreSQL, or MySQL database tables without requiring device reconfiguration.
    """

    @staticmethod
    def sync_employees_from_sql(
        db: Session,
        sql_employee_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synchronizes employee rows from eSSL SQL table 'Employees' into Master & Child hierarchy."""
        imported_masters = 0
        imported_children = 0
        errors = []

        for row in sql_employee_records:
            code = str(row.get("EmployeeCode", "")).strip()
            name = str(row.get("EmployeeName", "")).strip()
            card = str(row.get("CardNo", "")).strip()
            dept = str(row.get("Department", "General Staff")).strip()
            desig = str(row.get("Designation", "Personnel")).strip()

            if not code or not name:
                continue

            # Detect Master vs Child
            is_dependent = "." in code or "-" in code

            if not is_dependent:
                existing = db.query(MasterIdentity).filter(MasterIdentity.master_id == code).first()
                if not existing:
                    master = MasterIdentity(
                        master_id=code,
                        service_number=f"SN-{code}",
                        rank=desig,
                        full_name=name,
                        unit=dept,
                        category="DEFENCE_OFFICER" if "Officer" in desig else "AIRMAN",
                        status="ACTIVE"
                    )
                    db.add(master)
                    imported_masters += 1
            else:
                parent_code = code.split(".")[0].split("-")[0]
                parent = db.query(MasterIdentity).filter(MasterIdentity.master_id == parent_code).first()
                if parent:
                    rel_type = "DOMESTIC_HELP" if ".D" in code else ("SPOUSE" if code.endswith(".1") else "CHILD")
                    existing_child = db.query(ChildIdentity).filter(ChildIdentity.child_id == code).first()
                    if not existing_child:
                        child = ChildIdentity(
                            master_identity_id=parent.id,
                            child_id=code,
                            relationship_type=rel_type,
                            full_name=name,
                            rfid_card_number=card,
                            status="ACTIVE"
                        )
                        db.add(child)
                        imported_children += 1

        db.commit()
        return {
            "status": "SQL_SYNC_COMPLETED",
            "imported_masters": imported_masters,
            "imported_children": imported_children,
            "timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    def sync_punches_from_sql(
        db: Session,
        sql_log_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synchronizes punch rows from eSSL SQL table 'DeviceLogs' / 'AttendanceLogs'."""
        driver = eSSLMultiBiometricDriver()
        synced_count = 0

        for log in sql_log_records:
            user_id = str(log.get("UserId") or log.get("EnrollNumber", "")).strip()
            log_date = log.get("LogDate", "")
            direction = int(log.get("Direction", 0)) # 0 = in, 1 = out
            device_id = str(log.get("DeviceId", "ESSL-SQL-GATE"))

            if user_id:
                driver.register_punch(
                    db=db,
                    device_user_pin=user_id,
                    verify_mode=15, # Face / Biometric
                    in_out_mode=direction,
                    gate_id=device_id
                )
                synced_count += 1

        return {
            "status": "LOGS_SYNCED",
            "synced_punches": synced_count,
            "timestamp": datetime.utcnow().isoformat()
        }
