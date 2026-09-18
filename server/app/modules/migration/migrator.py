import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import MasterIdentity, ChildIdentity, BiometricCredential, LegacyMigrationRecord
from app.modules.identity.hierarchy import HierarchyService
from app.core.audit import AuditService
from app.core.config import PHOTO_DIR

class LegacyMigrationEngine:
    """End-to-end data migration engine for transferring legacy eTimeTrackLite,
       eSSL, and Biomax records into the new Master ID hierarchy.
    """

    @staticmethod
    def preflight_check(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validates legacy records before importing. Checks for duplicates and missing keys."""
        valid_records = []
        conflicts = []
        seen_codes = set()

        for idx, row in enumerate(records):
            code = str(row.get("EmployeeCode") or row.get("code") or "").strip()
            name = str(row.get("EmployeeName") or row.get("name") or "").strip()
            
            if not code or not name:
                conflicts.append({
                    "index": idx,
                    "record": row,
                    "reason": "Missing required EmployeeCode or EmployeeName"
                })
                continue
                
            if code in seen_codes:
                conflicts.append({
                    "index": idx,
                    "code": code,
                    "reason": f"Duplicate EmployeeCode '{code}' within batch"
                })
                continue
                
            seen_codes.add(code)
            valid_records.append({
                "code": code,
                "name": name,
                "card_no": str(row.get("CardNo") or row.get("card_number") or "").strip(),
                "rank": str(row.get("Designation") or row.get("rank") or "Staff").strip(),
                "unit": str(row.get("Department") or row.get("unit") or "Station HQ").strip(),
                "service_number": str(row.get("ServiceNo") or f"SN-{code}").strip(),
                "gender": str(row.get("Gender") or "M").strip(),
                "is_dependent": bool(row.get("IsDependent", False) or "." in code or "-" in code),
                "parent_code": str(row.get("ParentCode") or (code.split(".")[0] if "." in code else "")).strip(),
                "photo_filename": str(row.get("PhotoFilename") or f"{code}.jpg").strip()
            })

        return {
            "total_input": len(records),
            "valid_count": len(valid_records),
            "conflicts_count": len(conflicts),
            "conflicts": conflicts,
            "preview": valid_records[:10]
        }

    @staticmethod
    def execute_migration(
        db: Session,
        records: List[Dict[str, Any]],
        batch_id: Optional[str] = None,
        source_system: str = "eTimeTrackLite",
        legacy_photo_dir: Optional[str] = None,
        actor_id: str = "ADMIN"
    ) -> Dict[str, Any]:
        """Imports validated legacy records, creates Master IDs & Child IDs,
           migrates biometric photos and records audit history."""
        batch_id = batch_id or f"MIG-{int(datetime.utcnow().timestamp())}"
        migrated_masters = 0
        migrated_children = 0
        errors = []

        # First pass: Create primary Master Identities
        code_to_master_map = {}
        for row in records:
            code = str(row.get("code") or row.get("EmployeeCode")).strip()
            name = str(row.get("name") or row.get("EmployeeName")).strip()
            is_dependent = row.get("is_dependent", False) or ("." in code and not code.endswith(".0"))

            if not is_dependent:
                try:
                    # Check if already exists
                    existing = db.query(MasterIdentity).filter(MasterIdentity.master_id == code).first()
                    if not existing:
                        master = MasterIdentity(
                            master_id=code,
                            service_number=str(row.get("service_number") or f"SN-{code}"),
                            rank=str(row.get("rank") or "Air Force Personnel"),
                            full_name=name,
                            unit=str(row.get("unit") or "Station Unit"),
                            category="DEFENCE_OFFICER" if "Officer" in str(row.get("rank")) else "AIRMAN",
                            status="ACTIVE"
                        )
                        db.add(master)
                        db.flush()
                        code_to_master_map[code] = master
                        migrated_masters += 1
                    else:
                        code_to_master_map[code] = existing

                    # Migrate photo if present
                    photo_file = row.get("photo_filename") or f"{code}.jpg"
                    photo_migrated = False
                    if legacy_photo_dir and os.path.exists(os.path.join(legacy_photo_dir, photo_file)):
                        dest_path = os.path.join(PHOTO_DIR, f"master_{code}.jpg")
                        shutil.copy2(os.path.join(legacy_photo_dir, photo_file), dest_path)
                        photo_migrated = True

                    # Record migration entry
                    rec = LegacyMigrationRecord(
                        batch_id=batch_id,
                        source_system=source_system,
                        legacy_employee_code=code,
                        migrated_master_id=code,
                        face_photo_migrated=photo_migrated,
                        status="SUCCESS",
                        notes="Migrated as Primary Master ID"
                    )
                    db.add(rec)
                except Exception as e:
                    errors.append({"code": code, "error": str(e)})

        db.commit()

        # Second pass: Create Child Identities for dependents/staff
        for row in records:
            code = str(row.get("code") or row.get("EmployeeCode")).strip()
            name = str(row.get("name") or row.get("EmployeeName")).strip()
            is_dependent = row.get("is_dependent", False) or ("." in code and not code.endswith(".0"))

            if is_dependent:
                parent_code = str(row.get("parent_code") or code.split(".")[0]).strip()
                parent_master = db.query(MasterIdentity).filter(MasterIdentity.master_id == parent_code).first()
                if not parent_master:
                    # If parent wasn't found, create placeholder master or mark warning
                    errors.append({"code": code, "error": f"Parent Master ID '{parent_code}' not found for dependent '{code}'"})
                    continue

                try:
                    rel_type = "DOMESTIC_HELP" if ".D" in code else ("GUEST" if ".G" in code else ("SPOUSE" if code.endswith(".1") else "CHILD"))
                    
                    existing_child = db.query(ChildIdentity).filter(ChildIdentity.child_id == code).first()
                    if not existing_child:
                        child = ChildIdentity(
                            master_identity_id=parent_master.id,
                            child_id=code,
                            relationship_type=rel_type,
                            full_name=name,
                            rfid_card_number=str(row.get("card_no") or ""),
                            status="ACTIVE"
                        )
                        db.add(child)
                        db.flush()
                        migrated_children += 1

                    rec = LegacyMigrationRecord(
                        batch_id=batch_id,
                        source_system=source_system,
                        legacy_employee_code=code,
                        migrated_master_id=parent_code,
                        child_id=code,
                        face_photo_migrated=False,
                        status="SUCCESS",
                        notes=f"Migrated as Child ID ({rel_type})"
                    )
                    db.add(rec)
                except Exception as e:
                    errors.append({"code": code, "error": str(e)})

        db.commit()

        AuditService.record_event(
            db=db,
            actor_id=actor_id,
            actor_role="ADMIN",
            action="EXECUTE_LEGACY_MIGRATION",
            resource_type="MIGRATION_BATCH",
            resource_id=batch_id,
            details={
                "source_system": source_system,
                "masters_migrated": migrated_masters,
                "children_migrated": migrated_children,
                "error_count": len(errors)
            }
        )

        return {
            "batch_id": batch_id,
            "status": "COMPLETED",
            "masters_migrated": migrated_masters,
            "children_migrated": migrated_children,
            "errors": errors
        }

    @staticmethod
    def rollback_batch(db: Session, batch_id: str, actor_id: str = "ADMIN") -> Dict[str, Any]:
        """Rolls back a migration batch by batch_id."""
        records = db.query(LegacyMigrationRecord).filter(LegacyMigrationRecord.batch_id == batch_id).all()
        if not records:
            return {"status": "NOT_FOUND", "batch_id": batch_id, "deleted": 0}

        deleted_count = 0
        for r in records:
            if r.child_id:
                ch = db.query(ChildIdentity).filter(ChildIdentity.child_id == r.child_id).first()
                if ch:
                    db.delete(ch)
                    deleted_count += 1
            elif r.migrated_master_id:
                m = db.query(MasterIdentity).filter(MasterIdentity.master_id == r.migrated_master_id).first()
                if m:
                    db.delete(m)
                    deleted_count += 1
            db.delete(r)

        db.commit()

        AuditService.record_event(
            db=db,
            actor_id=actor_id,
            actor_role="ADMIN",
            action="ROLLBACK_LEGACY_MIGRATION",
            resource_type="MIGRATION_BATCH",
            resource_id=batch_id,
            details={"deleted_records": deleted_count}
        )

        return {"status": "ROLLED_BACK", "batch_id": batch_id, "deleted_entities": deleted_count}
