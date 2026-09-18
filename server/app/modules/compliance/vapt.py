from typing import Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

class VAPTSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects CERT-In recommended hardening headers on all HTTP responses."""
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        # Security hardening headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data: blob:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
        )
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Server"] = "AFS-SecureGateway/1.0"
        return response

class SystemOpennessManifest:
    """Anti-Vendor Lock-in and Master Access Manifest for Station IT Administrators."""
    @staticmethod
    def get_openness_manifest() -> Dict[str, Any]:
        return {
            "license_model": "Perpetual On-Premises Purchase (One-Time)",
            "vendor_lock_in_prevention": {
                "open_apis": "Full REST / OpenAPI 3.0 specification available at /docs",
                "direct_database_access": "Standard PostgreSQL / SQLite schema, no obfuscation",
                "master_credentials_provided": True,
                "encryption_keys_ownership": "Air Force Station Unit retains master AES-256 keys",
                "amc_friendly": "System updates delivered as modular microservice patches without core re-licensing"
            },
            "cert_in_vapt_readiness": {
                "sql_injection_protection": "Parameterized queries via SQLAlchemy ORM",
                "xss_prevention": "Strict CSP and JSON sanitization",
                "broken_auth_prevention": "HMAC-SHA256 tokens and PBKDF2 password hashing",
                "cryptographic_storage": "AES-256-GCM for sensitive fields at rest",
                "tamper_evident_audit": "SHA-256 cryptographic hash chain on forensic logs",
                "air_gapped_verification": "Zero external HTTP/DNS dependencies"
            }
        }
