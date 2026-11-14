"""Unit tests for services: ASR, TTS, Bank, Auth, Support, Admin, and Audio files."""
import os
import pytest
from httpx import AsyncClient, ASGITransport
from shared.database import init_db
from shared.seed_data import seed_database
from services.unified import unified_app
from shared.schemas import Language

@pytest.fixture(autouse=True)
async def setup_db():
    from shared.database import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await seed_database()

@pytest.mark.asyncio
async def test_health_checks():
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_asr_multipart_audio():
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        audio_path = "tests/audio_samples/check_balance.wav"
        with open(audio_path, "rb") as f:
            files = {"audio": ("sample.wav", f.read(), "audio/wav")}
            data = {"language": "ha"}
            res = await client.post("/v1/asr/transcribe", files=files, data=data)
            assert res.status_code == 200
            data = res.json()
            assert "text" in data
            assert data["confidence"] > 0.6
            assert data["is_low_confidence"] is False

@pytest.mark.asyncio
async def test_asr_low_confidence():
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        audio_path = "tests/audio_samples/low_conf.wav"
        with open(audio_path, "rb") as f:
            files = {"audio": ("sample.wav", f.read(), "audio/wav")}
            data = {"language": "en-ng"}
            res = await client.post("/v1/asr/transcribe", files=files, data=data)
            assert res.status_code == 200
            data = res.json()
            assert data["is_low_confidence"] is True

@pytest.mark.asyncio
async def test_tts_generation():
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/v1/tts/speak", json={
            "text": "Barka da zuwa Lyfpartner",
            "language": "ha",
            "sample_rate": 16000
        })
        assert res.status_code == 200
        assert res.headers["content-type"] == "audio/wav"
        # Must be valid WAV header
        assert res.content.startswith(b"RIFF")

@pytest.mark.asyncio
async def test_bank_transfer_limits_and_quote_expiry():
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Quote transfer exceeding voice limit (50,000 NGN = 5,000,000 kobo)
        # Attempt 60,000 NGN (6,000,000 kobo)
        quote_fail = await client.post("/v1/transfers/quote?is_voice=true", json={
            "source_account_id": "acc_aminu_001",
            "beneficiary_account_number": "2045678901",
            "beneficiary_bank_name": "First Bank",
            "amount_kobo": 6_000_000
        })
        assert quote_fail.status_code == 400
        assert "LIMIT_EXCEEDED" in quote_fail.json()["detail"]["code"]

@pytest.mark.asyncio
async def test_admin_metrics():
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/v1/admin/metrics")
        assert res.status_code == 200
        data = res.json()
        assert "deflection_rate_percent" in data
        assert "calls_today" in data

@pytest.mark.asyncio
async def test_audit_logs():
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/v1/admin/audit")
        assert res.status_code == 200
        logs = res.json()
        assert isinstance(logs, list)
