"""Authentication and Voice Biometrics FastAPI Microservice."""
import re
import secrets
from typing import Optional
from fastapi import FastAPI, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_db, CustomerModel, SessionModel, AuditLogModel, init_db
from shared.logging_utils import RequestLoggingMiddleware, get_logger
from shared.security import hash_pin, verify_pin_hash
from shared.errors import AccountLockedException, AuthenticationFailedException, LyfpartnerException
from shared.schemas import (
    PinSetRequest, PinVerifyRequest, VoiceEnrollRequest, VoiceVerifyRequest,
    ElevateSessionRequest, CaregiverOtpRequest, CaregiverOtpVerifyRequest, AuthLevel
)
from services.auth.provider import get_voice_provider
import base64

logger = get_logger("auth_service")
app = FastAPI(title="Lyfpartner Auth Service", version="1.0.0")
app.add_middleware(RequestLoggingMiddleware)

voice_provider = get_voice_provider()

# Spoken digit mapping across Hausa, Igbo, Yoruba and English
DIGIT_MAP = {
    # English
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    # Hausa
    "sifiri": "0", "daya": "1", "biyu": "2", "uku": "3", "hudu": "4",
    "biyar": "5", "shida": "6", "bakwai": "7", "takwas": "8", "tara": "9",
    # Igbo
    "otu": "1", "abuo": "2", "ato": "3", "ano": "4",
    "ise": "5", "isii": "6", "asaa": "7", "asato": "8", "itoolu": "9",
    # Yoruba
    "oókan": "1", "meji": "2", "meta": "3", "merin": "4",
    "marun": "5", "mefa": "6", "meje": "7", "mejo": "8", "mesan": "9",
    "kan": "1", "eji": "2", "eta": "3", "erin": "4", "arun": "5", "efa": "6", "eje": "7", "ejo": "8", "esan": "9"
}

def normalize_spoken_digits(text: str, max_digits: Optional[int] = None) -> str:
    """Normalize spoken digit words in Hausa/Igbo/Yoruba/English to numbers."""
    if not text:
        return ""
    clean_digits = "".join(re.findall(r'\d+', text))
    if clean_digits:
        return clean_digits[:max_digits] if max_digits else clean_digits
    
    words = re.findall(r'\w+', text.lower())
    result = []
    for w in words:
        if w in DIGIT_MAP:
            result.append(DIGIT_MAP[w])
        elif w.isdigit():
            result.append(w)
    res_str = "".join(result)
    return res_str[:max_digits] if max_digits else res_str

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/health")
async def health():
    return {"status": "ok", "service": "auth"}

@app.post("/v1/auth/pin/set")
async def set_pin(req: PinSetRequest, x_session_id: Optional[str] = Header(None, alias="X-Session-Id"), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(CustomerModel).where(CustomerModel.customer_id == req.customer_id))
    cust = res.scalar_one_or_none()
    if not cust:
        raise LyfpartnerException("CUSTOMER_NOT_FOUND", "Customer not found", status_code=404)
    
    digits = normalize_spoken_digits(req.pin, max_digits=4)
    if len(digits) != 4:
        raise LyfpartnerException("INVALID_PIN", "PIN must be exactly 4 digits", status_code=400)
    
    cust.pin_hash = hash_pin(digits)
    cust.failed_pin_attempts = 0
    cust.is_locked = False
    
    audit = AuditLogModel(
        actor=cust.customer_id,
        action="pin_set",
        session_id=x_session_id,
        resource_id=cust.customer_id,
        result="success"
    )
    db.add(audit)
    await db.commit()
    logger.info("PIN successfully set for customer")
    return {"status": "success", "message": "PIN set successfully"}

@app.post("/v1/auth/pin/verify")
async def verify_pin(req: PinVerifyRequest, x_session_id: Optional[str] = Header(None, alias="X-Session-Id"), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(CustomerModel).where(CustomerModel.customer_id == req.customer_id))
    cust = res.scalar_one_or_none()
    if not cust:
        raise LyfpartnerException("CUSTOMER_NOT_FOUND", "Customer not found", status_code=404)
    
    if cust.is_locked:
        raise AccountLockedException("Account locked due to 3 failed attempts. Please use caregiver OTP.")
    
    digits = normalize_spoken_digits(req.pin, max_digits=4)
    is_valid = bool(cust.pin_hash and verify_pin_hash(digits, cust.pin_hash))
    
    if is_valid:
        cust.failed_pin_attempts = 0
        audit = AuditLogModel(
            actor=cust.customer_id,
            action="pin_verify",
            session_id=x_session_id,
            resource_id=cust.customer_id,
            result="success"
        )
        db.add(audit)
        await db.commit()
        return {"verified": True, "attempts_remaining": 3}
    else:
        cust.failed_pin_attempts += 1
        remaining = max(0, 3 - cust.failed_pin_attempts)
        if cust.failed_pin_attempts >= 3:
            cust.is_locked = True
            audit = AuditLogModel(
                actor=cust.customer_id,
                action="account_lockout",
                session_id=x_session_id,
                resource_id=cust.customer_id,
                result="locked"
            )
            db.add(audit)
            await db.commit()
            raise AccountLockedException("Wrong PIN 3 times. Account is locked. Caregiver OTP required.")
        
        audit = AuditLogModel(
            actor=cust.customer_id,
            action="pin_verify_failed",
            session_id=x_session_id,
            resource_id=cust.customer_id,
            result="failure"
        )
        db.add(audit)
        await db.commit()
        return {"verified": False, "attempts_remaining": remaining}

@app.post("/v1/auth/voice/enroll")
async def enroll_voice(req: VoiceEnrollRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(CustomerModel).where(CustomerModel.customer_id == req.customer_id))
    cust = res.scalar_one_or_none()
    if not cust:
        raise LyfpartnerException("CUSTOMER_NOT_FOUND", "Customer not found", status_code=404)
    
    embeddings = []
    for sample in req.samples_base64:
        audio_bytes = base64.b64decode(sample)
        emb = await voice_provider.extract_embedding(audio_bytes)
        embeddings.append(emb)
    
    avg_emb = [sum(col) / len(col) for col in zip(*embeddings)]
    import json
    cust.voiceprint_json = json.dumps(avg_emb)
    await db.commit()
    return {"status": "enrolled", "sample_count": len(req.samples_base64)}

@app.post("/v1/auth/voice/verify")
async def verify_voice(req: VoiceVerifyRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(CustomerModel).where(CustomerModel.customer_id == req.customer_id))
    cust = res.scalar_one_or_none()
    if not cust or not cust.voiceprint_json:
        return {"verified": False, "confidence": 0.0, "reason": "No voiceprint enrolled"}
    
    import json
    enrolled = json.loads(cust.voiceprint_json)
    audio_bytes = base64.b64decode(req.audio_base64)
    match, score = await voice_provider.verify_similarity(enrolled, audio_bytes)
    return {"verified": match, "confidence": score}

@app.post("/v1/auth/elevate")
async def elevate_session(req: ElevateSessionRequest, db: AsyncSession = Depends(get_db)):
    s_res = await db.execute(select(SessionModel).where(SessionModel.session_id == req.session_id))
    session = s_res.scalar_one_or_none()
    if not session:
        raise LyfpartnerException("SESSION_NOT_FOUND", "Session not found", status_code=404)
    
    c_res = await db.execute(select(CustomerModel).where(CustomerModel.customer_id == req.customer_id))
    cust = c_res.scalar_one_or_none()
    if not cust:
        raise LyfpartnerException("CUSTOMER_NOT_FOUND", "Customer not found", status_code=404)
    
    if cust.is_locked:
        session.is_locked = True
        await db.commit()
        raise AccountLockedException()
    
    if req.pin:
        digits = normalize_spoken_digits(req.pin, max_digits=4)
        if not verify_pin_hash(digits, cust.pin_hash):
            cust.failed_pin_attempts += 1
            if cust.failed_pin_attempts >= 3:
                cust.is_locked = True
                session.is_locked = True
                await db.commit()
                raise AccountLockedException()
            await db.commit()
            raise AuthenticationFailedException(f"Incorrect PIN. Attempts remaining: {3 - cust.failed_pin_attempts}")
    
    session.auth_level = req.target_level.value
    session.account_id = f"acc_{cust.customer_id[5:]}"
    cust.failed_pin_attempts = 0
    await db.commit()
    
    return {"session_id": session.session_id, "auth_level": session.auth_level}

@app.post("/v1/auth/caregiver/otp")
async def send_caregiver_otp(req: CaregiverOtpRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(CustomerModel).where(CustomerModel.customer_id == req.customer_id))
    cust = res.scalar_one_or_none()
    if not cust:
        raise LyfpartnerException("CUSTOMER_NOT_FOUND", "Customer not found", status_code=404)
    
    otp = f"{secrets.randbelow(900000) + 100000}"
    cust.caregiver_otp = otp
    await db.commit()
    
    logger.info(f"Generated caregiver OTP for {cust.customer_id} (delivered to {cust.caregiver_phone})")
    return {
        "status": "sent",
        "message": f"Caregiver OTP sent to {cust.caregiver_phone or 'registered contact'}",
        "mock_otp": otp
    }

@app.post("/v1/auth/caregiver/otp/verify")
async def verify_caregiver_otp(req: CaregiverOtpVerifyRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(CustomerModel).where(CustomerModel.customer_id == req.customer_id))
    cust = res.scalar_one_or_none()
    if not cust:
        raise LyfpartnerException("CUSTOMER_NOT_FOUND", "Customer not found", status_code=404)
    
    if not cust.caregiver_otp or cust.caregiver_otp != req.otp.strip():
        raise AuthenticationFailedException("Invalid caregiver OTP")
    
    cust.is_locked = False
    cust.failed_pin_attempts = 0
    cust.caregiver_otp = None
    
    audit = AuditLogModel(
        actor=cust.customer_id,
        action="caregiver_unlock",
        resource_id=cust.customer_id,
        result="success"
    )
    db.add(audit)
    await db.commit()
    return {"status": "unlocked", "message": "Account successfully unlocked via caregiver OTP"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.auth.main:app", host="0.0.0.0", port=8004, reload=True)
