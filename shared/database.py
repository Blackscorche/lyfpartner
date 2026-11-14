"""SQLAlchemy 2 database setup, async engine, and ORM models for Lyfpartner."""
from datetime import datetime
import json
import uuid
from typing import AsyncGenerator
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from shared.config import settings

Base = declarative_base()

class CustomerModel(Base):
    __tablename__ = "customers"
    
    customer_id = Column(String(64), primary_key=True)
    phone_number = Column(String(32), unique=True, index=True, nullable=False)
    full_name = Column(String(128), nullable=False)
    bvn = Column(String(32), nullable=False)
    nin = Column(String(32), nullable=False)
    preferred_language = Column(String(16), default="ha")
    pin_hash = Column(String(256), nullable=True)
    voiceprint_json = Column(Text, nullable=True) # list of float speaker embeddings
    is_locked = Column(Boolean, default=False)
    failed_pin_attempts = Column(Integer, default=0)
    caregiver_phone = Column(String(32), nullable=True)
    caregiver_otp = Column(String(16), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AccountModel(Base):
    __tablename__ = "accounts"
    
    account_id = Column(String(64), primary_key=True)
    account_number = Column(String(32), unique=True, index=True, nullable=False)
    customer_id = Column(String(64), ForeignKey("customers.customer_id"), nullable=False)
    balance_kobo = Column(BigInteger, default=0, nullable=False)
    currency = Column(String(8), default="NGN")
    status = Column(String(16), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

class TransactionModel(Base):
    __tablename__ = "transactions"
    
    transaction_id = Column(String(64), primary_key=True)
    account_id = Column(String(64), ForeignKey("accounts.account_id"), index=True, nullable=False)
    type = Column(String(16), nullable=False) # debit, credit
    amount_kobo = Column(BigInteger, nullable=False)
    narration = Column(String(256), nullable=False)
    reference = Column(String(64), unique=True, nullable=False)
    balance_after_kobo = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class BeneficiaryModel(Base):
    __tablename__ = "beneficiaries"
    
    beneficiary_id = Column(String(64), primary_key=True)
    account_id = Column(String(64), ForeignKey("accounts.account_id"), index=True, nullable=False)
    name = Column(String(128), nullable=False)
    account_number = Column(String(32), nullable=False)
    bank_name = Column(String(64), nullable=False)
    nickname = Column(String(64), nullable=True)

class TransferQuoteModel(Base):
    __tablename__ = "transfer_quotes"
    
    token = Column(String(64), primary_key=True)
    source_account_id = Column(String(64), nullable=False)
    beneficiary_account_number = Column(String(32), nullable=False)
    beneficiary_name = Column(String(128), nullable=False)
    amount_kobo = Column(BigInteger, nullable=False)
    fee_kobo = Column(BigInteger, default=0)
    total_debit_kobo = Column(BigInteger, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)

class IdempotencyModel(Base):
    __tablename__ = "idempotency_records"
    
    idempotency_key = Column(String(128), primary_key=True)
    action = Column(String(64), nullable=False)
    response_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class SessionModel(Base):
    __tablename__ = "sessions"
    
    session_id = Column(String(64), primary_key=True)
    caller_id = Column(String(32), nullable=True)
    account_id = Column(String(64), nullable=True)
    channel = Column(String(32), default="web")
    language = Column(String(16), nullable=True)
    auth_level = Column(String(16), default="none")
    turn_count = Column(Integer, default=0)
    pending_action_json = Column(Text, nullable=True)
    last_reply_text = Column(Text, nullable=True)
    is_locked = Column(Boolean, default=False)
    pin_attempts = Column(Integer, default=0)
    outcome = Column(String(32), default="in_progress") # in_progress, completed, escalated, locked
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

class TranscriptModel(Base):
    __tablename__ = "transcripts"
    
    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(64), index=True, nullable=False)
    speaker = Column(String(32), nullable=False) # caller, assistant
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class TicketModel(Base):
    __tablename__ = "support_tickets"
    
    ticket_id = Column(String(64), primary_key=True)
    session_id = Column(String(64), index=True, nullable=False)
    customer_id = Column(String(64), nullable=True)
    caller_id = Column(String(32), nullable=True)
    subject = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(32), default="open") # open, in_progress, resolved
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLogModel(Base):
    __tablename__ = "audit_logs"
    
    log_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor = Column(String(64), nullable=False)
    action = Column(String(64), nullable=False)
    session_id = Column(String(64), index=True, nullable=True)
    resource_id = Column(String(64), nullable=True)
    result = Column(String(32), nullable=False) # success, failure, denied
    details_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ConsentModel(Base):
    __tablename__ = "consents"
    
    consent_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(64), nullable=False)
    session_id = Column(String(64), nullable=True)
    voiceprint_consent = Column(Boolean, default=True)
    recording_consent = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Database Engine & Session
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing database sessions."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
