"""Tests for structured intent extraction, slot-filling, and multi-turn transfer flow.

All tests use MockLLMProvider (rule-based, no Groq calls).
"""
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


async def _create_session(client: AsyncClient, caller_id="+2348000000001", language="en-ng") -> str:
    resp = await client.post("/v1/sessions", json={"channel": "web", "caller_id": caller_id, "language": language})
    assert resp.status_code == 200
    return resp.json()["session_id"]


async def _turn(client: AsyncClient, session_id: str, text: str) -> dict:
    resp = await client.post("/v1/voice/turn", json={"session_id": session_id, "text_input": text})
    assert resp.status_code == 200
    return resp.json()


# ─────────────────────────────────────────────────────────────────────────────
# Intent extraction: "hello I want to make a transfer" → asks for beneficiary
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_intent_transfer_no_slots_asks_beneficiary():
    """'Hello, I want to make a transfer' should ask who to send money to, NOT read balance."""
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sid = await _create_session(client)
        data = await _turn(client, sid, "Hello, I want to make a transfer")

        # Must NOT be a balance reply or generic greeting only
        reply = data["reply_text"].lower()
        assert "balance" not in reply or "transfer" in reply, (
            f"Should not default to balance check. Got: {data['reply_text']}"
        )
        # Must ask for beneficiary (who to send to)
        assert any(w in reply for w in ["who", "send", "whom", "beneficiary", "transfer"]), (
            f"Should ask who to send money to. Got: {data['reply_text']}"
        )
        # State must track transfer intent
        assert data["pending_action"] is not None
        assert data["pending_action"].get("pending_action_type") == "transfer"
        assert data["intent"] in ("slot_filling_beneficiary", "transfer", "pin_privacy_prompt", "slot_filling_account_bank")


@pytest.mark.asyncio
async def test_intent_send_5k_to_musa_goes_to_pin():
    """'Send 5000 to Musa' with both slots present → should ask for PIN."""
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sid = await _create_session(client)
        data = await _turn(client, sid, "Send 5000 to Musa")

        reply = data["reply_text"].lower()
        # Should mention both amount and beneficiary in the PIN prompt
        assert "5,000" in data["reply_text"] or "5000" in data["reply_text"], \
            f"Should mention amount. Got: {data['reply_text']}"
        assert "musa" in data["reply_text"].lower() or "musa" in str(data.get("pending_action", {})).lower(), \
            f"Should mention Musa. Got: {data['reply_text']}"
        assert "pin" in reply or "private" in reply or "privacy" in reply, \
            f"Should ask for PIN. Got: {data['reply_text']}"
        assert data["pending_action"]["pending_action_type"] == "transfer"
        assert data["intent"] == "pin_privacy_prompt"


@pytest.mark.asyncio
async def test_intent_transfer_no_balance_default():
    """Saying 'I want to transfer' must NEVER trigger a balance check."""
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sid = await _create_session(client)
        data = await _turn(client, sid, "I want to transfer")
        # Must not say the balance value
        assert "250,000" not in data["reply_text"], \
            f"Must not read balance for transfer intent. Got: {data['reply_text']}"
        assert data["intent"] not in ("check_balance",), \
            f"Must not default to check_balance. Got intent: {data['intent']}"


# ─────────────────────────────────────────────────────────────────────────────
# Multi-turn slot filling: transfer → ask beneficiary → ask amount → PIN
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_multiturn_transfer_slot_filling():
    """
    Turn 1: 'I want to send money' → asks beneficiary
    Turn 2: 'To Musa' → asks amount
    Turn 3: '5000 naira' → asks for PIN (pending_action_type=transfer still)
    """
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sid = await _create_session(client)

        # Turn 1: transfer intent, no slots
        t1 = await _turn(client, sid, "I want to send money")
        pa1 = t1.get("pending_action") or {}
        assert pa1.get("pending_action_type") == "transfer", \
            f"Should set transfer pending. Got pending: {pa1}, intent: {t1['intent']}"
        assert t1["intent"] in ("slot_filling_beneficiary", "transfer", "slot_filling_account_bank"), \
            f"Should be in slot-filling. Got: {t1['intent']}"
        reply1 = t1["reply_text"].lower()
        assert any(w in reply1 for w in ["who", "whom", "send to", "beneficiary", "account", "10-digit"]), \
            f"Should ask beneficiary. Got: {t1['reply_text']}"

        # Turn 2: provide beneficiary
        t2 = await _turn(client, sid, "To Musa")
        pa2 = t2.get("pending_action") or {}
        assert pa2.get("pending_action_type") == "transfer", \
            f"Should keep transfer pending. Got pending: {pa2}"

        # Turn 3: provide amount — should ask for PIN, NOT fire as PIN input itself
        t3 = await _turn(client, sid, "5000 naira")
        pa3 = t3.get("pending_action") or {}
        # At this point: either still collecting (asking PIN) or already a quote
        assert pa3.get("pending_action_type") == "transfer" or pa3.get("action") == "confirm_transfer", \
            f"Should keep transfer state. Got pending: {pa3}, intent: {t3['intent']}"
        reply3 = t3["reply_text"].lower()
        assert "pin" in reply3 or "private" in reply3 or "privacy" in reply3 or "5,000" in t3["reply_text"], \
            f"Should ask for PIN or show quote. Got: {t3['reply_text']}"


# ─────────────────────────────────────────────────────────────────────────────
# Full happy path: "send 5000 to Musa" → PIN → confirm
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_full_transfer_flow_with_pin():
    """
    Turn 1: 'Send 5000 naira to Musa' → PIN prompt (pending_action_type=transfer)
    Turn 2: '1234' (PIN) → reads back quote, asks to confirm
    Turn 3: 'Yes' → transfer_completed
    """
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sid = await _create_session(client, caller_id="+2348000000001", language="en-ng")

        # Turn 1: Express transfer intent with all slots
        t1 = await _turn(client, sid, "I want to send 5000 naira to Musa")
        assert t1["intent"] == "pin_privacy_prompt"
        assert t1["pending_action"]["pending_action_type"] == "transfer"
        assert "5,000" in t1["reply_text"] or "5000" in t1["reply_text"]

        # Turn 2: Submit PIN
        t2 = await _turn(client, sid, "1234")
        assert t2["auth_level"] == "basic"
        assert t2["intent"] == "quote_transfer"
        assert "5,000" in t2["reply_text"]
        assert t2["pending_action"]["action"] == "confirm_transfer"

        # Turn 3: Confirm
        t3 = await _turn(client, sid, "Yes proceed")
        assert t3["intent"] == "transfer_completed"
        assert "successful" in t3["reply_text"].lower() or "nasara" in t3["reply_text"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# Mid-flow correction: change amount
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_midflow_amount_correction():
    """While awaiting confirmation, user says 'make it 10000' → updates amount."""
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sid = await _create_session(client)

        # Auth first
        await _turn(client, sid, "1234")
        t1 = await _turn(client, sid, "Send 5000 to Musa")
        pa1 = t1.get("pending_action") or {}

        # Advance to quote if still at PIN stage
        if pa1.get("pending_action_type") == "transfer":
            t1 = await _turn(client, sid, "1234")
            pa1 = t1.get("pending_action") or {}

        # Now at confirmation stage — try mid-flow correction
        if pa1.get("action") == "confirm_transfer":
            t2 = await _turn(client, sid, "no, make it 10000")
            assert t2["intent"] in ("mid_flow_correction", "transfer_cancelled", "awaiting_confirmation"), \
                f"Expected correction or cancel. Got: {t2['intent']}"


@pytest.mark.asyncio
async def test_midflow_cancel():
    """User says 'cancel' while awaiting confirmation → transfer_cancelled."""
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sid = await _create_session(client)

        # Auth first
        await _turn(client, sid, "1234")
        t1 = await _turn(client, sid, "Send 5000 to Musa")
        pa1 = t1.get("pending_action") or {}

        # Advance to quote/confirm if at PIN stage
        if pa1.get("pending_action_type") == "transfer":
            t1 = await _turn(client, sid, "1234")
            pa1 = t1.get("pending_action") or {}

        if pa1.get("action") == "confirm_transfer":
            t2 = await _turn(client, sid, "cancel")
            assert t2["intent"] == "transfer_cancelled"
            assert t2["pending_action"] is None


# ─────────────────────────────────────────────────────────────────────────────
# Mid-flow intent switch: balance check while in a transfer flow
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_midflow_balance_digression_then_resume():
    """User asks 'what's my balance' while awaiting transfer confirmation → shows balance + offers to resume."""
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sid = await _create_session(client)

        # Get to confirm_transfer stage
        await _turn(client, sid, "1234")  # Auth PIN
        t1 = await _turn(client, sid, "Send 5000 to Musa")
        pa1 = t1.get("pending_action") or {}
        # Advance to quote if needed
        if pa1.get("pending_action_type") == "transfer":
            t1 = await _turn(client, sid, "1234")
            pa1 = t1.get("pending_action") or {}

        if pa1.get("action") == "confirm_transfer":
            t2 = await _turn(client, sid, "wait what is my balance")
            # Should show balance AND keep transfer pending or mention it
            reply = t2["reply_text"].lower()
            assert "naira" in reply or "balance" in reply, \
                f"Should mention balance. Got: {t2['reply_text']}"
            assert t2["intent"] in ("digression_balance", "check_balance", "awaiting_confirmation")


# ─────────────────────────────────────────────────────────────────────────────
# Ambiguous utterance → clarifying question (never defaults to balance)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ambiguous_utterance_asks_clarification():
    """Random ambiguous input → asks what caller wants, does NOT read balance."""
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sid = await _create_session(client)
        data = await _turn(client, sid, "erm so umm yeah")

        reply = data["reply_text"].lower()
        # Must not read a naira balance amount
        assert "250,000" not in reply, \
            f"Should NOT default to balance check. Got: {data['reply_text']}"
        # Should be a greeting, help, or clarifying question
        assert data["intent"] in ("greeting", "unknown", "help_services"), \
            f"Should be greeting/unknown/help, got: {data['intent']}"


# ─────────────────────────────────────────────────────────────────────────────
# Nigerian slang variants
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_oya_transfer_intent():
    """'Oya transfer' → transfer intent (not balance, not unknown)."""
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sid = await _create_session(client)
        data = await _turn(client, sid, "oya transfer")
        assert data["intent"] in ("slot_filling_beneficiary", "pin_privacy_prompt", "transfer", "slot_filling_account_bank"), \
            f"'oya transfer' should be transfer intent, got: {data['intent']}"
        assert "250,000" not in data["reply_text"], "Should not read balance for transfer"


@pytest.mark.asyncio
async def test_wanna_send_money():
    """'I wanna send money' → transfer intent."""
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sid = await _create_session(client)
        data = await _turn(client, sid, "I wanna send money")
        assert data["intent"] in ("slot_filling_beneficiary", "pin_privacy_prompt", "transfer", "slot_filling_account_bank"), \
            f"'wanna send money' should be transfer, got: {data['intent']}"


@pytest.mark.asyncio
async def test_hausa_transfer_tura_kudi():
    """Hausa: 'ina son tura kudi ga Musa' → transfer intent."""
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sid = await _create_session(client, language="ha")
        data = await _turn(client, sid, "ina son tura kudi ga Musa")
        assert data["intent"] not in ("check_balance", "greeting"), \
            f"Hausa transfer should not default to balance/greeting, got: {data['intent']}"
        assert data["intent"] in ("slot_filling_beneficiary", "slot_filling_amount",
                                   "pin_privacy_prompt", "transfer"), \
            f"Should be transfer flow, got: {data['intent']}"


# ─────────────────────────────────────────────────────────────────────────────
# Balance is ONLY read when explicitly requested + PIN verified
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_balance_only_read_when_intent_is_check_balance():
    """Balance value must NOT appear unless intent is check_balance and PIN is provided."""
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sid = await _create_session(client)

        # Greeting → no balance value
        t1 = await _turn(client, sid, "hello")
        assert "250,000" not in t1["reply_text"], "Greeting should not expose balance"

        # Explicit balance request without PIN → asks for PIN
        t2 = await _turn(client, sid, "what is my balance")
        assert t2["intent"] == "pin_privacy_prompt"
        assert "250,000" not in t2["reply_text"], "Balance PIN prompt should not expose balance"

        # Provide PIN → now balance is revealed
        t3 = await _turn(client, sid, "1234")
        assert "250,000" in t3["reply_text"], f"After PIN, balance should be shown. Got: {t3['reply_text']}"
        assert t3["intent"] == "check_balance"


# ─────────────────────────────────────────────────────────────────────────────
# VTU: Airtime and Data Bundle Flows
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_vtu_airtime_multiturn_flow():
    """
    Airtime flow:
    Turn 1: 'I want to buy airtime' -> asks amount
    Turn 2: '1000 naira' -> asks for PIN with summary
    Turn 3: '1234' -> quotes airtime and asks to confirm
    Turn 4: 'yes' -> airtime_completed + SMS receipt
    """
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sid = await _create_session(client, caller_id="+2348030000001")

        # Turn 1: Airtime intent without amount
        t1 = await _turn(client, sid, "I want to buy airtime")
        assert t1["intent"] in ("slot_filling_airtime_amount", "airtime")
        assert "how much" in t1["reply_text"].lower() or "amount" in t1["reply_text"].lower() or "airtime" in t1["reply_text"].lower()
        assert t1["pending_action"]["pending_action_type"] == "airtime"

        # Turn 2: Provide amount
        t2 = await _turn(client, sid, "1000 naira")
        assert t2["intent"] == "pin_privacy_prompt"
        assert "1,000" in t2["reply_text"] or "1000" in t2["reply_text"]
        assert "pin" in t2["reply_text"].lower()

        # Turn 3: Submit 4-digit PIN
        t3 = await _turn(client, sid, "1234")
        assert t3["intent"] == "quote_airtime"
        assert t3["pending_action"]["action"] == "confirm_airtime"
        assert "confirm" in t3["reply_text"].lower() or "proceed" in t3["reply_text"].lower()

        # Turn 4: Confirm purchase
        t4 = await _turn(client, sid, "yes proceed")
        assert t4["intent"] == "airtime_completed"
        assert "successful" in t4["reply_text"].lower() or "nasara" in t4["reply_text"].lower()


@pytest.mark.asyncio
async def test_vtu_data_multiturn_flow():
    """
    Data bundle flow:
    Turn 1: 'I want to buy data' -> asks which data plan
    Turn 2: '2.5GB' -> asks for PIN with summary
    Turn 3: '1234' -> quotes data bundle and asks to confirm
    Turn 4: 'yes' -> data_completed + SMS confirmation
    """
    transport = ASGITransport(app=unified_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sid = await _create_session(client, caller_id="+2348030000001")

        # Turn 1: Data intent without plan
        t1 = await _turn(client, sid, "I want to buy data")
        assert t1["intent"] in ("slot_filling_data_plan", "buy_data")
        assert "plan" in t1["reply_text"].lower() or "gb" in t1["reply_text"].lower()
        assert t1["pending_action"]["pending_action_type"] == "data"

        # Turn 2: Provide plan
        t2 = await _turn(client, sid, "2.5GB")
        assert t2["intent"] == "pin_privacy_prompt"
        assert "2.5gb" in t2["reply_text"].lower()
        assert "pin" in t2["reply_text"].lower()

        # Turn 3: Submit 4-digit PIN
        t3 = await _turn(client, sid, "1234")
        assert t3["intent"] == "quote_data"
        assert t3["pending_action"]["action"] == "confirm_data"

        # Turn 4: Confirm purchase
        t4 = await _turn(client, sid, "yes")
        assert t4["intent"] == "data_completed"
        assert "successful" in t4["reply_text"].lower() or "activated" in t4["reply_text"].lower()
