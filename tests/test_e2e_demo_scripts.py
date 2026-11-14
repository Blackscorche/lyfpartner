"""End-to-End Tests for the 7 Lyfpartner Demo Scenarios specified in POC spec."""
import pytest
from httpx import AsyncClient, ASGITransport
from shared.database import init_db
from shared.seed_data import seed_database
from services.unified import unified_app
from shared.schemas import Language, AuthLevel

@pytest.fixture(autouse=True)
async def setup_db():
    from shared.database import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await seed_database()

@pytest.mark.asyncio
async def test_scenario_1_language_selection_hausa():
    """1. Call, language prompt, user says 'Hausa', greeting in Hausa."""
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create session
        resp = await client.post("/v1/sessions", json={"channel": "web", "caller_id": "+2348000000001"})
        assert resp.status_code == 200
        session_id = resp.json()["session_id"]

        # User chooses Hausa
        lang_resp = await client.post(f"/v1/sessions/{session_id}/language", json={"language": "ha"})
        assert lang_resp.status_code == 200
        assert lang_resp.json()["language"] == "ha"

        # Turn: user says greeting or language
        turn_resp = await client.post("/v1/voice/turn", json={
            "session_id": session_id,
            "text_input": "Sannu barka da zuwa Hausa"
        })
        assert turn_resp.status_code == 200
        data = turn_resp.json()
        assert "Sannu" in data["reply_text"] or "Barka" in data["reply_text"]
        assert data["reply_audio_base64"] is not None

@pytest.mark.asyncio
async def test_scenario_2_spoken_pin_and_balance_check():
    """2. Spoken PIN, 'what is my balance?', balance read back."""
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create session for Aminu Kano (Cust 001)
        resp = await client.post("/v1/sessions", json={"channel": "web", "caller_id": "+2348000000001", "language": "ha"})
        session_id = resp.json()["session_id"]

        # Caller speaks 4-digit PIN "1234"
        pin_resp = await client.post("/v1/voice/turn", json={
            "session_id": session_id,
            "text_input": "1234"
        })
        assert pin_resp.status_code == 200
        assert pin_resp.json()["auth_level"] == "basic"

        # Caller asks for balance
        bal_resp = await client.post("/v1/voice/turn", json={
            "session_id": session_id,
            "text_input": "Ina son duba kudi na" # "I want to check my money"
        })
        assert bal_resp.status_code == 200
        data = bal_resp.json()
        assert "Naira" in data["reply_text"]
        assert "250,000" in data["reply_text"] # 25,000,000 kobo = 250,000 NGN

@pytest.mark.asyncio
async def test_scenario_3_two_step_transfer_and_sms():
    """3. 'Send 5,000 naira to Musa', system reads back amount and recipient, user says yes, transfer completes, SMS receipt."""
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/v1/sessions", json={"channel": "web", "caller_id": "+2348000000001", "language": "en-ng"})
        session_id = resp.json()["session_id"]

        # Authenticate PIN first
        await client.post("/v1/voice/turn", json={"session_id": session_id, "text_input": "1234"})

        # Step 1: Voice request to send money
        turn1 = await client.post("/v1/voice/turn", json={
            "session_id": session_id,
            "text_input": "Send 5,000 naira to Musa"
        })
        assert turn1.status_code == 200
        t1_data = turn1.json()
        # System MUST confirm amount and recipient before executing
        assert "5,000" in t1_data["reply_text"]
        assert "Musa" in t1_data["reply_text"]
        assert t1_data["pending_action"]["action"] == "confirm_transfer"
        assert t1_data["pending_action"]["confirmation_token"] is not None

        # Step 2: User confirms
        turn2 = await client.post("/v1/voice/turn", json={
            "session_id": session_id,
            "text_input": "Yes proceed"
        })
        assert turn2.status_code == 200
        t2_data = turn2.json()
        assert "successful" in t2_data["reply_text"].lower() or "nasara" in t2_data["reply_text"].lower()
        assert t2_data["intent"] == "transfer_completed"

@pytest.mark.asyncio
async def test_scenario_4_pay_electricity_bill_yoruba_igbo():
    """4. Pay an electricity bill in Yoruba or Igbo."""
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Yoruba caller Babatunde
        resp = await client.post("/v1/sessions", json={"channel": "web", "caller_id": "+2348000000003", "language": "yo"})
        session_id = resp.json()["session_id"]

        # Authenticate PIN
        await client.post("/v1/voice/turn", json={"session_id": session_id, "text_input": "4321"})

        # Pay electricity bill
        turn = await client.post("/v1/voice/turn", json={
            "session_id": session_id,
            "text_input": "Mo fe san owo ina electricity"
        })
        assert turn.status_code == 200
        data = turn.json()
        assert "ina" in data["reply_text"].lower() or "bill" in data["reply_text"].lower()
        assert data["intent"] == "pay_bill"

@pytest.mark.asyncio
async def test_scenario_5_angry_caller_escalation():
    """5. Angry caller ('I want to speak to a person'): escalates, transcript visible in admin."""
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/v1/sessions", json={"channel": "web", "caller_id": "+2348000000004", "language": "en-ng"})
        session_id = resp.json()["session_id"]

        turn = await client.post("/v1/voice/turn", json={
            "session_id": session_id,
            "text_input": "I am very angry, I want to speak to a person right now!"
        })
        assert turn.status_code == 200
        data = turn.json()
        assert data["intent"] == "escalate_to_human"
        assert "human" in data["reply_text"].lower() or "representative" in data["reply_text"].lower()

        # Verify escalation ticket is created
        tickets = await client.get("/v1/support/tickets")
        assert tickets.status_code == 200
        t_list = tickets.json()
        assert any(t["session_id"] == session_id for t in t_list)

        # Verify transcript visible in admin
        admin_call = await client.get(f"/v1/admin/calls/{session_id}")
        assert admin_call.status_code == 200
        call_details = admin_call.json()
        assert len(call_details["transcript"]) > 0
        assert any("angry" in item["text"].lower() for item in call_details["transcript"])

@pytest.mark.asyncio
async def test_scenario_6_wrong_pin_three_times_and_caregiver_unlock():
    """6. Wrong PIN three times: lockout and caregiver path."""
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        customer_id = "cust_hadiza_005"
        
        # 1st wrong PIN
        w1 = await client.post("/v1/auth/pin/verify", json={"customer_id": customer_id, "pin": "0000"})
        assert w1.status_code == 200
        assert w1.json()["verified"] is False
        assert w1.json()["attempts_remaining"] == 2

        # 2nd wrong PIN
        w2 = await client.post("/v1/auth/pin/verify", json={"customer_id": customer_id, "pin": "9999"})
        assert w2.status_code == 200
        assert w2.json()["attempts_remaining"] == 1

        # 3rd wrong PIN -> Locked!
        w3 = await client.post("/v1/auth/pin/verify", json={"customer_id": customer_id, "pin": "8888"})
        assert w3.status_code == 403
        assert "locked" in w3.json()["detail"]["code"].lower()

        # Caregiver OTP sent
        otp_resp = await client.post("/v1/auth/caregiver/otp", json={"customer_id": customer_id})
        assert otp_resp.status_code == 200
        otp_code = otp_resp.json()["mock_otp"]
        assert len(otp_code) == 6

        # Caregiver verifies OTP -> Unlocked!
        unlock_resp = await client.post("/v1/auth/caregiver/otp/verify", json={"customer_id": customer_id, "otp": otp_code})
        assert unlock_resp.status_code == 200
        assert unlock_resp.json()["status"] == "unlocked"

        # Now correct PIN succeeds!
        correct_resp = await client.post("/v1/auth/pin/verify", json={"customer_id": customer_id, "pin": "1122"})
        assert correct_resp.status_code == 200
        assert correct_resp.json()["verified"] is True

@pytest.mark.asyncio
async def test_scenario_7_new_user_spoken_onboarding_with_bvn():
    """7. New user onboarding by voice with mock BVN."""
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        import secrets
        new_phone = f"+234809{secrets.randbelow(9000000) + 1000000}"
        new_bvn = f"222{secrets.randbelow(90000000) + 10000000}"
        
        # Start onboarding
        start_resp = await client.post("/v1/onboarding/start", json={
            "phone_number": new_phone,
            "preferred_language": "ha"
        })
        assert start_resp.status_code == 200

        # Verify BVN
        bvn_resp = await client.post("/v1/kyc/bvn/verify", json={"bvn": new_bvn})
        assert bvn_resp.status_code == 200
        assert bvn_resp.json()["valid"] is True

        # Face check
        face_resp = await client.post("/v1/kyc/face/check", json={"image_base64": "mock_selfie"})
        assert face_resp.status_code == 200
        assert face_resp.json()["matched"] is True

        # Complete onboarding
        comp_resp = await client.post("/v1/onboarding/complete", json={
            "phone_number": new_phone,
            "full_name": "Fatima Zahra Usman",
            "bvn": new_bvn,
            "nin": "12345678909",
            "pin": "7788",
            "preferred_language": "ha"
        })
        assert comp_resp.status_code == 200
        data = comp_resp.json()
        assert data["account_number"].startswith("0")
        assert len(data["account_number"]) == 10
        assert "Fatima" in data["full_name"]
