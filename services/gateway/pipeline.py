"""Voice Turn Orchestration Pipeline with both HTTP microservice routing and local in-process fallback."""
import base64
import json
import secrets
from typing import Optional
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.config import settings
from shared.database import SessionModel, TranscriptModel, CustomerModel, AccountModel, AuditLogModel
from shared.logging_utils import get_logger
from shared.schemas import (
    Language, AuthLevel, VoiceTurnRequest, VoiceTurnResponse,
    AgentRespondRequest, AgentRespondResponse
)

# In-process providers for fast fallback or unified mode
from services.asr.provider import get_asr_provider
from services.agent.provider import get_llm_provider
from services.agent.tools import ToolRegistry
from services.tts.provider import get_tts_provider
from services.auth.main import normalize_spoken_digits
from shared.security import verify_pin_hash

logger = get_logger("turn_pipeline")

class TurnPipeline:
    def __init__(self, http_client: Optional[httpx.AsyncClient] = None):
        self.http_client = http_client
        self.asr_provider = get_asr_provider()
        self.llm_provider = get_llm_provider()
        self.tts_provider = get_tts_provider()
        self.tools = ToolRegistry(http_client)

    async def _get_client(self) -> httpx.AsyncClient:
        if self.http_client:
            return self.http_client
        return httpx.AsyncClient(headers={"X-Service-Key": settings.SERVICE_KEY}, timeout=5.0)

    async def execute_turn(
        self,
        db: AsyncSession,
        session_id: str,
        audio_bytes: Optional[bytes] = None,
        text_input: Optional[str] = None
    ) -> VoiceTurnResponse:
        # 1. Fetch or create Session
        s_res = await db.execute(select(SessionModel).where(SessionModel.session_id == session_id))
        session = s_res.scalar_one_or_none()
        if not session:
            session = SessionModel(
                session_id=session_id,
                channel="web",
                language=Language.HAUSA.value,
                auth_level=AuthLevel.NONE.value,
                turn_count=0
            )
            db.add(session)
            await db.commit()

        # 2. ASR Speech-to-Text
        transcribed_text = text_input
        is_low_conf = False
        curr_lang = Language(session.language) if session.language else Language.HAUSA

        if audio_bytes and not text_input:
            asr_data = await self.asr_provider.transcribe(audio_bytes, curr_lang)
            transcribed_text = asr_data.text
            is_low_conf = asr_data.is_low_confidence

        if not transcribed_text:
            transcribed_text = "Hello"

        # Auto-detect language switch if caller switched tongues
        if transcribed_text and len(transcribed_text.split()) >= 2:
            lower = transcribed_text.lower()
            if any(w in lower for w in ["sannu", "ina son", "kudi", "ragowar", "tura"]):
                curr_lang = Language.HAUSA
                session.language = Language.HAUSA.value
            elif any(w in lower for w in ["bawo", "mo fe", "owo", "eku"]):
                curr_lang = Language.YORUBA
                session.language = Language.YORUBA.value
            elif any(w in lower for w in ["ndewo", "kedu", "ego", "biko"]):
                curr_lang = Language.IGBO
                session.language = Language.IGBO.value
            elif any(w in lower for w in ["balance", "transfer", "send money", "hello", "check", "naira", "account"]):
                curr_lang = Language.NIGERIAN_ENGLISH
                session.language = Language.NIGERIAN_ENGLISH.value

        # Record caller transcript turn
        c_transcript = TranscriptModel(
            session_id=session.session_id,
            speaker="caller",
            text=transcribed_text
        )
        db.add(c_transcript)

        # 3. Check for Spoken PIN Elevation
        digits = normalize_spoken_digits(transcribed_text)
        if len(digits) == 4 and session.auth_level == AuthLevel.NONE.value:
            cust = None
            if session.caller_id:
                c_res = await db.execute(select(CustomerModel).where(CustomerModel.phone_number == session.caller_id))
                cust = c_res.scalar_one_or_none()
            if not cust and session.account_id:
                a_res = await db.execute(select(AccountModel).where(AccountModel.account_id == session.account_id))
                acc = a_res.scalar_one_or_none()
                if acc:
                    c_res = await db.execute(select(CustomerModel).where(CustomerModel.customer_id == acc.customer_id))
                    cust = c_res.scalar_one_or_none()
            
            if cust and cust.pin_hash and verify_pin_hash(digits, cust.pin_hash):
                session.auth_level = AuthLevel.BASIC.value
                cust.failed_pin_attempts = 0
                logger.info(f"Session {session.session_id} elevated to BASIC auth")

        # 4. Agent Dialogue & Reasoning
        pending_dict = json.loads(session.pending_action_json) if session.pending_action_json else {}
        agent_req = AgentRespondRequest(
            session_id=session.session_id,
            text=transcribed_text,
            language=curr_lang,
            caller_id=session.caller_id,
            account_id=session.account_id or "acc_aminu_001",
            auth_level=AuthLevel(session.auth_level),
            pending_action=pending_dict,
            is_low_confidence=is_low_conf,
            last_reply_text=session.last_reply_text,
            turn_count=session.turn_count
        )
        agent_res = await self.llm_provider.respond(agent_req, self.tools)
        reply_text = agent_res.reply_text
        intent = agent_res.intent
        next_state = agent_res.next_state

        # Record assistant transcript turn
        a_transcript = TranscriptModel(
            session_id=session.session_id,
            speaker="assistant",
            text=reply_text
        )
        db.add(a_transcript)

        # 5. TTS Speech Generation
        tts = get_tts_provider()
        wav_bytes = await tts.speak(reply_text, curr_lang, 16000)
        reply_audio_base64 = base64.b64encode(wav_bytes).decode("utf-8")

        # 6. Update Session State
        session.turn_count += 1
        session.last_reply_text = reply_text
        session.pending_action_json = json.dumps(next_state) if next_state else None
        await db.commit()

        return VoiceTurnResponse(
            session_id=session.session_id,
            reply_text=reply_text,
            reply_audio_base64=reply_audio_base64,
            user_text=transcribed_text,
            language=curr_lang,
            auth_level=AuthLevel(session.auth_level),
            turn_count=session.turn_count,
            intent=intent,
            pending_action=next_state,
            state={
                "account_id": session.account_id,
                "caller_id": session.caller_id,
                "auth_level": session.auth_level
            }
        )
