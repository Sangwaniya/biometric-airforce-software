import base64
import os
import json
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

# AES-256-GCM Cryptographic Engine
_KEY_BYTES = bytes.fromhex(settings.AES_256_SECRET_KEY_HEX)
_AESGCM = AESGCM(_KEY_BYTES)

def encrypt_aes256(plain_text: str) -> str:
    """Encrypts plaintext string using AES-256-GCM. Returns base64 encoded ciphertext with nonce."""
    if not plain_text:
        return ""
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    ciphertext = _AESGCM.encrypt(nonce, plain_text.encode('utf-8'), None)
    # Combine nonce + ciphertext
    payload = nonce + ciphertext
    return base64.b64encode(payload).decode('utf-8')

def decrypt_aes256(encrypted_base64: str) -> str:
    """Decrypts base64 encoded AES-256-GCM ciphertext."""
    if not encrypted_base64:
        return ""
    try:
        data = base64.b64decode(encrypted_base64.encode('utf-8'))
        nonce = data[:12]
        ciphertext = data[12:]
        decrypted = _AESGCM.decrypt(nonce, ciphertext, None)
        return decrypted.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Decryption failed: integrity check or invalid key ({str(e)})")

# Password Hashing using PBKDF2-HMAC-SHA256 (FIPS / CERT-In compliant)
def hash_password(password: str, salt: Optional[str] = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        bytes.fromhex(salt),
        iterations=100000
    ).hex()
    return f"{salt}:{hashed}"

def verify_password(plain_password: str, stored_hash: str) -> bool:
    try:
        salt, expected_hash = stored_hash.split(":")
        computed = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            bytes.fromhex(salt),
            iterations=100000
        ).hex()
        return hmac.compare_digest(computed, expected_hash)
    except Exception:
        return False

# Token Generation & Validation (Self-contained for 100% offline air-gapped security)
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": int(expire.timestamp())})
    header = {"alg": "HS256", "typ": "JWT"}
    
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(to_encode).encode()).decode().rstrip("=")
    
    signature = hmac.new(
        settings.JWT_SECRET.encode(),
        f"{header_b64}.{payload_b64}".encode(),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def decode_access_token(token: str) -> dict:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="Invalid token format")
        header_b64, payload_b64, sig_b64 = parts
        
        expected_sig = hmac.new(
            settings.JWT_SECRET.encode(),
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256
        ).digest()
        
        # pad base64
        rem = len(sig_b64) % 4
        padded_sig = sig_b64 + "=" * ((4 - rem) % 4)
        actual_sig = base64.urlsafe_b64decode(padded_sig.encode())
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            raise HTTPException(status_code=401, detail="Token signature verification failed")
            
        rem = len(payload_b64) % 4
        padded_payload = payload_b64 + "=" * ((4 - rem) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded_payload.encode()).decode())
        
        if "exp" in payload and datetime.now(timezone.utc).timestamp() > payload["exp"]:
            raise HTTPException(status_code=401, detail="Token has expired")
            
        return payload
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication token invalid: {str(e)}")

# RBAC Roles
class UserRole:
    SUPER_ADMIN = "SUPER_ADMIN"
    SECURITY_OFFICER = "SECURITY_OFFICER"
    SENTRY_OPERATOR = "SENTRY_OPERATOR"
    RECEPTION_OPERATOR = "RECEPTION_OPERATOR"
    AUDITOR = "AUDITOR"

security_bearer = HTTPBearer(auto_error=False)

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)) -> Dict[str, Any]:
    if not credentials:
        # Development / Default Local Sentry fallback for air-gapped gate machines if header omitted
        return {
            "sub": "sentry_gate_01",
            "name": "Gate 1 Sentry In-Charge",
            "role": UserRole.SUPER_ADMIN,
            "gate_id": "GATE-01"
        }
    return decode_access_token(credentials.credentials)

def require_role(*allowed_roles: str):
    def role_checker(current_user: Dict[str, Any] = Security(get_current_user)):
        user_role = current_user.get("role")
        if user_role not in allowed_roles and user_role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {allowed_roles}, your role: {user_role}"
            )
        return current_user
    return role_checker
