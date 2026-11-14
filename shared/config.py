"""Global configuration and environment settings for Lyfpartner."""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Service Auth & Environment
    ENVIRONMENT: str = "development"
    SERVICE_KEY: str = "lyfpartner-secret-service-key-2026"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite+aiosqlite:///./lyfpartner.db"
    
    # Audio & Storage
    STORE_AUDIO: bool = False
    SAMPLE_RATE: int = 16000
    TELEPHONY_SAMPLE_RATE: int = 8000
    ASR_CONFIDENCE_THRESHOLD: float = 0.65
    
    # Voice Channel Limits (in kobo: 1 NGN = 100 kobo)
    PER_TRANSFER_LIMIT_KOBO: int = 5_000_000  # 50,000 NGN
    DAILY_TRANSFER_LIMIT_KOBO: int = 10_000_000  # 100,000 NGN
    REQUIRE_SAVED_BENEFICIARY_FOR_VOICE: bool = True
    
    # Transfer Quote Expiry
    TRANSFER_QUOTE_EXPIRY_SECONDS: int = 120
    
    # Provider Settings
    ASR_PROVIDER: str = "mock"  # "mock", "natlas"
    TTS_PROVIDER: str = "mock"  # "mock", "spitch"
    LLM_PROVIDER: str = "mock"  # "mock", "gemini", "natlas", "anthropic"
    VOICE_VERIFY_PROVIDER: str = "mock"  # "mock", "speaker_embedding"
    BANK_PROVIDER: str = "mock"
    KYC_PROVIDER: str = "mock"
    SMS_PROVIDER: str = "mock"  # "mock", "africastalking"
    
    # External Vendor Credentials
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    HF_TOKEN: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    SPITCH_API_KEY: Optional[str] = None
    AT_API_KEY: Optional[str] = None
    AT_USERNAME: Optional[str] = "sandbox"
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    
    # Microservice URLs (default to local ports or gateway routing)
    GATEWAY_URL: str = "http://localhost:8000"
    ASR_URL: str = "http://localhost:8001"
    AGENT_URL: str = "http://localhost:8002"
    TTS_URL: str = "http://localhost:8003"
    AUTH_URL: str = "http://localhost:8004"
    BANK_URL: str = "http://localhost:8005"
    KYC_URL: str = "http://localhost:8006"
    SUPPORT_URL: str = "http://localhost:8007"
    ADMIN_URL: str = "http://localhost:8008"
    NOTIFY_URL: str = "http://localhost:8009"

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
