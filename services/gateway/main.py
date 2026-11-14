"""Public Voice Gateway & Telephony Orchestration Service."""
import base64
from datetime import datetime
import json
import secrets
from typing import Optional
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.config import settings
from shared.database import get_db, SessionModel, CustomerModel, TranscriptModel, init_db
from shared.logging_utils import RequestLoggingMiddleware, get_logger
from shared.schemas import (
    SessionCreate, SessionState, SessionLanguageUpdate, VoiceTurnRequest,
    VoiceTurnResponse, Language, AuthLevel, Channel
)
from services.gateway.pipeline import TurnPipeline

logger = get_logger("gateway")
app = FastAPI(title="Lyfpartner Voice Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

pipeline = TurnPipeline()

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway", "version": "1.0.0"}

# ----------------- Session Endpoints -----------------
@app.post("/v1/sessions", response_model=SessionState)
async def create_session(req: SessionCreate, db: AsyncSession = Depends(get_db)):
    session_id = f"sess_{secrets.token_hex(8)}"
    account_id = req.account_id
    
    # Try looking up customer by caller_id
    if req.caller_id and not account_id:
        c_res = await db.execute(select(CustomerModel).where(CustomerModel.phone_number == req.caller_id))
        cust = c_res.scalar_one_or_none()
        if cust:
            account_id = f"acc_{cust.customer_id[5:]}"
            if not req.language:
                req.language = Language(cust.preferred_language)

    session = SessionModel(
        session_id=session_id,
        caller_id=req.caller_id,
        account_id=account_id or "acc_aminu_001",
        channel=req.channel.value,
        language=(req.language.value if req.language else None),
        auth_level=AuthLevel.NONE.value,
        turn_count=0
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    logger.info(f"Created voice session {session_id} on channel {req.channel}")
    
    return SessionState(
        session_id=session.session_id,
        channel=Channel(session.channel),
        caller_id=session.caller_id,
        account_id=session.account_id,
        language=Language(session.language) if session.language else None,
        auth_level=AuthLevel(session.auth_level),
        turn_count=session.turn_count,
        pending_action=None,
        last_reply_text=session.last_reply_text,
        is_locked=session.is_locked,
        pin_attempts=session.pin_attempts,
        created_at=session.created_at,
        updated_at=session.updated_at
    )

@app.get("/v1/sessions/{id}", response_model=SessionState)
async def get_session(id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(SessionModel).where(SessionModel.session_id == id))
    session = res.scalar_one_or_none()
    if not session:
        return Response(status_code=404)
    pending = json.loads(session.pending_action_json) if session.pending_action_json else None
    return SessionState(
        session_id=session.session_id,
        channel=Channel(session.channel),
        caller_id=session.caller_id,
        account_id=session.account_id,
        language=Language(session.language) if session.language else None,
        auth_level=AuthLevel(session.auth_level),
        turn_count=session.turn_count,
        pending_action=pending,
        last_reply_text=session.last_reply_text,
        is_locked=session.is_locked,
        pin_attempts=session.pin_attempts,
        created_at=session.created_at,
        updated_at=session.updated_at
    )

@app.post("/v1/sessions/{id}/language")
async def set_session_language(id: str, update: SessionLanguageUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(SessionModel).where(SessionModel.session_id == id))
    session = res.scalar_one_or_none()
    if not session:
        return Response(status_code=404)
    session.language = update.language.value
    await db.commit()
    logger.info(f"Session {id} language set to {update.language}")
    return {"session_id": id, "language": session.language}

@app.post("/v1/sessions/{id}/end")
async def end_session(id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(SessionModel).where(SessionModel.session_id == id))
    session = res.scalar_one_or_none()
    if session:
        session.ended_at = datetime.utcnow()
        if session.outcome == "in_progress":
            session.outcome = "completed"
        await db.commit()
    return {"session_id": id, "status": "ended"}

# ----------------- Conversational Turn -----------------
@app.post("/v1/voice/turn", response_model=VoiceTurnResponse)
@app.post("/v1/voice/turn_audio", response_model=VoiceTurnResponse)
async def voice_turn(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    content_type = request.headers.get("content-type", "")
    session_id = None
    audio_bytes = None
    text_input = None

    if "multipart/form-data" in content_type:
        form = await request.form()
        session_id = form.get("session_id")
        text_input = form.get("text_input")
        audio_file = form.get("audio")
        if audio_file and hasattr(audio_file, "read"):
            audio_bytes = await audio_file.read()
    else:
        body = await request.json()
        session_id = body.get("session_id")
        text_input = body.get("text_input")
        if body.get("audio_base64"):
            audio_bytes = base64.b64decode(body["audio_base64"])

    if not session_id:
        session_id = f"sess_{secrets.token_hex(8)}"

    result = await pipeline.execute_turn(db, session_id, audio_bytes=audio_bytes, text_input=text_input)

    # Audio privacy rule: delete raw audio from memory/disk
    if not settings.STORE_AUDIO and audio_bytes:
        del audio_bytes

    return result

# ----------------- WebSocket Live Call Demo -----------------
@app.websocket("/ws/web-call")
async def websocket_web_call(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    session_id = f"sess_{secrets.token_hex(8)}"
    logger.info(f"WebSocket client connected: session {session_id}")
    try:
        # Send initial welcome and language selection prompt
        await websocket.send_json({
            "type": "ready",
            "session_id": session_id,
            "message": "Connected to Lyfpartner hotline. Speak or type your request."
        })
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            msg_type = payload.get("type", "turn")
            
            if msg_type == "language":
                lang = payload.get("language", "ha")
                await set_session_language(session_id, SessionLanguageUpdate(language=Language(lang)), db)
                await websocket.send_json({"type": "language_updated", "language": lang})
                continue

            text_in = payload.get("text")
            audio_b64 = payload.get("audio_base64")
            audio_bytes = base64.b64decode(audio_b64) if audio_b64 else None

            turn_res = await pipeline.execute_turn(db, session_id, audio_bytes=audio_bytes, text_input=text_in)
            await websocket.send_json({
                "type": "turn_reply",
                "session_id": session_id,
                "reply_text": turn_res.reply_text,
                "reply_audio_base64": turn_res.reply_audio_base64,
                "intent": turn_res.intent,
                "auth_level": turn_res.auth_level.value,
                "pending_action": turn_res.pending_action
            })
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
        await end_session(session_id, db)

# ----------------- Telephony: Africa's Talking -----------------
@app.post("/telephony/at/voice")
async def africas_talking_voice(request: Request, db: AsyncSession = Depends(get_db)):
    """Africa's Talking voice webhook returning AT Voice XML."""
    form = await request.form()
    session_id = form.get("sessionId", f"sess_at_{secrets.token_hex(6)}")
    caller_number = form.get("callerNumber", "+2348000000001")
    dtmf_digits = form.get("dtmfDigits")
    recording_url = form.get("recordingUrl")

    # XML response for Africa's Talking
    xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Barka da zuwa Lyfpartner. Don Allah ku fadi bukatarku.</Say>
    <Record finishOnKey="#" maxLength="15" trimSilence="true" playBeep="true" callbackUrl="{settings.GATEWAY_URL}/telephony/at/voice" />
</Response>"""
    return Response(content=xml_response, media_type="application/xml")

@app.post("/telephony/at/events")
async def africas_talking_events(request: Request):
    """Africa's Talking call lifecycle events (answered, ended)."""
    form = await request.form()
    event_status = form.get("status", "completed")
    session_id = form.get("sessionId")
    logger.info(f"Africa's Talking call event: {session_id} - status: {event_status}")
    return {"status": "ok"}

# ----------------- Telephony: Twilio -----------------
@app.post("/telephony/twilio/voice")
async def twilio_voice(request: Request):
    """Twilio voice webhook returning TwiML XML."""
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="en-NG">Welcome to Lyfpartner voice banking. Please speak after the tone.</Say>
    <Gather input="speech" timeout="5" action="/v1/voice/turn" method="POST">
        <Say>Say your command.</Say>
    </Gather>
</Response>"""
    return Response(content=twiml, media_type="application/xml")

@app.websocket("/telephony/twilio/stream")
async def twilio_media_stream(websocket: WebSocket):
    """Twilio Media Stream for bi-directional audio."""
    await websocket.accept()
    logger.info("Twilio Media Stream connected")
    try:
        while True:
            msg = await websocket.receive_text()
            # Handle inbound media packets
    except WebSocketDisconnect:
        logger.info("Twilio Media Stream disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.gateway.main:app", host="0.0.0.0", port=8000, reload=True)
