import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
PHOTO_DIR = DATA_DIR / "photos"
PASS_DIR = DATA_DIR / "passes"
LOGS_DIR = DATA_DIR / "logs"

for folder in [DATA_DIR, PHOTO_DIR, PASS_DIR, LOGS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    PROJECT_NAME: str = "Air Force Station Biometric & Gate Security Platform"
    VERSION: str = "1.0.0-PROD-AIRFORCE"
    STATION_CODE: str = "AFS-SEC-01"
    
    # 100% On-Premises & Air-gapped: no external telemetry or cloud dependencies
    AIR_GAPPED_MODE: bool = True
    
    # Database
    DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'station_security.db'}"
    
    # Cryptography & Security
    # AES-256 Key (32 bytes hex-encoded). In production, this can be injected via secure hardware HSM/env.
    AES_256_SECRET_KEY_HEX: str = os.getenv(
        "AFS_AES_KEY", "7a6f9c8e1b3d5a7f2e4c6b8d0a2f4e6b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f"
    )
    JWT_SECRET: str = os.getenv("AFS_JWT_SECRET", "super-secret-afs-onprem-jwt-key-2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hour duty shift
    
    # Biomax Indigo Face 8 Hardware Defaults
    BIOMAX_DEFAULT_PORT: int = 4370
    BIOMAX_COMM_KEY: int = 0
    BIOMAX_POLL_INTERVAL_SECONDS: int = 2
    
    # Overstay Engine Defaults (in minutes)
    DEFAULT_VISITOR_VALIDITY_HOURS: int = 4
    OVERSTAY_GRACE_PERIOD_MINUTES: int = 15
    
    # DPDP-23 Retention Policy
    VISITOR_LOG_RETENTION_DAYS: int = 180  # 6-month statutory retention
    PURGE_ANONYMIZED_AFTER_DAYS: int = 365

settings = Settings()
