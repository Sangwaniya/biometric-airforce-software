from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
)
from sqlalchemy.orm import relationship
from app.db.database import Base

class MasterIdentity(Base):
    __tablename__ = "master_identities"

    id = Column(Integer, primary_key=True, index=True)
    master_id = Column(String(64), unique=True, index=True, nullable=False) # e.g. "32" or "AF-1042"
    service_number = Column(String(64), unique=True, index=True, nullable=False)
    rank = Column(String(64), nullable=False)
    full_name = Column(String(128), nullable=False)
    unit = Column(String(128), nullable=False)
    residential_quarter = Column(String(128), nullable=True)
    category = Column(String(64), default="DEFENCE_OFFICER") # DEFENCE_OFFICER, AIRMAN, CIVILIAN_OFFICER, CONTRACTOR
    security_clearance_level = Column(String(32), default="LEVEL_1")
    phone = Column(String(32), nullable=True)
    status = Column(String(32), default="ACTIVE", index=True) # ACTIVE, SUSPENDED, POSTED_OUT
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    children = relationship("ChildIdentity", back_populates="master", cascade="all, delete-orphan")
    vehicles = relationship("Vehicle", back_populates="master")
    hosted_visitors = relationship("Visitor", back_populates="host")

class ChildIdentity(Base):
    __tablename__ = "child_identities"

    id = Column(Integer, primary_key=True, index=True)
    master_identity_id = Column(Integer, ForeignKey("master_identities.id", ondelete="CASCADE"), nullable=False)
    child_id = Column(String(64), unique=True, index=True, nullable=False) # e.g. "32.1", "32.2", "32.D1"
    relationship_type = Column(String(32), nullable=False) # SPOUSE, CHILD, DEPENDENT_PARENT, DOMESTIC_HELP, GUEST
    full_name = Column(String(128), nullable=False)
    dob = Column(String(32), nullable=True)
    gender = Column(String(16), nullable=True)
    rfid_card_number = Column(String(64), index=True, nullable=True)
    police_verification_status = Column(String(32), default="EXEMPT") # VERIFIED, PENDING, EXEMPT
    valid_until = Column(DateTime, nullable=True) # Expiration date for domestic staff / guests
    status = Column(String(32), default="ACTIVE", index=True) # ACTIVE, SUSPENDED, EXPIRED
    created_at = Column(DateTime, default=datetime.utcnow)

    master = relationship("MasterIdentity", back_populates="children")

class BiometricCredential(Base):
    __tablename__ = "biometric_credentials"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(32), nullable=False) # MASTER, CHILD
    entity_id = Column(Integer, nullable=False, index=True)
    device_pin = Column(String(32), index=True, nullable=False) # Numeric PIN used in Biomax (e.g. 32, 3201)
    card_number = Column(String(64), nullable=True)
    face_photo_path = Column(String(256), nullable=True)
    face_template_version = Column(String(32), default="BioMax_AI_v9")
    is_enrolled = Column(Boolean, default=False)
    sync_status = Column(String(32), default="SYNCED") # SYNCED, PENDING_UPLOAD, ERROR
    last_synced_at = Column(DateTime, default=datetime.utcnow)

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String(32), unique=True, index=True, nullable=False) # e.g. "DL01AB1234"
    master_identity_id = Column(Integer, ForeignKey("master_identities.id"), nullable=True)
    child_identity_id = Column(Integer, ForeignKey("child_identities.id"), nullable=True)
    vehicle_type = Column(String(32), default="FOUR_WHEELER") # TWO_WHEELER, FOUR_WHEELER, DEFENCE_SERVICE, SUPPLY_TRUCK
    make_model = Column(String(64), nullable=True)
    color = Column(String(32), nullable=True)
    rfid_tag_id = Column(String(64), nullable=True)
    status = Column(String(32), default="ACTIVE", index=True) # ACTIVE, BLACKLISTED, TEMPORARY
    created_at = Column(DateTime, default=datetime.utcnow)

    master = relationship("MasterIdentity", back_populates="vehicles")
    documents = relationship("VehicleDocument", back_populates="vehicle", uselist=False, cascade="all, delete-orphan")

class VehicleDocument(Base):
    __tablename__ = "vehicle_documents"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), unique=True, nullable=False)
    rc_number = Column(String(64), nullable=True)
    rc_expiry = Column(String(32), nullable=True) # YYYY-MM-DD
    dl_number = Column(String(64), nullable=True)
    dl_holder_name = Column(String(128), nullable=True)
    dl_expiry = Column(String(32), nullable=True) # YYYY-MM-DD
    insurance_policy_number = Column(String(64), nullable=True)
    insurance_company = Column(String(128), nullable=True)
    insurance_expiry = Column(String(32), nullable=False) # YYYY-MM-DD
    puc_expiry = Column(String(32), nullable=True) # YYYY-MM-DD
    station_pass_expiry = Column(String(32), nullable=True) # YYYY-MM-DD
    
    # Pre-computed status cache
    computed_status = Column(String(16), default="GREEN") # GREEN, YELLOW, RED
    status_reason = Column(String(256), default="All documents valid")
    last_evaluated_at = Column(DateTime, default=datetime.utcnow)

    vehicle = relationship("Vehicle", back_populates="documents")

class Visitor(Base):
    __tablename__ = "visitors"

    id = Column(Integer, primary_key=True, index=True)
    visitor_pass_id = Column(String(64), unique=True, index=True, nullable=False) # e.g. "VP-20260905-001"
    full_name = Column(String(128), nullable=False)
    dob = Column(String(32), nullable=True)
    gender = Column(String(16), nullable=True)
    masked_aadhaar = Column(String(32), nullable=True) # DPDP-23 Zero-Biometric: "XXXX-XXXX-1234"
    phone = Column(String(32), nullable=True)
    address = Column(Text, nullable=True)
    photo_path = Column(String(256), nullable=True)
    purpose_of_visit = Column(String(256), nullable=False)
    host_master_id = Column(Integer, ForeignKey("master_identities.id"), nullable=False)
    assigned_rfid_card = Column(String(64), index=True, nullable=True)
    permitted_zones = Column(Text, default='["ZONE_A_RESIDENTIAL"]') # JSON string array
    entry_time = Column(DateTime, default=datetime.utcnow, index=True)
    expected_exit_time = Column(DateTime, nullable=False, index=True)
    actual_exit_time = Column(DateTime, nullable=True)
    status = Column(String(32), default="CHECKED_IN", index=True) # CHECKED_IN, CHECKED_OUT, OVERSTAYED, DENIED
    overstay_alert_sent = Column(Boolean, default=False)
    consent_recorded = Column(Boolean, default=True) # DPDP-23 consent flag

    host = relationship("MasterIdentity", back_populates="hosted_visitors")

class GateTransaction(Base):
    __tablename__ = "gate_transactions"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    gate_id = Column(String(32), default="GATE-01", index=True)
    gate_type = Column(String(16), default="ENTRY") # ENTRY, EXIT
    channel = Column(String(32), default="BIOMETRIC_FACE") # BIOMETRIC_FACE, ANPR_VEHICLE, VISITOR_PASS, RFID_CARD
    identifier = Column(String(64), index=True) # Scanned Plate or User PIN or RFID Card
    matched_entity_type = Column(String(32)) # MASTER, CHILD, VISITOR, UNKNOWN
    matched_entity_id = Column(Integer, nullable=True)
    matched_entity_name = Column(String(128), nullable=True)
    status_color = Column(String(16), default="GREEN") # GREEN, YELLOW, RED
    status_message = Column(String(256))
    barrier_actuated = Column(Boolean, default=False)
    sentry_override = Column(Boolean, default=False)
    sentry_override_reason = Column(String(256), nullable=True)
    sentry_id = Column(String(64), default="SENTRY-01")

class ForensicAuditLog(Base):
    __tablename__ = "forensic_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    sequence_number = Column(Integer, unique=True, index=True, nullable=False)
    timestamp = Column(String(64), index=True, nullable=False)
    actor_id = Column(String(64), index=True, nullable=False)
    actor_role = Column(String(32), nullable=False)
    action = Column(String(64), index=True, nullable=False)
    resource_type = Column(String(64), index=True, nullable=False)
    resource_id = Column(String(64), index=True, nullable=False)
    payload_hash = Column(String(64), nullable=False)
    encrypted_payload = Column(Text, nullable=False) # AES-256 encrypted payload
    previous_chain_hash = Column(String(64), nullable=False)
    current_chain_hash = Column(String(64), index=True, nullable=False)

class LegacyMigrationRecord(Base):
    __tablename__ = "legacy_migration_records"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(64), index=True, nullable=False)
    source_system = Column(String(64), default="eTimeTrackLite")
    legacy_employee_code = Column(String(64), index=True)
    migrated_master_id = Column(String(64), index=True)
    child_id = Column(String(64), nullable=True)
    face_photo_migrated = Column(Boolean, default=False)
    status = Column(String(32), default="SUCCESS") # SUCCESS, WARNING, FAILED
    notes = Column(Text, nullable=True)
    migrated_at = Column(DateTime, default=datetime.utcnow)
