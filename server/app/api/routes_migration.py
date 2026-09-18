from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from app.db.database import get_db
from app.modules.migration.migrator import LegacyMigrationEngine
from app.db.models import LegacyMigrationRecord

router = APIRouter(prefix="/api/migration", tags=["Legacy Data Migration"])

class MigrationBatchRequest(BaseModel):
    source_system: str = "eTimeTrackLite"
    records: List[Dict[str, Any]]
    legacy_photo_dir: Optional[str] = None

@router.post("/preflight")
def run_preflight(records: List[Dict[str, Any]]):
    return LegacyMigrationEngine.preflight_check(records)

@router.post("/execute")
def execute_migration(req: MigrationBatchRequest, db: Session = Depends(get_db)):
    pre = LegacyMigrationEngine.preflight_check(req.records)
    if pre["conflicts_count"] > 0 and len(pre["conflicts"]) == len(req.records):
        raise HTTPException(status_code=400, detail="All records in batch have conflicts")
    
    return LegacyMigrationEngine.execute_migration(
        db=db,
        records=req.records,
        source_system=req.source_system,
        legacy_photo_dir=req.legacy_photo_dir
    )

@router.post("/rollback/{batch_id}")
def rollback(batch_id: str, db: Session = Depends(get_db)):
    return LegacyMigrationEngine.rollback_batch(db=db, batch_id=batch_id)

@router.get("/batches")
def list_batches(db: Session = Depends(get_db)):
    return db.query(LegacyMigrationRecord).order_by(LegacyMigrationRecord.migrated_at.desc()).limit(100).all()
