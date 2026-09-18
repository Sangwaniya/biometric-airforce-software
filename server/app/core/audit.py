import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.core.security import encrypt_aes256

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def compute_payload_hash(payload: Any) -> str:
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

def compute_chain_hash(
    previous_hash: str,
    sequence: int,
    timestamp: str,
    actor_id: str,
    actor_role: str,
    action: str,
    resource_type: str,
    resource_id: str,
    payload_hash: str
) -> str:
    message = f"{previous_hash}|{sequence}|{timestamp}|{actor_id}|{actor_role}|{action}|{resource_type}|{resource_id}|{payload_hash}"
    return hashlib.sha256(message.encode('utf-8')).hexdigest()

class AuditService:
    @staticmethod
    def record_event(
        db: Session,
        actor_id: str,
        actor_role: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = "127.0.0.1"
    ):
        # Deferred import to avoid circular dependency
        from app.db.models import ForensicAuditLog
        
        # Get last log entry to maintain chain
        last_log = db.query(ForensicAuditLog).order_by(ForensicAuditLog.sequence_number.desc()).first()
        prev_hash = last_log.current_chain_hash if last_log else GENESIS_HASH
        seq_num = (last_log.sequence_number + 1) if last_log else 1
        
        now_utc = datetime.now(timezone.utc).isoformat()
        payload = details or {}
        payload["ip"] = ip_address
        p_hash = compute_payload_hash(payload)
        
        curr_hash = compute_chain_hash(
            prev_hash,
            seq_num,
            now_utc,
            actor_id,
            actor_role,
            action,
            resource_type,
            resource_id,
            p_hash
        )
        
        # Encrypt sensitive audit details
        encrypted_details = encrypt_aes256(json.dumps(payload))
        
        audit_entry = ForensicAuditLog(
            sequence_number=seq_num,
            timestamp=now_utc,
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            payload_hash=p_hash,
            encrypted_payload=encrypted_details,
            previous_chain_hash=prev_hash,
            current_chain_hash=curr_hash
        )
        
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry

    @staticmethod
    def verify_chain_integrity(db: Session) -> Dict[str, Any]:
        """Performs full forensic audit chain cryptographic verification across all logs."""
        from app.db.models import ForensicAuditLog
        
        logs: List[ForensicAuditLog] = db.query(ForensicAuditLog).order_by(ForensicAuditLog.sequence_number.asc()).all()
        if not logs:
            return {"status": "CLEAN", "total_records": 0, "corrupted_records": []}
            
        expected_prev_hash = GENESIS_HASH
        corrupted = []
        
        for idx, entry in enumerate(logs):
            expected_seq = idx + 1
            if entry.sequence_number != expected_seq:
                corrupted.append({
                    "id": entry.id,
                    "sequence": entry.sequence_number,
                    "reason": f"Sequence break: expected {expected_seq}, got {entry.sequence_number}"
                })
                
            if entry.previous_chain_hash != expected_prev_hash:
                corrupted.append({
                    "id": entry.id,
                    "sequence": entry.sequence_number,
                    "reason": f"Previous hash mismatch at sequence {entry.sequence_number}"
                })
                
            recomputed_hash = compute_chain_hash(
                entry.previous_chain_hash,
                entry.sequence_number,
                entry.timestamp,
                entry.actor_id,
                entry.actor_role,
                entry.action,
                entry.resource_type,
                entry.resource_id,
                entry.payload_hash
            )
            
            if recomputed_hash != entry.current_chain_hash:
                corrupted.append({
                    "id": entry.id,
                    "sequence": entry.sequence_number,
                    "reason": f"Tamper detected! Stored hash {entry.current_chain_hash} does not match recomputed {recomputed_hash}"
                })
                
            expected_prev_hash = entry.current_chain_hash
            
        return {
            "status": "TAMPER_DETECTED" if corrupted else "VERIFIED_INTEGRITY",
            "total_records": len(logs),
            "corrupted_records": corrupted
        }
