from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.database import get_db
from app.db.models import ForensicAuditLog
from app.core.audit import AuditService
from app.modules.compliance.dpdp import DPDPComplianceEngine
from app.modules.compliance.vapt import SystemOpennessManifest

router = APIRouter(prefix="/api/audit", tags=["Forensic Audit Log & Compliance"])

@router.get("/logs")
def search_logs(
    actor_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    q = db.query(ForensicAuditLog)
    if actor_id:
        q = q.filter(ForensicAuditLog.actor_id == actor_id)
    if action:
        q = q.filter(ForensicAuditLog.action == action)
    if resource_type:
        q = q.filter(ForensicAuditLog.resource_type == resource_type)

    logs = q.order_by(ForensicAuditLog.sequence_number.desc()).limit(limit).all()
    return logs

@router.get("/verify_integrity")
def verify_audit_chain(db: Session = Depends(get_db)):
    """Verifies SHA-256 cryptographic chain of all forensic audit logs to detect any tampering."""
    return AuditService.verify_chain_integrity(db)

@router.get("/dpdp_status")
def get_dpdp_status(db: Session = Depends(get_db)):
    return DPDPComplianceEngine.get_compliance_status(db)

@router.post("/dpdp_retention_purge")
def apply_retention_purge(db: Session = Depends(get_db)):
    return DPDPComplianceEngine.apply_retention_policy(db)

@router.get("/openness_manifest")
def get_openness_manifest():
    return SystemOpennessManifest.get_openness_manifest()
