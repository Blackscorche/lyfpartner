"""KYC and Spoken Onboarding FastAPI Microservice."""
import secrets
import json
from fastapi import FastAPI, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_db, CustomerModel, AccountModel, AuditLogModel, init_db
from shared.logging_utils import RequestLoggingMiddleware, get_logger
from shared.security import hash_pin
from shared.errors import LyfpartnerException
from shared.schemas import (
    OnboardingStartRequest, BVNVerifyRequest, NINVerifyRequest,
    FaceCheckRequest, OnboardingCompleteRequest
)
from services.auth.main import normalize_spoken_digits
from services.kyc.provider import get_kyc_provider

logger = get_logger("kyc_service")
app = FastAPI(title="Lyfpartner KYC & Onboarding Service", version="1.0.0")
app.add_middleware(RequestLoggingMiddleware)

kyc_provider = get_kyc_provider()

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/health")
async def health():
    return {"status": "ok", "service": "kyc"}

@app.post("/v1/onboarding/start")
async def start_onboarding(req: OnboardingStartRequest):
    logger.info(f"Started spoken onboarding for {req.phone_number} in {req.preferred_language}")
    return {
        "status": "started",
        "phone_number": req.phone_number,
        "instructions": "Please speak your 11-digit BVN or National Identity Number clearly."
    }

@app.post("/v1/kyc/bvn/verify")
async def verify_bvn(req: BVNVerifyRequest):
    normalized = normalize_spoken_digits(req.bvn)
    # If standard 11 digits
    result = await kyc_provider.verify_bvn(normalized or req.bvn)
    if not result.get("valid"):
        raise LyfpartnerException("BVN_INVALID", result.get("reason", "Invalid BVN"), status_code=400)
    return result

@app.post("/v1/kyc/nin/verify")
async def verify_nin(req: NINVerifyRequest):
    normalized = normalize_spoken_digits(req.nin)
    result = await kyc_provider.verify_nin(normalized or req.nin)
    if not result.get("valid"):
        raise LyfpartnerException("NIN_INVALID", result.get("reason", "Invalid NIN"), status_code=400)
    return result

@app.post("/v1/kyc/face/check")
async def check_face(req: FaceCheckRequest):
    return await kyc_provider.check_face_match(req.image_base64)

@app.post("/v1/onboarding/complete")
async def complete_onboarding(req: OnboardingCompleteRequest, db: AsyncSession = Depends(get_db)):
    clean_pin = normalize_spoken_digits(req.pin)
    if len(clean_pin) != 4:
        raise LyfpartnerException("INVALID_PIN", "PIN must be exactly 4 digits", status_code=400)
    
    clean_bvn = normalize_spoken_digits(req.bvn) or req.bvn
    clean_nin = normalize_spoken_digits(req.nin) or req.nin

    customer_id = f"cust_{secrets.token_hex(4)}"
    account_number = f"0{secrets.randbelow(900000000) + 100000000}"
    account_id = f"acc_{customer_id[5:]}"

    customer = CustomerModel(
        customer_id=customer_id,
        phone_number=req.phone_number,
        full_name=req.full_name,
        bvn=clean_bvn,
        nin=clean_nin,
        preferred_language=req.preferred_language.value,
        pin_hash=hash_pin(clean_pin),
        voiceprint_json=json.dumps([0.18] * 128) if req.voice_sample_base64 else None,
        is_locked=False,
        failed_pin_attempts=0
    )
    db.add(customer)

    account = AccountModel(
        account_id=account_id,
        account_number=account_number,
        customer_id=customer_id,
        balance_kobo=0,
        currency="NGN",
        status="active"
    )
    db.add(account)

    audit = AuditLogModel(
        actor=customer_id,
        action="onboarding_completed",
        resource_id=account_id,
        result="success",
        details_json=json.dumps({"name": req.full_name, "account_number": account_number})
    )
    db.add(audit)
    await db.commit()

    logger.info(f"Successfully completed voice onboarding: account={account_number}")
    return {
        "status": "success",
        "customer_id": customer_id,
        "account_id": account_id,
        "account_number": account_number,
        "full_name": req.full_name,
        "message": f"Welcome {req.full_name}! Your account number is {account_number}."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.kyc.main:app", host="0.0.0.0", port=8006, reload=True)
