from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.db.models import MasterIdentity, ChildIdentity, BiometricCredential
from app.core.audit import AuditService

class HierarchyService:
    @staticmethod
    def generate_next_child_id(db: Session, master_id: str, relationship_type: str) -> str:
        """Generates hierarchical child ID:
           - Spouse: 32.1
           - Children / Dependents: 32.2, 32.3, ...
           - Domestic staff: 32.D1, 32.D2, ...
           - Guests: 32.G1, 32.G2, ...
        """
        master = db.query(MasterIdentity).filter(MasterIdentity.master_id == master_id).first()
        if not master:
            raise HTTPException(status_code=404, detail=f"Master ID '{master_id}' not found")

        existing_children = db.query(ChildIdentity).filter(ChildIdentity.master_identity_id == master.id).all()
        existing_ids = [c.child_id for c in existing_children]

        if relationship_type == "DOMESTIC_HELP":
            prefix = f"{master_id}.D"
            count = 1
            while f"{prefix}{count}" in existing_ids:
                count += 1
            return f"{prefix}{count}"
            
        elif relationship_type == "GUEST":
            prefix = f"{master_id}.G"
            count = 1
            while f"{prefix}{count}" in existing_ids:
                count += 1
            return f"{prefix}{count}"
            
        elif relationship_type == "SPOUSE":
            spouse_id = f"{master_id}.1"
            if spouse_id not in existing_ids:
                return spouse_id
            # If re-marrying or already assigned, fallback to next dot-index
            idx = 2
            while f"{master_id}.{idx}" in existing_ids:
                idx += 1
            return f"{master_id}.{idx}"
            
        else:  # CHILD or DEPENDENT_PARENT
            idx = 2
            while f"{master_id}.{idx}" in existing_ids:
                idx += 1
            return f"{master_id}.{idx}"

    @staticmethod
    def create_master_identity(
        db: Session,
        master_id: str,
        service_number: str,
        rank: str,
        full_name: str,
        unit: str,
        residential_quarter: Optional[str] = None,
        category: str = "DEFENCE_OFFICER",
        security_clearance_level: str = "LEVEL_1",
        phone: Optional[str] = None,
        actor_id: str = "SYSTEM"
    ) -> MasterIdentity:
        existing = db.query(MasterIdentity).filter(
            (MasterIdentity.master_id == master_id) | (MasterIdentity.service_number == service_number)
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Master Identity with ID '{master_id}' or Service Number '{service_number}' already exists."
            )

        new_master = MasterIdentity(
            master_id=master_id,
            service_number=service_number,
            rank=rank,
            full_name=full_name,
            unit=unit,
            residential_quarter=residential_quarter,
            category=category,
            security_clearance_level=security_clearance_level,
            phone=phone,
            status="ACTIVE"
        )
        db.add(new_master)
        db.commit()
        db.refresh(new_master)

        AuditService.record_event(
            db=db,
            actor_id=actor_id,
            actor_role="ADMIN",
            action="CREATE_MASTER_IDENTITY",
            resource_type="MASTER_IDENTITY",
            resource_id=master_id,
            details={"service_number": service_number, "name": full_name, "rank": rank, "unit": unit}
        )

        return new_master

    @staticmethod
    def create_child_identity(
        db: Session,
        master_id: str,
        relationship_type: str,
        full_name: str,
        dob: Optional[str] = None,
        gender: Optional[str] = None,
        rfid_card_number: Optional[str] = None,
        police_verification_status: str = "EXEMPT",
        valid_until: Optional[datetime] = None,
        custom_child_id: Optional[str] = None,
        actor_id: str = "SYSTEM"
    ) -> ChildIdentity:
        master = db.query(MasterIdentity).filter(MasterIdentity.master_id == master_id).first()
        if not master:
            raise HTTPException(status_code=404, detail=f"Master ID '{master_id}' not found")

        child_id = custom_child_id or HierarchyService.generate_next_child_id(db, master_id, relationship_type)

        new_child = ChildIdentity(
            master_identity_id=master.id,
            child_id=child_id,
            relationship_type=relationship_type,
            full_name=full_name,
            dob=dob,
            gender=gender,
            rfid_card_number=rfid_card_number,
            police_verification_status=police_verification_status,
            valid_until=valid_until,
            status="ACTIVE" if master.status == "ACTIVE" else "SUSPENDED"
        )
        db.add(new_child)
        db.commit()
        db.refresh(new_child)

        AuditService.record_event(
            db=db,
            actor_id=actor_id,
            actor_role="ADMIN",
            action="CREATE_CHILD_IDENTITY",
            resource_type="CHILD_IDENTITY",
            resource_id=child_id,
            details={
                "master_id": master_id,
                "relationship_type": relationship_type,
                "name": full_name,
                "rfid": rfid_card_number
            }
        )

        return new_child

    @staticmethod
    def set_master_status(
        db: Session,
        master_id: str,
        new_status: str,
        reason: str,
        cascade: bool = True,
        actor_id: str = "SYSTEM"
    ) -> Dict[str, Any]:
        """Sets Master ID status (ACTIVE, SUSPENDED, POSTED_OUT).
           If cascade is True, child identities inherit suspension/deactivation."""
        master = db.query(MasterIdentity).filter(MasterIdentity.master_id == master_id).first()
        if not master:
            raise HTTPException(status_code=404, detail=f"Master ID '{master_id}' not found")

        old_status = master.status
        master.status = new_status
        db.commit()

        cascaded_children = []
        if cascade and new_status in ["SUSPENDED", "POSTED_OUT"]:
            children = db.query(ChildIdentity).filter(ChildIdentity.master_identity_id == master.id).all()
            for child in children:
                child.status = new_status
                cascaded_children.append(child.child_id)
            db.commit()

        AuditService.record_event(
            db=db,
            actor_id=actor_id,
            actor_role="ADMIN",
            action="UPDATE_MASTER_STATUS",
            resource_type="MASTER_IDENTITY",
            resource_id=master_id,
            details={
                "old_status": old_status,
                "new_status": new_status,
                "reason": reason,
                "cascade": cascade,
                "affected_children": cascaded_children
            }
        )

        return {
            "master_id": master_id,
            "old_status": old_status,
            "new_status": new_status,
            "cascaded_children": cascaded_children
        }

    @staticmethod
    def get_hierarchy_tree(db: Session, master_id: str) -> Dict[str, Any]:
        master = db.query(MasterIdentity).filter(MasterIdentity.master_id == master_id).first()
        if not master:
            raise HTTPException(status_code=404, detail=f"Master ID '{master_id}' not found")

        children = db.query(ChildIdentity).filter(ChildIdentity.master_identity_id == master.id).all()
        vehicles = master.vehicles

        return {
            "master": {
                "id": master.id,
                "master_id": master.master_id,
                "service_number": master.service_number,
                "rank": master.rank,
                "full_name": master.full_name,
                "unit": master.unit,
                "residential_quarter": master.residential_quarter,
                "category": master.category,
                "security_clearance_level": master.security_clearance_level,
                "phone": master.phone,
                "status": master.status
            },
            "children": [
                {
                    "id": c.id,
                    "child_id": c.child_id,
                    "relationship_type": c.relationship_type,
                    "full_name": c.full_name,
                    "dob": c.dob,
                    "gender": c.gender,
                    "rfid_card_number": c.rfid_card_number,
                    "police_verification_status": c.police_verification_status,
                    "valid_until": c.valid_until.isoformat() if c.valid_until else None,
                    "status": c.status
                }
                for c in children
            ],
            "vehicles": [
                {
                    "id": v.id,
                    "plate_number": v.plate_number,
                    "vehicle_type": v.vehicle_type,
                    "make_model": v.make_model,
                    "status": v.status,
                    "status_color": v.documents.computed_status if v.documents else "RED"
                }
                for v in vehicles
            ]
        }
