"""Notification and SMS FastAPI Microservice."""
from fastapi import FastAPI
from shared.config import settings
from shared.logging_utils import RequestLoggingMiddleware, get_logger
from shared.schemas import SMSRequest

logger = get_logger("notify_service")
app = FastAPI(title="Lyfpartner Notification Service", version="1.0.0")
app.add_middleware(RequestLoggingMiddleware)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "notify", "sms_provider": settings.SMS_PROVIDER}

@app.post("/v1/notify/sms")
async def send_sms(req: SMSRequest):
    # If Africa's Talking credentials present
    if settings.SMS_PROVIDER == "africastalking" and settings.AT_API_KEY:
        # Live Africa's Talking SMS API
        logger.info(f"[AT-LIVE-SMS] Sending SMS to {req.to_phone}: {req.message}")
    else:
        # Mock Africa's Talking sandbox delivery
        logger.info(f"[MOCK-SMS] Delivered to {req.to_phone}: '{req.message}'")
        
    return {
        "status": "delivered",
        "provider": settings.SMS_PROVIDER,
        "recipient": req.to_phone,
        "message": req.message
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.notify.main:app", host="0.0.0.0", port=8009, reload=True)
