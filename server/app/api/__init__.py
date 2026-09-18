from app.api.routes_identity import router as identity_router
from app.api.routes_biometric import router as biometric_router
from app.api.routes_essl import router as essl_router
from app.api.routes_migration import router as migration_router
from app.api.routes_vehicle import router as vehicle_router
from app.api.routes_led import router as led_router
from app.api.routes_visitor import router as visitor_router
from app.api.routes_command import router as command_router
from app.api.routes_audit import router as audit_router
from app.api.routes_auth import router as auth_router

__all__ = [
    "identity_router",
    "biometric_router",
    "essl_router",
    "migration_router",
    "vehicle_router",
    "led_router",
    "visitor_router",
    "command_router",
    "audit_router",
    "auth_router"
]
