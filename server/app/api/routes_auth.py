from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.security import create_access_token, hash_password, verify_password, UserRole

router = APIRouter(prefix="/api/auth", tags=["Authentication & Access Control"])

# Pre-seeded Air Force Station system accounts
DEFAULT_USERS = {
    "admin": {
        "password_hash": hash_password("AirForce@2026"),
        "role": UserRole.SUPER_ADMIN,
        "name": "Station Security Commander"
    },
    "sentry1": {
        "password_hash": hash_password("Sentry@123"),
        "role": UserRole.SENTRY_OPERATOR,
        "name": "Gate 1 Main Guard Post"
    },
    "reception": {
        "password_hash": hash_password("Reception@123"),
        "role": UserRole.RECEPTION_OPERATOR,
        "name": "Visitor Registration Desk"
    }
}

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(req: LoginRequest):
    user = DEFAULT_USERS.get(req.username)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid service credentials")

    token = create_access_token({
        "sub": req.username,
        "role": user["role"],
        "name": user["name"]
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "name": user["name"]
    }
