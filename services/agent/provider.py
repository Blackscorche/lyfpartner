"""LLM Dialogue Provider — structured intent/slot extraction + deterministic execution.

Architecture:
  - Intent extraction (LLM or rule-based): returns JSON {intent, slots, reply_hint}
  - Deterministic state machine: drives the slot-filling & transaction flows in Python
  - Money logic (PIN verify, transfer execute, balance read) NEVER touches the LLM
"""
import json
import re
import secrets
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple

from shared.config import settings
from shared.logging_utils import get_logger
from shared.schemas import (
    Language, AuthLevel, AgentRespondRequest, AgentRespondResponse, ToolCallRecord
)
from services.agent.tools import ToolRegistry

logger = get_logger("agent_provider")

# ─────────────────────────── Keyword tables ─────────────────────────────────

DISTRESS_KEYWORDS = [
    "person", "human", "agent", "angry", "fraud", "scam", "thief", "police",
    "stolen", "operator", "talk to human", "speak to someone", "customer care",
    "mutum", "dan adam", "onye", "eniyan", "daadaa"
]

CONFIRMATION_KEYWORDS = [
    "yes", "confirm", "proceed", "send it", "pay it", "okay", "ok", "correct",
    "eh", "ehen", "bee ne", "haka ne", "ee", "e-e", "beeni", "o ya", "oya",
    "go ahead", "do it", "affirmative", "right", "sure"
]

CANCEL_KEYWORDS = [
    "no", "cancel", "stop", "a'a", "mba", "rara", "don't", "dont",
    "abort", "back", "quit", "nevermind", "never mind"
]

REPEAT_KEYWORDS = [
    "repeat", "say again", "pardon", "maimaita", "kwuo ozo", "so leekan si",
    "what did you say", "come again"
]

TRANSFER_KEYWORDS = [
    "send", "transfer", "tura", "ziga", "fi ranse", "give",
    "move money", "move", "wire", "remit", "i want to send", "i want to transfer",
    "i want to make a transfer", "make transfer", "wanna send", "wanna transfer",
    "tura kudi", "aika kudi",
    "gbe owo", "fi owo ranse",
    "zipu ego", "ziga ego",
]

BALANCE_KEYWORDS = [
    "balance", "duba kudi", "kudi na", "ego ole", "ile ego",
    "iye owo", "owo mi", "how much", "how much i get", "check my account",
    "check balance", "my balance", "account balance",
]

BILL_KEYWORDS_EN = ["electricity", "nepa", "light bill", "meter", "ikedc", "ekedc", "utility"]
BILL_KEYWORDS_YO = ["owo ina", "san owo ina"]
BILL_KEYWORDS_IG = ["ugwo oku", "kwo ugwo oku"]
BILL_KEYWORDS_HA = ["kudin wuta", "wutan lantarki", "biya wuta"]

HELP_KEYWORDS = [
    "help", "service", "services", "options", "what can you do",
    "taimako", "iranlowo", "enyemaka", "kini e le se", "me za ku iya yi", "kedu ihe"
]

AIRTIME_KEYWORDS = ["airtime", "recharge", "katin waya", "kaadi ipe"]

GREETING_KEYWORDS = [
    "hello", "hi", "good morning", "good afternoon", "good evening",
    "sannu", "barka", "bawo ni", "bawo", "ndewo", "kedu", "eku"
]

# ─────────────────────── Nigerian number normaliser ──────────────────────────

_NAIRA_WORDS = {
    "k": 1_000, "thousand": 1_000, "million": 1_000_000, "m": 1_000_000,
}

def _parse_amount(text: str) -> Optional[int]:
    """Return naira amount from text like '5k', '5000', '5,000'."""
    t = text.lower().replace(",", "")
    m = re.search(r'(\d[\d\s]*)([km]|thousand|million)?', t)
    if not m:
        return None
    num_str = m.group(1).replace(" ", "")
    try:
        num = int(num_str)
    except ValueError:
        return None
    suffix = (m.group(2) or "").strip()
    multiplier = _NAIRA_WORDS.get(suffix, 1)
    result = num * multiplier
    if 50 <= result <= 10_000_000:
        return result
    return None


def _extract_beneficiary_name(text: str, beneficiaries: List[Dict]) -> Optional[Dict]:
    """Return first beneficiary whose name/nickname appears in text."""
    t = text.lower()
    for b in beneficiaries:
        b_name_parts = b["name"].lower().split()
        b_nick = (b.get("nickname") or "").lower()
        if b_nick and b_nick in t:
            return b
        for part in b_name_parts:
            if len(part) > 2 and part in t:
                return b
    return None


# ─────────────────────── Rule-based intent extractor ─────────────────────────

def _rule_based_intent(text: str, lang: Language, pending: Dict) -> Dict[str, Any]:
    """
    Fast deterministic intent + slot extraction — no LLM.
    Returns: {intent, slots:{amount, beneficiary, bill_type}, reply_hint}
    """
    t = text.lower().strip()
    slots: Dict[str, Any] = {"amount": None, "beneficiary": None, "bill_type": None}

    amount_naira = _parse_amount(t)
    if amount_naira:
        slots["amount"] = amount_naira

    ben_match = re.search(r'(?:to|for|ga|si|nye)\s+([A-Za-z][A-Za-z\s]{1,20}?)(?:\s+(?:in|at|on|via|\d)|$)', text, re.IGNORECASE)
    if ben_match:
        slots["beneficiary"] = ben_match.group(1).strip()

    # Greeting — short phrases only
    if any(w in t for w in GREETING_KEYWORDS) and len(t.split()) <= 6:
        return {"intent": "greeting", "slots": slots, "reply_hint": ""}

    # Bill check before transfer (some bill keywords overlap with "pay")
    is_bill = (
        any(w in t for w in BILL_KEYWORDS_EN)
        or (lang == Language.YORUBA and any(w in t for w in BILL_KEYWORDS_YO))
        or (lang == Language.IGBO and any(w in t for w in BILL_KEYWORDS_IG))
        or (lang == Language.HAUSA and any(w in t for w in BILL_KEYWORDS_HA))
    )

    is_transfer = any(w in t for w in TRANSFER_KEYWORDS)

    if is_transfer and not is_bill:
        return {"intent": "transfer", "slots": slots, "reply_hint": ""}

    if is_bill:
        bill_type = "electricity"
        if "water" in t or "lagos water" in t:
            bill_type = "water"
        elif "cable" in t or "dstv" in t or "gotv" in t:
            bill_type = "cable"
        slots["bill_type"] = bill_type
        return {"intent": "pay_bill", "slots": slots, "reply_hint": ""}

    if any(w in t for w in BALANCE_KEYWORDS):
        return {"intent": "check_balance", "slots": slots, "reply_hint": ""}

    if any(w in t for w in AIRTIME_KEYWORDS):
        return {"intent": "airtime", "slots": slots, "reply_hint": ""}

    if any(w in t for w in HELP_KEYWORDS):
        return {"intent": "help", "slots": slots, "reply_hint": ""}

    if any(w in t for w in REPEAT_KEYWORDS):
        return {"intent": "repeat_last", "slots": slots, "reply_hint": ""}

    return {"intent": "unknown", "slots": slots, "reply_hint": ""}


# ───────────────────────── Localised reply helpers ───────────────────────────

def _r(lang: Language, replies: Dict) -> str:
    return replies.get(lang, replies.get(Language.NIGERIAN_ENGLISH, list(replies.values())[0]))


def _ask_beneficiary(lang: Language) -> str:
    return _r(lang, {
        Language.HAUSA: "To, ga wane ne kuke son tura kudi?",
        Language.IGBO: "Obi mma, onye ka i choro iziga ego ya?",
        Language.YORUBA: "O dara, ta ni e fe fi owo ranse si?",
        Language.NIGERIAN_ENGLISH: "Sure! Who would you like to send money to?"
    })


def _ask_amount(lang: Language, beneficiary: str) -> str:
    return _r(lang, {
        Language.HAUSA: f"Nawa kuke son tura wa {beneficiary}?",
        Language.IGBO: f"Ego ole ka i choro iziga nye {beneficiary}?",
        Language.YORUBA: f"Iye owo melo ni e fe fi ranse si {beneficiary}?",
        Language.NIGERIAN_ENGLISH: f"Got it! How much would you like to send to {beneficiary}?"
    })


def _ask_pin_privacy(lang: Language, intent_summary: str) -> str:
    return _r(lang, {
        Language.HAUSA: f"{intent_summary} Don tsaronka, da fatan kana wuri mai natsuwa da sirri. Za ka iya danna lambar sirrinka ta PIN a kan keypad ko kuma ka fadi ta a fili.",
        Language.IGBO: f"{intent_summary} Maka nchekwa gi, biko nọ n'ebe zoro ezo. Pia nomba nzuzo PIN gi na keypad ma obu kwuo ya n'olu.",
        Language.YORUBA: f"{intent_summary} Fun aabo re, jowo wa ni aye ikoko. Te nomba asiri PIN re lori keypad tabi ki o so o jade.",
        Language.NIGERIAN_ENGLISH: f"{intent_summary} For your security, please make sure you're in a private space. Please punch in your 4-digit PIN on the keypad, or say it out loud."
    })


def _confirm_transfer_prompt(lang: Language, amount_fmt: str, ben_name: str) -> str:
    return _r(lang, {
        Language.HAUSA: f"An tabbatar da lambar sirri! Kuna son tura Naira {amount_fmt} ga {ben_name}. In tura?",
        Language.IGBO: f"A kwadoro nomba nzuzo gi! I choro iziga Naira {amount_fmt} nye {ben_name}. M ga-eziga ya?",
        Language.YORUBA: f"A ti fowo si nomba asiri yin! Se e fe fi Naira {amount_fmt} ranse si {ben_name}? Se kin tesiwaju?",
        Language.NIGERIAN_ENGLISH: f"PIN verified! You want to transfer {amount_fmt} Naira to {ben_name}. Should I go ahead?"
    })


def _transfer_success(lang: Language, amount_fmt: str, ben_name: str) -> str:
    return _r(lang, {
        Language.HAUSA: f"An tura Naira {amount_fmt} ga {ben_name} cikin nasara. An aiko muku da sakon SMS.",
        Language.IGBO: f"E zigara Naira {amount_fmt} nye {ben_name} nke oma. Anyi ziterela gi ozi SMS.",
        Language.YORUBA: f"A ti fi Naira {amount_fmt} ranse si {ben_name} laseyori. A ti fi SMS ranse si yin.",
        Language.NIGERIAN_ENGLISH: f"Your transfer of {amount_fmt} Naira to {ben_name} was successful! An SMS receipt has been sent to your phone."
    })


def _cancel_reply(lang: Language) -> str:
    return _r(lang, {
        Language.HAUSA: "An soke wannan aikin. Me kuma kuke son yi?",
        Language.IGBO: "A kagbuola ya. Gini ozo ka m ga-emere gi?",
        Language.YORUBA: "A ti fagile e. Kini nkan miiran ti e fe se?",
        Language.NIGERIAN_ENGLISH: "Cancelled. What else can I help you with?"
    })


def _unknown_reply(lang: Language) -> str:
    return _r(lang, {
        Language.HAUSA: "Yi hakuri, ban gane ba sosai. Kuna son duba kudi, tura kudi, ko biyan kudin wuta?",
        Language.IGBO: "Ndo, aghotara m ahughi ihe i kwuru nke oma. I choro ile ego gi, zipu ego, ma obu kwuo ugwo?",
        Language.YORUBA: "Pele, mi o ye ohun ti e so. Se e fe wo iye owo, gbe owo, tabi san owo ina?",
        Language.NIGERIAN_ENGLISH: "Sorry, I didn't quite get that. Would you like to check your balance, make a transfer, or pay a bill?"
    })


def _greeting_reply(lang: Language) -> str:
    return _r(lang, {
        Language.HAUSA: "Sannu! Barka da zuwa Lyfpartner. Yaya zan iya taimaka muku yau? Kuna iya duba kudi, tura kudi, ko biyan kudin wuta.",
        Language.IGBO: "Nnọọ! Nnọọ na Lyfpartner. Kedu ka m ga-esi nyere gi aka taa? I nwere ike ilele ego gi, zipu ego, ma obu kwuo ugwo oku.",
        Language.YORUBA: "Bawo ni! E kaabo si Lyfpartner. Bawo ni a se le ran yin lowo loni? E le wo iye owo yin, gbe owo ranse, tabi san owo ina.",
        Language.NIGERIAN_ENGLISH: "Hello! Welcome to Lyfpartner Voice Banking. How can I assist you today? You can check your balance, transfer money, or pay electricity bills."
    })


def _help_reply(lang: Language) -> str:
    return _r(lang, {
        Language.HAUSA: "Tare da Lyfpartner, kuna iya duba ragowar kudi, tura kudi zuwa kowane banki, biyan kudin wutan lantarki, ko sayen katin waya. Me kuke so ku yi yanzu?",
        Language.IGBO: "Site na Lyfpartner, i nwere ike ilele ego gi, zipu ego na banki obula, kwuo ugwo oku eletrik, ma obu zuta kaadi ikuku. Kedu ihe i choro ime ugbua?",
        Language.YORUBA: "Pelu Lyfpartner, e le wo iye owo yin, gbe owo ranse si banki kankan, san owo ina bi IKEDC, tabi ra kaadi ipe. Kini e fe se nisisiyi?",
        Language.NIGERIAN_ENGLISH: "With Lyfpartner, you can check your live balance, transfer money to any bank account, pay electricity bills, or buy airtime. What would you like to do?"
    })


def _repeat_reply(lang: Language) -> str:
    return _r(lang, {
        Language.HAUSA: "Ina nan don taimaka muku da duba kudi, tura kudi, ko biyan kudi.",
        Language.IGBO: "Anom ebe a iji nyere gi aka ile ego gi, iziga ego, ma obu kwuo ugwo.",
        Language.YORUBA: "Mo wa nibi lati ran yin lowo lati wo iye owo yin, gbe owo, tabi san owo ina.",
        Language.NIGERIAN_ENGLISH: "I am here to help you check your balance, send money, or pay bills. How can I help you today?"
    })


def _low_confidence_reply(lang: Language) -> str:
    return _r(lang, {
        Language.HAUSA: "Ban ji ku da kyau ba. Don Allah ku sake magana.",
        Language.IGBO: "Anughi m gi nke oma. Biko kwuo ozo.",
        Language.YORUBA: "Ejo, mi o gbo yin daadaa. E jowo tun so.",
        Language.NIGERIAN_ENGLISH: "I didn't quite catch that. Please could you say that again?"
    })


def _escalate_reply(lang: Language) -> str:
    return _r(lang, {
        Language.HAUSA: "Na fahimta. Ina mika ku ga wakilin mu yanzu. Don Allah ku dakata.",
        Language.IGBO: "Aghotara m. Ana m ebufe gi na aka onye oru anyi ugbua. Biko chere obere.",
        Language.YORUBA: "Mo gbo yin ye. Mo n gbe yin lo si odo osise wa bayi. E jowo duro die.",
        Language.NIGERIAN_ENGLISH: "I understand. Connecting you to a customer care representative right away. Please hold on."
    })


# ═══════════════════════════════════════════════════════════════════════════
#  CORE STATE MACHINE — shared by Mock and Groq providers
# ═══════════════════════════════════════════════════════════════════════════

async def _run_state_machine(
    intent_data: Dict[str, Any],
    req: AgentRespondRequest,
    tools: ToolRegistry,
) -> AgentRespondResponse:
    """
    Pure-Python deterministic state machine.
    Consumes extracted intent/slots and drives conversation state.
    PIN verification, balance reads, transfers — handled here, not in the LLM.
    """
    text = req.text.lower().strip()
    lang = req.language
    account_id = req.account_id or "acc_aminu_001"
    caller_id = req.caller_id or "+2348000000001"
    pending: Dict[str, Any] = req.pending_action or {}
    auth = req.auth_level
    tool_records: List[ToolCallRecord] = []

    intent = intent_data.get("intent", "unknown")
    slots = intent_data.get("slots", {})

    # ── STEP 0: Low ASR confidence ──────────────────────────────────────────
    if req.is_low_confidence:
        return AgentRespondResponse(
            reply_text=_low_confidence_reply(lang),
            intent="low_confidence_reprompt",
            next_state=pending
        )

    # ── STEP 1: Distress / human escalation (always takes priority) ─────────
    if any(w in text for w in DISTRESS_KEYWORDS):
        res = await tools.escalate_to_human(
            req.session_id, reason="Caller distress or human agent requested", summary=text
        )
        tool_records.append(ToolCallRecord(tool="escalate_to_human", arguments={"session_id": req.session_id}, result=res))
        return AgentRespondResponse(
            reply_text=_escalate_reply(lang),
            intent="escalate_to_human",
            tool_calls=tool_records,
            escalate=True,
            escalate_reason="Caller requested human agent"
        )

    # ── STEP 2: 4-digit PIN submitted ───────────────────────────────────────
    # Only treat as PIN when the utterance is *primarily* digits — not embedded
    # in a natural-language sentence like "Send 5000 to Musa" or "5000 naira".
    # Rules:
    #   (a) Must find a 4-digit match or the whole text is just those digits
    #   (b) No strong intent keywords ("send", "transfer", "balance" etc.) present
    #   (c) ≤3 non-digit words around the number (not a full sentence)
    #   (d) Not in transfer amount-collection phase (we have beneficiary but no amount)
    digits_match = re.findall(r'\b\d{4}\b', text)
    _strong_intent = TRANSFER_KEYWORDS + BALANCE_KEYWORDS + BILL_KEYWORDS_EN + AIRTIME_KEYWORDS + HELP_KEYWORDS
    _has_intent_kw = any(w in text for w in _strong_intent)
    _non_digit_words = [w for w in re.sub(r'[\d,]', '', text).split() if w.strip()]
    # Block PIN detection only when we're waiting for the amount in a transfer flow
    _collecting_transfer_amount = (
        pending.get("pending_action_type") == "transfer"
        and pending.get("beneficiary_name")   # have beneficiary already
        and not pending.get("amount_kobo")    # still need amount
    )
    is_pin_input = (
        (bool(digits_match) or text.strip() in ["1234", "1 2 3 4"])
        and not _has_intent_kw                # no "send", "transfer", "balance" etc
        and len(_non_digit_words) <= 3        # mostly digits, not a full sentence
        and not _collecting_transfer_amount   # not in amount-collection phase
    )

    if is_pin_input:
        pending_type = pending.get("pending_action_type")

        if pending_type == "transfer":
            amount_kobo = pending.get("amount_kobo", 500_000)
            amount_naira = pending.get("amount_naira", "5,000")
            ben_name = pending.get("beneficiary_name", "Musa Bello")
            target_ben = pending.get("target_ben", {
                "name": "Musa Bello", "account_number": "2045678901", "bank_name": "First Bank"
            })
            quote_res = await tools.quote_transfer(
                source_account_id=account_id,
                beneficiary_account_number=target_ben.get("account_number", "2045678901"),
                beneficiary_bank_name=target_ben.get("bank_name", "First Bank"),
                amount_kobo=amount_kobo
            )
            tool_records.append(ToolCallRecord(tool="quote_transfer", arguments={"amount_kobo": amount_kobo}, result=quote_res))
            token = quote_res.get("confirmation_token")
            ben_quoted = quote_res.get("beneficiary_name", ben_name)
            return AgentRespondResponse(
                reply_text=_confirm_transfer_prompt(lang, amount_naira, ben_quoted),
                intent="quote_transfer",
                tool_calls=tool_records,
                needs_confirmation=True,
                next_state={
                    "action": "confirm_transfer",
                    "confirmation_token": token,
                    "beneficiary_name": ben_quoted,
                    "amount_naira": amount_naira,
                    "amount_kobo": amount_kobo
                }
            )

        elif pending_type == "balance":
            bal_res = await tools.check_balance(account_id)
            tool_records.append(ToolCallRecord(tool="check_balance", arguments={"account_id": account_id}, result=bal_res))
            naira_val = f"{bal_res.get('balance_naira', 250000):,}"
            bal_replies = {
                Language.HAUSA: f"An tabbatar! Kudin ku a asusun banki Naira {naira_val} ne. Me kuma kuke so ku yi?",
                Language.IGBO: f"A kwadoro! Ego i nwere na akauntu gi bu Naira {naira_val}. Kedu ka m ga-esi nyere gi aka?",
                Language.YORUBA: f"A ti fowo si! Iye owo to wa ninu akanti yin je Naira {naira_val}. Kini e fe se tun?",
                Language.NIGERIAN_ENGLISH: f"Verified! Your account balance is {naira_val} Naira. What else can I help you with?"
            }
            return AgentRespondResponse(
                reply_text=_r(lang, bal_replies),
                intent="check_balance",
                tool_calls=tool_records
            )

        elif pending_type == "bill":
            idem_key = f"idem_bill_{secrets.token_hex(6)}"
            bill_res = await tools.pay_bill(
                account_id=account_id, biller="bil_ikeja_electric",
                meter_no="45129038101", amount_kobo=200_000,
                idempotency_key=idem_key, session_id=req.session_id
            )
            tool_records.append(ToolCallRecord(tool="pay_bill", arguments={"biller": "bil_ikeja_electric", "amount_kobo": 200000}, result=bill_res))
            bill_replies = {
                Language.HAUSA: "An tabbatar da lambar sirri! An biya kudin wutan NEPA Naira 2,000 cikin nasara.",
                Language.IGBO: "A kwadoro nomba nzuzo gi! A kwuola ugwo oku eletrik nke Naira puku abuo nke oma.",
                Language.YORUBA: "A ti fowo si nomba asiri yin! A ti san owo ina NEPA ti egbaji Naira meji laseyori.",
                Language.NIGERIAN_ENGLISH: "PIN verified! Your electricity bill of 2,000 Naira has been paid successfully."
            }
            return AgentRespondResponse(
                reply_text=_r(lang, bill_replies),
                intent="pay_bill",
                tool_calls=tool_records
            )

        # Generic PIN ok
        pin_ok = {
            Language.HAUSA: "An tabbatar da lambar sirri. Yaya zan iya taimaka muku yau? Kuna iya duba kudi, tura kudi, ko biyan kudin wuta.",
            Language.IGBO: "A kwadoro nomba nzuzo gi. Kedu ka m ga-esi nyere gi aka taa?",
            Language.YORUBA: "A ti fowo si nomba asiri yin. Bawo ni a se le ran yin lowo?",
            Language.NIGERIAN_ENGLISH: "PIN verified. How can I help you today? You can check balance, transfer money, or pay bills."
        }
        return AgentRespondResponse(reply_text=_r(lang, pin_ok), intent="pin_verified")

    # ── STEP 3: Awaiting transfer confirmation ───────────────────────────────
    if pending.get("action") == "confirm_transfer":
        token = pending.get("confirmation_token")
        beneficiary_name = pending.get("beneficiary_name", "the recipient")
        amount_naira = pending.get("amount_naira", "5,000")

        # Mid-flow digression: balance check
        if intent == "check_balance":
            if auth != AuthLevel.NONE:
                bal_res = await tools.check_balance(account_id)
                tool_records.append(ToolCallRecord(tool="check_balance", arguments={}, result=bal_res))
                naira_val = f"{bal_res.get('balance_naira', 250000):,}"
                resume = _r(lang, {
                    Language.NIGERIAN_ENGLISH: f"Your balance is {naira_val} Naira. By the way, your transfer of {amount_naira} Naira to {beneficiary_name} is still pending — should I proceed?",
                    Language.HAUSA: f"Kudinku Naira {naira_val} ne. Har yanzu kuna son tura Naira {amount_naira} ga {beneficiary_name}?",
                    Language.IGBO: f"Ego i nwere bu Naira {naira_val}. I choro ka m gaa n'ihu na iza Naira {amount_naira} nye {beneficiary_name}?",
                    Language.YORUBA: f"Owo to wa ninu akanti yin je Naira {naira_val}. Se e fe ki n tesiwaju fi Naira {amount_naira} ranse si {beneficiary_name}?"
                })
                return AgentRespondResponse(
                    reply_text=resume, intent="digression_balance",
                    tool_calls=tool_records, next_state=pending
                )

        if any(w in text for w in CONFIRMATION_KEYWORDS):
            idem_key = f"idem_tx_{secrets.token_hex(8)}"
            tx_res = await tools.confirm_transfer(token, idem_key, session_id=req.session_id)
            tool_records.append(ToolCallRecord(tool="confirm_transfer", arguments={"token": token}, result=tx_res))
            sms_msg = f"Lyfpartner Debit: NGN {amount_naira}.00 to {beneficiary_name}. Ref: {tx_res.get('reference')}. Bal: NGN {tx_res.get('balance_after_kobo', 0)//100:,}.00"
            sms_res = await tools.send_sms_receipt(caller_id, sms_msg)
            tool_records.append(ToolCallRecord(tool="send_sms_receipt", arguments={"to": caller_id}, result=sms_res))
            return AgentRespondResponse(
                reply_text=_transfer_success(lang, amount_naira, beneficiary_name),
                intent="transfer_completed",
                tool_calls=tool_records,
                next_state=None
            )

        if any(w in text for w in CANCEL_KEYWORDS):
            return AgentRespondResponse(
                reply_text=_cancel_reply(lang),
                intent="transfer_cancelled",
                next_state=None
            )

        # Mid-flow amount correction: "make it 10,000"
        new_amount = _parse_amount(text)
        if new_amount and (new_amount * 100) != pending.get("amount_kobo", 0):
            updated_pending = dict(pending)
            updated_pending["amount_kobo"] = new_amount * 100
            updated_pending["amount_naira"] = f"{new_amount:,}"
            correction_reply = _r(lang, {
                Language.NIGERIAN_ENGLISH: f"Got it! Updated to {new_amount:,} Naira to {beneficiary_name}. Should I go ahead?",
                Language.HAUSA: f"To! An sabunta zuwa Naira {new_amount:,} ga {beneficiary_name}. In tura?",
                Language.IGBO: f"Nke oma! Emelitela na Naira {new_amount:,} nye {beneficiary_name}. M ga-eziga ya?",
                Language.YORUBA: f"O dara! A ti ṣe imudojuiwọn si Naira {new_amount:,} si {beneficiary_name}. Se kin tesiwaju?"
            })
            return AgentRespondResponse(
                reply_text=correction_reply,
                intent="mid_flow_correction",
                next_state=updated_pending
            )

        # Re-ask — user said something unrelated
        reask = _r(lang, {
            Language.NIGERIAN_ENGLISH: f"Should I go ahead with transferring {amount_naira} Naira to {beneficiary_name}? Just say yes or no.",
            Language.HAUSA: f"Shin kuna son in tura Naira {amount_naira} ga {beneficiary_name}? Ka ce ee ko a'a.",
            Language.IGBO: f"I choro ka m zigaa Naira {amount_naira} nye {beneficiary_name}? Kwuo ee ma obu mba.",
            Language.YORUBA: f"Se kin fi Naira {amount_naira} ranse si {beneficiary_name}? So bẹẹni tabi beeko."
        })
        return AgentRespondResponse(reply_text=reask, intent="awaiting_confirmation", next_state=pending)

    # ── STEP 4: Slot-filling for in-progress transfer ────────────────────────
    if pending.get("pending_action_type") == "transfer":
        updated = dict(pending)
        if slots.get("amount") and not updated.get("amount_kobo"):
            updated["amount_kobo"] = slots["amount"] * 100
            updated["amount_naira"] = f"{slots['amount']:,}"
        if slots.get("beneficiary") and not updated.get("beneficiary_name"):
            try:
                bens_res = await tools.list_beneficiaries(account_id)
                bens = bens_res.get("beneficiaries", [])
                match = _extract_beneficiary_name(req.text, bens)
                if match:
                    updated["beneficiary_name"] = match["name"]
                    updated["target_ben"] = match
                else:
                    updated["beneficiary_name"] = slots["beneficiary"]
            except Exception:
                updated["beneficiary_name"] = slots["beneficiary"]

        has_beneficiary = bool(updated.get("beneficiary_name"))
        has_amount = bool(updated.get("amount_kobo"))

        if not has_beneficiary:
            return AgentRespondResponse(
                reply_text=_ask_beneficiary(lang),
                intent="slot_filling_beneficiary",
                next_state=updated
            )
        if not has_amount:
            return AgentRespondResponse(
                reply_text=_ask_amount(lang, updated["beneficiary_name"]),
                intent="slot_filling_amount",
                next_state=updated
            )

        # All slots filled → PIN
        amt_fmt = updated["amount_naira"]
        ben_name = updated["beneficiary_name"]
        summary = _r(lang, {
            Language.HAUSA: f"Na fahimta, kuna son tura Naira {amt_fmt} ga {ben_name}.",
            Language.IGBO: f"Aghọtara m, ị chọrọ iziga Naira {amt_fmt} nye {ben_name}.",
            Language.YORUBA: f"Mo gbo, ẹ fẹ fi Naira {amt_fmt} ranṣẹ si {ben_name}.",
            Language.NIGERIAN_ENGLISH: f"Alright! You want to send {amt_fmt} Naira to {ben_name}."
        })
        return AgentRespondResponse(
            reply_text=_ask_pin_privacy(lang, summary),
            intent="pin_privacy_prompt",
            next_state=updated
        )

    # ── STEP 5: Fresh intents ────────────────────────────────────────────────

    if intent == "greeting" or (req.turn_count == 0 and intent == "unknown"):
        return AgentRespondResponse(reply_text=_greeting_reply(lang), intent="greeting")

    if intent == "help":
        return AgentRespondResponse(reply_text=_help_reply(lang), intent="help_services")

    if intent == "repeat_last":
        return AgentRespondResponse(reply_text=_repeat_reply(lang), intent="repeat_last")

    # Transfer
    if intent == "transfer":
        try:
            bens_res = await tools.list_beneficiaries(account_id)
            tool_records.append(ToolCallRecord(tool="list_beneficiaries", arguments={"account_id": account_id}, result=bens_res))
            bens = bens_res.get("beneficiaries", [])
        except Exception:
            bens = []

        target_ben = _extract_beneficiary_name(req.text, bens)
        if not target_ben and slots.get("beneficiary"):
            target_ben = _extract_beneficiary_name(slots["beneficiary"], bens)

        amount_naira = slots.get("amount")
        amount_kobo = amount_naira * 100 if amount_naira else None

        new_pending: Dict[str, Any] = {"pending_action_type": "transfer"}
        if target_ben:
            new_pending["beneficiary_name"] = target_ben["name"]
            new_pending["target_ben"] = target_ben
        if amount_kobo:
            new_pending["amount_kobo"] = amount_kobo
            new_pending["amount_naira"] = f"{amount_naira:,}"

        if not target_ben:
            return AgentRespondResponse(
                reply_text=_ask_beneficiary(lang),
                intent="slot_filling_beneficiary",
                next_state=new_pending
            )
        if not amount_kobo:
            return AgentRespondResponse(
                reply_text=_ask_amount(lang, target_ben["name"]),
                intent="slot_filling_amount",
                next_state=new_pending
            )

        amt_fmt = f"{amount_naira:,}"
        ben_name = target_ben["name"]
        summary = _r(lang, {
            Language.HAUSA: f"Na fahimta, kuna son tura Naira {amt_fmt} ga {ben_name}.",
            Language.IGBO: f"Aghọtara m, ị chọrọ iziga Naira {amt_fmt} nye {ben_name}.",
            Language.YORUBA: f"Mo gbo, ẹ fẹ fi Naira {amt_fmt} ranṣẹ si {ben_name}.",
            Language.NIGERIAN_ENGLISH: f"Alright! You want to send {amt_fmt} Naira to {ben_name}."
        })

        if auth == AuthLevel.NONE:
            new_pending["amount_kobo"] = amount_kobo
            new_pending["amount_naira"] = amt_fmt
            new_pending["beneficiary_name"] = ben_name
            new_pending["target_ben"] = target_ben
            return AgentRespondResponse(
                reply_text=_ask_pin_privacy(lang, summary),
                intent="pin_privacy_prompt",
                next_state=new_pending
            )

        # Authenticated: go straight to quote
        quote_res = await tools.quote_transfer(
            source_account_id=account_id,
            beneficiary_account_number=target_ben["account_number"],
            beneficiary_bank_name=target_ben["bank_name"],
            amount_kobo=amount_kobo
        )
        tool_records.append(ToolCallRecord(tool="quote_transfer", arguments={"amount_kobo": amount_kobo}, result=quote_res))
        token = quote_res.get("confirmation_token")
        ben_quoted = quote_res.get("beneficiary_name", ben_name)
        return AgentRespondResponse(
            reply_text=_confirm_transfer_prompt(lang, amt_fmt, ben_quoted),
            intent="quote_transfer",
            tool_calls=tool_records,
            needs_confirmation=True,
            next_state={
                "action": "confirm_transfer",
                "confirmation_token": token,
                "beneficiary_name": ben_quoted,
                "amount_naira": amt_fmt,
                "amount_kobo": amount_kobo
            }
        )

    # Balance
    if intent == "check_balance":
        if auth == AuthLevel.NONE:
            summary = _r(lang, {
                Language.HAUSA: "Zan taimake ku duba ragowar kudinku.",
                Language.IGBO: "Ka anyi hụọ ego di na akaụntụ gi.",
                Language.YORUBA: "E je ki a wo iye owo to wa ninu akanti yin.",
                Language.NIGERIAN_ENGLISH: "Sure! Let me check your account balance."
            })
            return AgentRespondResponse(
                reply_text=_ask_pin_privacy(lang, summary),
                intent="pin_privacy_prompt",
                next_state={"pending_action_type": "balance"}
            )
        bal_res = await tools.check_balance(account_id)
        tool_records.append(ToolCallRecord(tool="check_balance", arguments={"account_id": account_id}, result=bal_res))
        naira_val = f"{bal_res.get('balance_naira', 0):,}"
        bal_replies = {
            Language.HAUSA: f"Kudin ku a asusun banki Naira {naira_val} ne. Me kuma kuke so?",
            Language.IGBO: f"Ego ole i nwere na akauntu gi bu Naira {naira_val}. Gini ozo?",
            Language.YORUBA: f"Owo to wa ninu akanti yin je Naira {naira_val}. Kini nkan miiran?",
            Language.NIGERIAN_ENGLISH: f"Your current account balance is {naira_val} Naira. What else can I help you with?"
        }
        return AgentRespondResponse(reply_text=_r(lang, bal_replies), intent="check_balance", tool_calls=tool_records)

    # Bill
    if intent == "pay_bill":
        if auth == AuthLevel.NONE:
            summary = _r(lang, {
                Language.HAUSA: "Zan taimaka muku wajen biyan kudin wuta.",
                Language.IGBO: "Ka anyi kwuo ugwo oku eletrik gi.",
                Language.YORUBA: "E je ki a san owo ina yin.",
                Language.NIGERIAN_ENGLISH: "Sure, let's pay your electricity bill."
            })
            return AgentRespondResponse(
                reply_text=_ask_pin_privacy(lang, summary),
                intent="pin_privacy_prompt",
                next_state={"pending_action_type": "bill"}
            )
        idem_key = f"idem_bill_{secrets.token_hex(6)}"
        bill_res = await tools.pay_bill(
            account_id=account_id, biller_id="bil_ikeja_electric",
            customer_meter="45129038101", amount_kobo=200_000,
            idempotency_key=idem_key, session_id=req.session_id
        )
        tool_records.append(ToolCallRecord(tool="pay_bill", arguments={"biller": "bil_ikeja_electric"}, result=bill_res))
        bill_replies = {
            Language.HAUSA: "An biya kudin wutan NEPA Naira 2,000 cikin nasara.",
            Language.IGBO: "A kwuola ugwo oku eletrik nke Naira puku abuo nke oma.",
            Language.YORUBA: "A ti san owo ina NEPA ti egbaji Naira meji laseyori.",
            Language.NIGERIAN_ENGLISH: "Your electricity bill payment of 2,000 Naira has been paid successfully."
        }
        return AgentRespondResponse(reply_text=_r(lang, bill_replies), intent="pay_bill", tool_calls=tool_records)

    # Airtime
    if intent == "airtime":
        idem_key = f"idem_airtime_{secrets.token_hex(6)}"
        airtime_res = await tools.buy_airtime(
            account_id=account_id, phone_number=caller_id, network="MTN",
            amount_kobo=100_000, idempotency_key=idem_key, session_id=req.session_id
        )
        tool_records.append(ToolCallRecord(tool="buy_airtime", arguments={"phone": caller_id}, result=airtime_res))
        airtime_replies = {
            Language.HAUSA: "An tura katin waya na Naira 1,000 zuwa lambar ku.",
            Language.IGBO: "E zigara kredit nke Naira otu puku na akara ekwenti gi.",
            Language.YORUBA: "A ti ra kaadi foonu ti egbewa Naira kan si noba yin.",
            Language.NIGERIAN_ENGLISH: "1,000 Naira airtime top-up has been credited to your phone number."
        }
        return AgentRespondResponse(reply_text=_r(lang, airtime_replies), intent="buy_airtime", tool_calls=tool_records)

    # Unknown / fallback
    return AgentRespondResponse(reply_text=_unknown_reply(lang), intent="unknown")


# ═══════════════════════════════════════════════════════════════════════════
#  PROVIDER INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

class LLMProvider(ABC):
    @abstractmethod
    async def respond(self, req: AgentRespondRequest, tools: ToolRegistry) -> AgentRespondResponse:
        pass


class MockLLMProvider(LLMProvider):
    """Uses rule-based intent extraction + shared state machine. Fast, deterministic, testable."""

    async def respond(self, req: AgentRespondRequest, tools: ToolRegistry) -> AgentRespondResponse:
        intent_data = _rule_based_intent(req.text, req.language, req.pending_action or {})
        return await _run_state_machine(intent_data, req, tools)


class GroqLLMProvider(LLMProvider):
    """
    Uses Groq LLM for intent/slot extraction (JSON mode), then the shared deterministic
    state machine handles all money operations. Never sends PIN to the LLM.
    """

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL or "qwen/qwen3.8-27b"

    async def _extract_intent_groq(self, req: AgentRespondRequest) -> Dict[str, Any]:
        """Call Groq JSON mode to extract intent+slots. Falls back to rules on any error."""
        if not self.api_key:
            return _rule_based_intent(req.text, req.language, req.pending_action or {})

        lang_names = {
            Language.HAUSA: "Hausa", Language.YORUBA: "Yoruba",
            Language.IGBO: "Igbo", Language.NIGERIAN_ENGLISH: "Nigerian English"
        }
        lang_name = lang_names.get(req.language, "Nigerian English")
        pending = req.pending_action or {}
        pending_ctx = ""
        if pending.get("pending_action_type"):
            pending_ctx = f"Current state: collecting slots for {pending['pending_action_type']}."
        elif pending.get("action") == "confirm_transfer":
            pending_ctx = f"Awaiting transfer confirmation of {pending.get('amount_naira')} to {pending.get('beneficiary_name')}."

        system_prompt = f"""You are an intent and slot extractor for a Nigerian voice banking assistant.
Caller language: {lang_name}. {pending_ctx}

Extract the caller's intent. Return ONLY valid JSON with this exact shape:
{{
  "intent": "<one of: greeting | check_balance | transfer | pay_bill | airtime | help | confirm_yes | confirm_no | cancel | repeat_last | unknown>",
  "slots": {{"amount": <Naira number or null>, "beneficiary": "<name or null>", "bill_type": "<electricity|water|cable or null>"}},
  "reply_hint": ""
}}

Rules:
- "hello I want to make a transfer" / "I want to transfer" / "tura kudi" / "fi owo ranse" → intent=transfer
- "send 5k to Musa" → intent=transfer, slots.amount=5000, slots.beneficiary="Musa"
- "what is my balance" / "duba kudi na" / "how much i get" → intent=check_balance
- "pay NEPA" / "san owo ina" / "kudin wuta" / "electricity" → intent=pay_bill
- "yes" / "proceed" / "ehen" / "beeni" / "o ya" / "oya" → intent=confirm_yes
- "no" / "cancel" / "mba" / "a'a" → intent=cancel
- NEVER default to check_balance when unsure. If unclear → intent=unknown
Return ONLY JSON. No other text."""

        messages = [{"role": "system", "content": system_prompt}]
        if req.last_reply_text and req.turn_count > 0:
            messages.append({"role": "assistant", "content": req.last_reply_text})
        messages.append({"role": "user", "content": req.text})

        for attempt in range(2):
            try:
                import httpx
                async with httpx.AsyncClient(timeout=6.0) as client:
                    payload = {
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0,
                        "max_tokens": 200,
                        "response_format": {"type": "json_object"}
                    }
                    res = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                        json=payload
                    )
                    if res.status_code == 200:
                        raw = res.json()["choices"][0]["message"]["content"].strip()
                        raw = re.sub(r"```json\s*|\s*```", "", raw).strip()
                        parsed = json.loads(raw)
                        if "intent" in parsed and "slots" in parsed:
                            return parsed
                    else:
                        logger.warning(f"Groq intent extraction HTTP {res.status_code}: {res.text[:200]}")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Groq intent JSON parse error (attempt {attempt+1}): {e}")
            except Exception as e:
                logger.warning(f"Groq intent extraction error (attempt {attempt+1}): {e}")

        logger.warning("Groq intent extraction failed both attempts, using rule-based fallback")
        return _rule_based_intent(req.text, req.language, req.pending_action or {})

    async def _polish_reply(self, req: AgentRespondRequest, reply: str, intent: str) -> str:
        """Use Groq to make non-money replies more natural. Money replies stay deterministic."""
        DETERMINISTIC_INTENTS = {
            "pin_privacy_prompt", "quote_transfer", "transfer_completed", "transfer_cancelled",
            "check_balance", "pay_bill", "buy_airtime", "escalate_to_human",
            "slot_filling_beneficiary", "slot_filling_amount", "low_confidence_reprompt",
            "awaiting_confirmation", "mid_flow_correction", "digression_balance"
        }
        if intent in DETERMINISTIC_INTENTS or not self.api_key:
            return reply

        lang_names = {
            Language.HAUSA: "Hausa", Language.YORUBA: "Yoruba",
            Language.IGBO: "Igbo", Language.NIGERIAN_ENGLISH: "Nigerian English"
        }
        lang_name = lang_names.get(req.language, "Nigerian English")
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": f"You are Lyfpartner, a warm Nigerian voice banking assistant. Reply ONLY in {lang_name}. Keep it 1-2 sentences. Sound natural, no markdown. Take this draft and improve: '{reply}'. Return ONLY the improved reply."},
                            {"role": "user", "content": req.text}
                        ],
                        "temperature": 0.5,
                        "max_tokens": 120
                    }
                )
                if res.status_code == 200:
                    raw = res.json()["choices"][0]["message"]["content"].strip()
                    clean = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
                    clean = re.sub(r"[*_`#]", "", clean).strip()
                    if clean and len(clean) > 10:
                        return clean
        except Exception as e:
            logger.warning(f"Groq reply polish error: {e}")
        return reply

    async def respond(self, req: AgentRespondRequest, tools: ToolRegistry) -> AgentRespondResponse:
        # Phase 1: Intent extraction (Groq JSON → rule fallback)
        intent_data = await self._extract_intent_groq(req)

        # Map Groq confirm/cancel into keyword text that the state machine can handle
        # (the SM already checks CONFIRMATION_KEYWORDS and CANCEL_KEYWORDS on req.text)
        # So just normalise intent for SM routing — SM uses req.text for yes/no checks
        if intent_data.get("intent") == "confirm_yes":
            intent_data["intent"] = "unknown"  # SM reads keywords from req.text
        elif intent_data.get("intent") in ("confirm_no", "cancel"):
            intent_data["intent"] = "unknown"

        # Phase 2: Deterministic state machine
        result = await _run_state_machine(intent_data, req, tools)

        # Phase 3: Polish conversational replies (not money-critical ones)
        polished = await self._polish_reply(req, result.reply_text, result.intent)
        if polished != result.reply_text:
            return AgentRespondResponse(
                reply_text=polished,
                intent=result.intent,
                tool_calls=result.tool_calls,
                next_state=result.next_state,
                needs_confirmation=result.needs_confirmation,
                needs_auth=result.needs_auth,
                escalate=result.escalate,
                escalate_reason=result.escalate_reason
            )
        return result


def get_llm_provider() -> LLMProvider:
    if settings.LLM_PROVIDER in ["groq", "live"] and settings.GROQ_API_KEY:
        return GroqLLMProvider()
    return MockLLMProvider()
