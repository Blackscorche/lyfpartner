"""Voice biometrics and authentication logic for Lyfpartner."""
from abc import ABC, abstractmethod
import json
import secrets
from typing import List, Tuple
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.config import settings
from shared.database import CustomerModel, SessionModel, AuditLogModel
from shared.security import hash_pin, verify_pin_hash
from shared.errors import AccountLockedException, AuthenticationFailedException, LyfpartnerException
from shared.schemas import AuthLevel

class VoiceVerifyProvider(ABC):
    @abstractmethod
    async def extract_embedding(self, audio_bytes: bytes) -> List[float]:
        pass

    @abstractmethod
    async def verify_similarity(self, enrolled_embedding: List[float], audio_bytes: bytes) -> Tuple[bool, float]:
        pass

class MockVoiceVerifyProvider(VoiceVerifyProvider):
    async def extract_embedding(self, audio_bytes: bytes) -> List[float]:
        # Return 128-d normalized embedding vector
        rng = np.random.default_rng(len(audio_bytes) % 100)
        vec = rng.standard_normal(128).astype(np.float32)
        vec /= np.linalg.norm(vec)
        return vec.tolist()

    async def verify_similarity(self, enrolled_embedding: List[float], audio_bytes: bytes) -> Tuple[bool, float]:
        # Check if caller matches or if simulated reject tag present
        audio_str = audio_bytes.decode("utf-8", errors="ignore")
        if "IMPOSTOR" in audio_str:
            return False, 0.42
        return True, 0.93

def get_voice_provider() -> VoiceVerifyProvider:
    return MockVoiceVerifyProvider()
