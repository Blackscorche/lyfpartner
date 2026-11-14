"""Pydantic v2 schemas for all Lyfpartner services."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class Language(str, Enum):
    HAUSA = "ha"
    IGBO = "ig"
    YORUBA = "yo"
    NIGERIAN_ENGLISH = "en-ng"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val = value.lower().strip()
            if val in ["en", "english", "en_ng", "en-us", "en-gb"]:
                return cls.NIGERIAN_ENGLISH
            if val in ["ha", "hausa"]:
                return cls.HAUSA
            if val in ["yo", "yoruba"]:
                return cls.YORUBA
            if val in ["ig", "igbo"]:
                return cls.IGBO
        return None

class AuthLevel(str, Enum):
    NONE = "none"
    BASIC = "basic"    # balance inquiry, transaction history
    FULL = "full"      # transfers, bill payments, airtime

class Channel(str, Enum):
    WEB = "web"
    TELEPHONY_AT = "telephony_at"
    TELEPHONY_TWILIO = "telephony_twilio"

# ----------------- Session Schemas -----------------
class SessionCreate(BaseModel):
    channel: Channel = Channel.WEB
    caller_id: Optional[str] = "+2348000000001"
    language: Optional[Language] = None
    account_id: Optional[str] = None

class SessionState(BaseModel):
    session_id: str
    channel: Channel
    caller_id: Optional[str] = None
    account_id: Optional[str] = None
    language: Optional[Language] = None
    auth_level: AuthLevel = AuthLevel.NONE
    turn_count: int = 0
    pending_action: Optional[Dict[str, Any]] = None
    last_reply_text: Optional[str] = None
    is_locked: bool = False
    pin_attempts: int = 0
    created_at: datetime
    updated_at: datetime

class SessionLanguageUpdate(BaseModel):
    language: Language

# ----------------- ASR Schemas -----------------
class WordInfo(BaseModel):
    word: str
    start: float
    end: float
    confidence: float

class ASRResponse(BaseModel):
    text: str
    confidence: float
    language: str
    is_low_confidence: bool
    words: List[WordInfo] = Field(default_factory=list)

class LanguageDetectResponse(BaseModel):
    language: Language
    confidence: float

# ----------------- Agent Schemas -----------------
class AgentRespondRequest(BaseModel):
    session_id: str
    text: str
    language: Language
    caller_id: Optional[str] = None
    account_id: Optional[str] = None
    auth_level: AuthLevel = AuthLevel.NONE
    pending_action: Optional[Dict[str, Any]] = None
    is_low_confidence: bool = False

class ToolCallRecord(BaseModel):
    tool: str
    arguments: Dict[str, Any]
    result: Any

class AgentRespondResponse(BaseModel):
    reply_text: str
    intent: str
    tool_calls: List[ToolCallRecord] = Field(default_factory=list)
    next_state: Optional[Dict[str, Any]] = None
    needs_confirmation: bool = False
    needs_auth: Optional[AuthLevel] = None
    escalate: bool = False
    escalate_reason: Optional[str] = None

# ----------------- TTS Schemas -----------------
class TTSRequest(BaseModel):
    text: str
    language: Language
    voice: Optional[str] = "default"
    sample_rate: int = 16000

# ----------------- Voice Turn Schemas -----------------
class VoiceTurnRequest(BaseModel):
    session_id: str
    text_input: Optional[str] = None # For testing or web-text hybrid turns
    audio_base64: Optional[str] = None # Base64 audio if sending via JSON

class VoiceTurnResponse(BaseModel):
    session_id: str
    reply_text: str
    reply_audio_base64: Optional[str] = None
    user_text: Optional[str] = None
    language: Optional[Language] = None
    auth_level: AuthLevel = AuthLevel.NONE
    turn_count: int
    intent: Optional[str] = None
    pending_action: Optional[Dict[str, Any]] = None
    state: Dict[str, Any] = Field(default_factory=dict)

# ----------------- Bank Schemas -----------------
class Account(BaseModel):
    account_id: str
    account_number: str
    customer_id: str
    name: str
    phone_number: str
    balance_kobo: int
    currency: str = "NGN"
    bvn: str
    nin: str
    status: str = "active"
    created_at: datetime

class Transaction(BaseModel):
    transaction_id: str
    account_id: str
    type: str # debit, credit
    amount_kobo: int
    narration: str
    reference: str
    balance_after_kobo: int
    created_at: datetime

class Beneficiary(BaseModel):
    beneficiary_id: str
    account_id: str
    name: str
    account_number: str
    bank_name: str
    nickname: Optional[str] = None

class TransferQuoteRequest(BaseModel):
    source_account_id: str
    beneficiary_account_number: str
    beneficiary_bank_name: str
    amount_kobo: int
    narration: Optional[str] = "Voice transfer"

class TransferQuoteResponse(BaseModel):
    confirmation_token: str
    source_account_id: str
    beneficiary_account_number: str
    beneficiary_name: str
    amount_kobo: int
    fee_kobo: int
    total_debit_kobo: int
    expires_at: datetime

class TransferConfirmRequest(BaseModel):
    confirmation_token: str
    idempotency_key: str

class TransferConfirmResponse(BaseModel):
    transaction_id: str
    reference: str
    status: str
    amount_kobo: int
    beneficiary_name: str
    source_account_id: str
    balance_after_kobo: int

class Biller(BaseModel):
    biller_id: str
    category: str # electricity, cable, water
    name: str

class BillPaymentRequest(BaseModel):
    account_id: str
    biller_id: str
    customer_meter_or_id: str
    amount_kobo: int
    idempotency_key: str

class AirtimePurchaseRequest(BaseModel):
    account_id: str
    phone_number: str
    network: str # MTN, AIRTEL, GLO, 9MOBILE
    amount_kobo: int
    idempotency_key: str

class DailyLimitsResponse(BaseModel):
    account_id: str
    per_transfer_limit_kobo: int
    daily_transfer_limit_kobo: int
    spent_today_kobo: int
    remaining_today_kobo: int

# ----------------- Auth Schemas -----------------
class PinSetRequest(BaseModel):
    customer_id: str
    pin: str

class PinVerifyRequest(BaseModel):
    customer_id: str
    pin: str

class VoiceEnrollRequest(BaseModel):
    customer_id: str
    samples_base64: List[str]

class VoiceVerifyRequest(BaseModel):
    customer_id: str
    audio_base64: str

class ElevateSessionRequest(BaseModel):
    session_id: str
    customer_id: str
    target_level: AuthLevel
    pin: Optional[str] = None
    voice_audio_base64: Optional[str] = None

class CaregiverOtpRequest(BaseModel):
    customer_id: str
    trusted_phone: Optional[str] = None

class CaregiverOtpVerifyRequest(BaseModel):
    customer_id: str
    otp: str

# ----------------- KYC Schemas -----------------
class OnboardingStartRequest(BaseModel):
    phone_number: str
    preferred_language: Language

class BVNVerifyRequest(BaseModel):
    bvn: str
    expected_phone: Optional[str] = None

class NINVerifyRequest(BaseModel):
    nin: str

class FaceCheckRequest(BaseModel):
    image_base64: str

class OnboardingCompleteRequest(BaseModel):
    phone_number: str
    full_name: str
    bvn: str
    nin: str
    pin: str
    preferred_language: Language
    voice_sample_base64: Optional[str] = None

# ----------------- Support & Admin Schemas -----------------
class TicketCreate(BaseModel):
    session_id: str
    customer_id: Optional[str] = None
    caller_id: Optional[str] = None
    subject: str
    description: str
    category: str = "general"

class Ticket(BaseModel):
    ticket_id: str
    session_id: str
    customer_id: Optional[str] = None
    subject: str
    description: str
    status: str
    created_at: datetime

class EscalationRequest(BaseModel):
    session_id: str
    reason: str
    summary: Optional[str] = None

class CallLog(BaseModel):
    session_id: str
    caller_id: Optional[str]
    account_id: Optional[str]
    language: Optional[str]
    channel: str
    turn_count: int
    duration_seconds: int
    outcome: str # completed, escalated, abandoned, locked
    created_at: datetime
    ended_at: Optional[datetime] = None

class TranscriptTurn(BaseModel):
    speaker: str # caller, assistant
    text: str
    timestamp: datetime
    audio_url: Optional[str] = None

class AdminMetrics(BaseModel):
    calls_today: int
    deflection_rate_percent: float
    avg_turns: float
    low_confidence_rate_percent: float
    escalations_count: int

class AuditLogEntry(BaseModel):
    log_id: str
    actor: str
    action: str
    session_id: Optional[str]
    resource_id: Optional[str]
    result: str # success, failure, denied
    details: Optional[Dict[str, Any]]
    timestamp: datetime

# ----------------- Notify Schemas -----------------
class SMSRequest(BaseModel):
    to_phone: str
    message: str
