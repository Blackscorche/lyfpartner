"""Security utilities: service auth, Argon2 PIN hashing and verification."""
from fastapi import Header, HTTPException
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from shared.config import settings

ph = PasswordHasher()

def hash_pin(pin: str) -> str:
    """Hash a numeric PIN using Argon2."""
    return ph.hash(pin)

def verify_pin_hash(plain_pin: str, hashed_pin: str) -> bool:
    """Verify plain PIN against Argon2 hash."""
    try:
        return ph.verify(hashed_pin, plain_pin)
    except VerifyMismatchError:
        return False
    except Exception:
        return False

async def verify_service_key(x_service_key: str = Header(None, alias="X-Service-Key")):
    """Check service-to-service key for internal APIs."""
    if not x_service_key or x_service_key != settings.SERVICE_KEY:
        if settings.ENVIRONMENT == "development" and not x_service_key:
            return True
        raise HTTPException(status_code=403, detail="Invalid or missing X-Service-Key")
    return True
