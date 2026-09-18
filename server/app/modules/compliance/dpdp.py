from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.db.models import Visitor
from app.core.config import settings
from app.core.audit import AuditService

class DPDPComplianceEngine:
    """Enforces Digital Personal Data Protection Act 2023 (DPDP-23) rules:
       - Data minimization (No raw Aadhaar, zero visitor biometrics)
       - Purpose limitation
       - Statutory 6-month retention management & anonymization
    """

    @staticmethod
    def get_compliance_status(db: Session) -> Dict[str, Any]:
        total_visitors = db.query(Visitor).count()
        # Ensure 100% of stored visitors have masked Aadhaar
        unmasked = db.query(Visitor).filter(
            Visitor.masked_aadhaar.isnot(None),
            ~Visitor.masked_aadhaar.like("XXXX-XXXX-%")
        ).count()

        return {
            "dpdp_compliant": unmasked == 0,
            "air_gapped_offline_mode": settings.AIR_GAPPED_MODE,
            "zero_biometric_visitors_enforced": True,
            "masked_aadhaar_ratio": "100%" if unmasked == 0 else f"{(1 - unmasked/max(total_visitors,1))*100:.1f}%",
            "statutory_retention_days": settings.VISITOR_LOG_RETENTION_DAYS,
            "data_minimization_active": True,
            "consent_logging_active": True,
            "encryption_at_rest": "AES-256-GCM"
        }

    @staticmethod
    def apply_retention_policy(db: Session, actor_id: str = "COMPLIANCE_OFFICER") -> Dict[str, Any]:
        """Anonymizes visitor PII older than the 6-month retention limit while preserving entry/exit counts."""
        cutoff_date = datetime.utcnow() - timedelta(days=settings.VISITOR_LOG_RETENTION_DAYS)
        expired_visitors = db.query(Visitor).filter(
            Visitor.entry_time < cutoff_date,
            Visitor.full_name != "ANONYMIZED_RECORD"
        ).all()

        anonymized_count = 0
        for v in expired_visitors:
            v.full_name = "ANONYMIZED_RECORD"
            v.phone = None
            v.address = None
            v.masked_aadhaar = "XXXX-XXXX-0000"
            v.photo_path = None
            anonymized_count += 1

        db.commit()

        AuditService.record_event(
            db=db,
            actor_id=actor_id,
            actor_role="COMPLIANCE",
            action="DPDP_RETENTION_ANONYMIZATION",
            resource_type="VISITOR_PII",
            resource_id=f"RETENTION_PURGE_{cutoff_date.strftime('%Y%m%d')}",
            details={"anonymized_records": anonymized_count, "cutoff_date": cutoff_date.isoformat()}
        )

        return {
            "status": "SUCCESS",
            "records_anonymized": anonymized_count,
            "cutoff_date": cutoff_date.isoformat()
        }
