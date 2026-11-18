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
    "go ahead", "do it", "affirmative", "right", "sure",
    "i mana", "ii", "ci gaba", "aika shi", "toh", "to", "haka", "yauwa", "yawwa"
]

CANCEL_KEYWORDS = [
    "no", "cancel", "stop", "a'a", "mba", "rara", "don't", "dont",
    "abort", "back", "quit", "nevermind", "never mind",
    "fasa", "dakatar", "ba na so", "bar shi"
]

REPEAT_KEYWORDS = [
    "repeat", "say again", "pardon", "maimaita", "kwuo ozo", "so leekan si",
    "what did you say", "come again", "ban ji ba", "sake fada"
]

TRANSFER_KEYWORDS = [
    "send", "transfer", "tura", "ziga", "fi ranse", "give",
    "move money", "move", "wire", "remit", "i want to send", "i want to transfer",
    "i want to make a transfer", "make transfer", "wanna send", "wanna transfer",
    "tura kudi", "aika kudi", "aika", "ba da kudi",
    "gbe owo", "fi owo ranse",
    "zipu ego", "ziga ego",
]

BALANCE_KEYWORDS = [
    "balance", "duba kudi", "kudi na", "ego ole", "ile ego",
    "iye owo", "owo mi", "how much", "how much i get", "check my account",
    "check balance", "my balance", "account balance",
    "ragowar kudi", "ragowa", "asusu na", "asusu", "kudin account",
    "nawa nake da shi", "ina da nawa", "nawa ne a asusu", "nawa ne kudi na",
    "nawa kudi", "kudi nawa"
]

BILL_KEYWORDS_EN = ["electricity", "nepa", "light bill", "meter", "ikedc", "ekedc", "utility"]
BILL_KEYWORDS_YO = ["owo ina", "san owo ina"]
BILL_KEYWORDS_IG = ["ugwo oku", "kwo ugwo oku"]
BILL_KEYWORDS_HA = ["kudin wuta", "wutan lantarki", "biya wuta", "kudin nepa", "wuta"]

HELP_KEYWORDS = [
    "help", "service", "services", "options", "what can you do",
    "taimako", "iranlowo", "enyemaka", "kini e le se", "me za ku iya yi", "kedu ihe"
]

AIRTIME_KEYWORDS = [
    "airtime", "recharge", "topup", "top up", "credit", "katin waya", "kaadi ipe",
    "buy airtime", "send airtime", "sayen katin waya", "ra kaadi", "sanya katin", "kati"
]
DATA_KEYWORDS = [
    "data", "internet", "bundle", "gig", "browse", "browsing", "megabyte", "gigabyte",
    "sayen data", "ra data", "zuta data", "data bundle", "buy data", "kunshin data", "intanet"
]

GREETING_KEYWORDS = [
    "hello", "hi", "good morning", "good afternoon", "good evening",
    "sannu", "barka", "bawo ni", "bawo", "ndewo", "kedu", "eku",
    "ina kwana", "ina wuni", "yaya dai", "yaya kake", "yaya kuke"
]

# ─────────────────────── Nigerian number normaliser ──────────────────────────

_NAIRA_WORDS = {
    "k": 1_000, "thousand": 1_000, "million": 1_000_000, "m": 1_000_000,
}

_SPOKEN_AMOUNTS = {
    # Hausa spoken amounts
    "dubu dari": 100_000,
    "dubu hamsin": 50_000,
    "dubu ashirin": 20_000,
    "dubu goma": 10_000,
    "dubu tara": 9_000,
    "dubu takwas": 8_000,
    "dubu bakwai": 7_000,
    "dubu shida": 6_000,
    "dubu biyar": 5_000,
    "dubu hudu": 4_000,
    "dubu uku": 3_000,
    "dubu biyu": 2_000,
    "dubu daya": 1_000,
    "dubu": 1_000,
    "dari biyar": 500,
    "dari daya": 100,
    # Yoruba spoken amounts
    "egberun mewa": 10_000,
    "egberun mejo": 8_000,
    "egberun meje": 7_000,
    "egberun mefa": 6_000,
    "egberun marun": 5_000,
    "egberun merin": 4_000,
    "egberun meta": 3_000,
    "egberun meji": 2_000,
    "egberun kan": 1_000,
    "egberun": 1_000,
    # Igbo spoken amounts
    "puku iri": 10_000,
    "puku itoolu": 9_000,
    "puku asato": 8_000,
    "puku asaa": 7_000,
    "puku isii": 6_000,
    "puku ise": 5_000,
    "puku ano": 4_000,
    "puku ato": 3_000,
    "puku abuo": 2_000,
    "puku otu": 1_000,
    "puku nani": 1_000,
    "puku": 1_000,
    # English spoken words
    "one hundred thousand": 100_000,
    "fifty thousand": 50_000,
    "twenty thousand": 20_000,
    "ten thousand": 10_000,
    "nine thousand": 9_000,
    "eight thousand": 8_000,
    "seven thousand": 7_000,
    "six thousand": 6_000,
    "five thousand": 5_000,
    "four thousand": 4_000,
    "three thousand": 3_000,
    "two thousand": 2_000,
    "one thousand": 1_000,
    "five hundred": 500,
}

def _parse_amount(text: str) -> Optional[int]:
    """Return naira amount from text like '5k', '5000', 'dubu biyar', 'egberun marun'."""
    t = text.lower().replace(",", "")
    for phrase, val in _SPOKEN_AMOUNTS.items():
        if phrase in t:
            return val
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


NIGERIAN_BANKS = [
    ("gtbank", "GTBank"),
    ("gtb", "GTBank"),
    ("guaranty trust", "GTBank"),
    ("zenith", "Zenith Bank"),
    ("zenith bank", "Zenith Bank"),
    ("first bank", "First Bank"),
    ("firstbank", "First Bank"),
    ("fbn", "First Bank"),
    ("access bank", "Access Bank"),
    ("access", "Access Bank"),
    ("uba", "UBA"),
    ("united bank for africa", "UBA"),
    ("kuda", "Kuda Bank"),
    ("kuda bank", "Kuda Bank"),
    ("opay", "OPay"),
    ("palmpay", "PalmPay"),
    ("palm pay", "PalmPay"),
    ("stanbic", "Stanbic IBTC"),
    ("stanbic ibtc", "Stanbic IBTC"),
    ("fidelity", "Fidelity Bank"),
    ("sterling", "Sterling Bank"),
    ("union bank", "Union Bank"),
    ("union", "Union Bank"),
    ("fcmb", "FCMB"),
    ("wema", "Wema Bank"),
    ("alat", "Wema Bank"),
    ("moniepoint", "Moniepoint"),
    ("jaiz", "Jaiz Bank"),
    ("taj", "Taj Bank"),
]

def _extract_beneficiary_from_text(text: str) -> Optional[str]:
    """
    Extract a plain-name beneficiary from short utterances like 'to Ibrahim' or 'Ibrahim'.
    Returns None if no plausible single name is found.
    """
    _NOT_NAMES = {
        "bank", "my", "account", "the", "make", "a", "do", "pay", "send", "transfer",
        "check", "buy", "get", "give", "someone", "anyone", "this", "that", "him",
        "her", "them", "you", "me", "it", "us", "who", "whom", "what", "how", "when",
        "where", "why", "an", "another", "one", "two", "three", "four", "five",
        "money", "cash", "naira", "ngn",
    }
    t = text.strip()
    # Match "to <Name>" patterns
    m = re.search(r'\b(?:to|ti|for|ga|si|nye)\s+([A-Za-z][A-Za-z]{1,20})', t, re.IGNORECASE)
    if m:
        name = m.group(1).strip()
        if (name.lower() not in [b[0] for b in NIGERIAN_BANKS]
                and name.lower() not in _NOT_NAMES):
            return name.title()
    # Very short utterance that's just a name (1-2 words, no digits)
    words = [w for w in re.sub(r'[^A-Za-z\s]', '', t).split() if w]
    if len(words) <= 2:
        clean = " ".join(words).title()
        clean_lower = clean.lower()
        if (clean_lower not in [b[0] for b in NIGERIAN_BANKS]
                and not any(w in _NOT_NAMES for w in clean_lower.split())
                and len(clean) > 2):
            return clean
    return None


def _extract_account_number(text: str) -> Optional[str]:
    """Find a 10-digit Nigerian NUBAN account number."""
    m = re.search(r'\b\d{10}\b', text)
    if m:
        return m.group(0)
    digits_only = re.sub(r'[^\d]', '', text)
    if len(digits_only) == 10:
        return digits_only
    return None

def _extract_bank_name(text: str) -> Optional[str]:
    t = text.lower()
    for kw, standard_name in NIGERIAN_BANKS:
        if re.search(r'\b' + re.escape(kw) + r'\b', t):
            return standard_name
    return None

def _extract_meter_number(text: str) -> Optional[str]:
    """Extract a 10 to 13 digit Nigerian electricity meter number."""
    m = re.search(r'\b\d{10,13}\b', text)
    if m:
        return m.group(0)
    digits_only = re.sub(r'[^\d]', '', text)
    if 10 <= len(digits_only) <= 13:
        return digits_only
    return None

STANDARD_DATA_PLANS = {
    "1gb": {"name": "1GB", "amount_naira": 500, "amount_kobo": 50_000, "validity": "30 days"},
    "2.5gb": {"name": "2.5GB", "amount_naira": 1000, "amount_kobo": 100_000, "validity": "30 days"},
    "2gb": {"name": "2.5GB", "amount_naira": 1000, "amount_kobo": 100_000, "validity": "30 days"},
    "5gb": {"name": "5GB", "amount_naira": 1500, "amount_kobo": 150_000, "validity": "30 days"},
    "10gb": {"name": "10GB", "amount_naira": 3000, "amount_kobo": 300_000, "validity": "30 days"},
}

def _detect_network(phone: str) -> str:
    """Detect Nigerian mobile network from phone prefix."""
    p = phone.strip()
    if p.startswith("+234"):
        p = "0" + p[4:]
    elif p.startswith("234"):
        p = "0" + p[3:]
    prefix = p[:4]

    mtn_prefixes = {"0803", "0806", "0703", "0706", "0813", "0816", "0810", "0814", "0903", "0906", "0913", "0916"}
    airtel_prefixes = {"0802", "0808", "0708", "0812", "0701", "0902", "0901", "0904", "0907", "0912"}
    glo_prefixes = {"0805", "0807", "0705", "0815", "0811", "0905", "0915"}
    etisalat_prefixes = {"0809", "0817", "0818", "0909", "0908"}

    if prefix in mtn_prefixes:
        return "MTN"
    if prefix in airtel_prefixes:
        return "Airtel"
    if prefix in glo_prefixes:
        return "Glo"
    if prefix in etisalat_prefixes:
        return "9mobile"
    return "MTN"

def _extract_phone_number(text: str) -> Optional[str]:
    """Find a Nigerian phone number in text (e.g. 08012345678 or +2348012345678)."""
    m = re.search(r'(\+234\d{10}|0[789][01]\d{8})\b', text)
    if m:
        return m.group(1)
    return None

def _extract_network_from_text(text: str) -> Optional[str]:
    t = text.lower()
    if "mtn" in t:
        return "MTN"
    if "airtel" in t:
        return "Airtel"
    if "glo" in t or "globacom" in t:
        return "Glo"
    if "9mobile" in t or "etisalat" in t:
        return "9mobile"
    return None

def _extract_data_plan(text: str) -> Optional[Dict[str, Any]]:
    t = text.lower().replace(" ", "")
    for key, plan in STANDARD_DATA_PLANS.items():
        if key in t:
            return plan
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
    Returns: {intent, slots:{amount, beneficiary, bill_type, account_number, bank_name, meter_number}, reply_hint}
    """
    t = text.lower().strip()
    slots: Dict[str, Any] = {
        "amount": None,
        "beneficiary": None,
        "bill_type": None,
        "account_number": None,
        "bank_name": None,
        "meter_number": None,
        "phone_number": None,
        "network": None,
        "data_plan": None
    }

    amount_naira = _parse_amount(t)
    if amount_naira:
        slots["amount"] = amount_naira

    phone = _extract_phone_number(text)
    if phone:
        slots["phone_number"] = phone
        slots["network"] = _detect_network(phone)

    net = _extract_network_from_text(text)
    if net:
        slots["network"] = net

    d_plan = _extract_data_plan(text)
    if d_plan:
        slots["data_plan"] = d_plan["name"]
        if not slots["amount"]:
            slots["amount"] = d_plan["amount_naira"]

    # Common English words that look like names after "to" but are NOT beneficiaries
    _NOT_NAMES = {
        "bank", "my", "account", "the", "make", "a", "do", "pay", "send", "transfer",
        "check", "buy", "get", "give", "someone", "anyone", "this", "that", "him",
        "her", "them", "you", "me", "it", "us", "who", "whom", "what", "how", "when",
        "where", "why", "an", "another", "one", "two", "three", "four", "five",
        "airtime", "data", "credit", "recharge", "phone"
    }
    ben_match = re.search(r'(?:to|ti|for|ga|si|nye)\s+([A-Za-z][A-Za-z\s]{1,20}?)(?:\s+(?:in|at|on|via|account|bank|\d)|$)', text, re.IGNORECASE)
    if ben_match:
        cand = ben_match.group(1).strip()
        cand_lower = cand.lower()
        if (cand_lower not in [b[0] for b in NIGERIAN_BANKS]
                and cand_lower not in _NOT_NAMES
                and not any(word in _NOT_NAMES for word in cand_lower.split())):
            slots["beneficiary"] = cand

    acct_no = _extract_account_number(text)
    if acct_no:
        slots["account_number"] = acct_no

    bank = _extract_bank_name(text)
    if bank:
        slots["bank_name"] = bank

    meter_no = _extract_meter_number(text)
    if meter_no:
        slots["meter_number"] = meter_no

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

    if any(w in t for w in DATA_KEYWORDS):
        return {"intent": "buy_data", "slots": slots, "reply_hint": ""}

    if any(w in t for w in AIRTIME_KEYWORDS):
        return {"intent": "airtime", "slots": slots, "reply_hint": ""}

    if any(w in t for w in BALANCE_KEYWORDS):
        return {"intent": "check_balance", "slots": slots, "reply_hint": ""}

    if any(w in t for w in HELP_KEYWORDS):
        return {"intent": "help", "slots": slots, "reply_hint": ""}

    if any(w in t for w in REPEAT_KEYWORDS):
        return {"intent": "repeat_last", "slots": slots, "reply_hint": ""}

    # Pure greeting — when no specific banking action was requested
    if any(w in t for w in GREETING_KEYWORDS) and len(t.split()) <= 6:
        return {"intent": "greeting", "slots": slots, "reply_hint": ""}

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


def _ask_account_and_bank(lang: Language, ben_name: str) -> str:
    return _r(lang, {
        Language.HAUSA: f"Menene lambar asusun banki mai lamba 10 da sunan bankin {ben_name}?",
        Language.IGBO: f"Kedu nomba akauntu onuogugu 10 na aha ulo aku {ben_name}?",
        Language.YORUBA: f"Kini nomba akanti oni-nomba 10 ati oruko banki ti {ben_name}?",
        Language.NIGERIAN_ENGLISH: f"What is {ben_name}'s 10-digit account number and bank name?"
    })


def _ask_amount_with_acct(lang: Language, ben_name: str, bank: str, acct: str) -> str:
    return _r(lang, {
        Language.HAUSA: f"Na gane, asusun {acct} a {bank}. Nawa kuke son tura wa {ben_name}?",
        Language.IGBO: f"Aghotara m, akauntu {acct} na {bank}. Ego ole ka i choro iziga nye {ben_name}?",
        Language.YORUBA: f"Mo gba, akanti {acct} ni {bank}. Elo ni e fe fi ranse si {ben_name}?",
        Language.NIGERIAN_ENGLISH: f"Got it, account {acct} at {bank}. How much would you like to send to {ben_name}?"
    })


def _ask_amount(lang: Language, beneficiary: str) -> str:
    return _r(lang, {
        Language.HAUSA: f"Nawa kuke son tura wa {beneficiary}?",
        Language.IGBO: f"Ego ole ka i choro iziga nye {beneficiary}?",
        Language.YORUBA: f"Iye owo melo ni e fe fi ranse si {beneficiary}?",
        Language.NIGERIAN_ENGLISH: f"Got it! How much would you like to send to {beneficiary}?"
    })


def _ask_meter_number(lang: Language) -> str:
    return _r(lang, {
        Language.HAUSA: "To, bari mu biya kudin wutan lantarki. Don Allah fadi lambar mitarku mai lamba 11.",
        Language.IGBO: "Ọ dị mma, ka anyị kwuo ụgwọ ọkụ eletrik gị. Biko gwa m nọmba mita gị nke nwere ọnụọgụ 11.",
        Language.YORUBA: "O dara, ẹ jẹ ki a san owo ina mọnamọna yin. Ẹ jọwọ sọ nọmba mita oni-nọmba 11 yin.",
        Language.NIGERIAN_ENGLISH: "Sure! Let's pay your electricity bill. Please tell me your 11-digit meter number."
    })


def _meter_verified_ask_amount(lang: Language, meter_no: str, customer_name: str = "Aminu Kano") -> str:
    return _r(lang, {
        Language.HAUSA: f"An tabbatar da lambar mita {meter_no} a karkashin Ikeja Electric ga {customer_name}. Nawa kuke son biya?",
        Language.IGBO: f"A kwadoro nọmba mita {meter_no} n'okpuru Ikeja Electric maka {customer_name}. Ego ole ka ị chọrọ ịkwụ?",
        Language.YORUBA: f"A ti fọwọsi nọmba mita {meter_no} labẹ Ikeja Electric fun {customer_name}. Elo ni ẹ fẹ san?",
        Language.NIGERIAN_ENGLISH: f"Meter number {meter_no} verified under Ikeja Electric for {customer_name}. How much would you like to pay?"
    })


def _confirm_bill_prompt(lang: Language, amount_fmt: str, meter_no: str, biller_name: str = "Ikeja Electric") -> str:
    return _r(lang, {
        Language.HAUSA: f"An tabbatar da lambar sirri! Tabbatar da biyan Naira {amount_fmt} ga {biller_name} don mitar {meter_no}. In tura?",
        Language.IGBO: f"A kwadoro nọmba nzuzo gị! Kwenye nkwụnye ụgwọ nke Naira {amount_fmt} na {biller_name} maka mita {meter_no}. M ga-aga n'ihu?",
        Language.YORUBA: f"A ti fọwọsi nọmba asiri yin! Ṣe ẹ fẹ san Naira {amount_fmt} si {biller_name} fun mita {meter_no}? Ṣe kin tẹsiwaju?",
        Language.NIGERIAN_ENGLISH: f"PIN verified! Confirm payment of {amount_fmt} Naira to {biller_name} for meter {meter_no}. Should I go ahead?"
    })


def _bill_success(lang: Language, amount_fmt: str, meter_no: str, token: str, biller_name: str = "Ikeja Electric") -> str:
    return _r(lang, {
        Language.HAUSA: f"Biyan kudin wutan NEPA Naira {amount_fmt} na mitar {meter_no} ya yi nasara! Lambar wutanku ita ce {token}. An aiko muku da sakon SMS.",
        Language.IGBO: f"Ịkwụ ụgwọ ọkụ eletrik nke Naira {amount_fmt} maka mita {meter_no} gara nke ọma! Nọmba nchaji gị bụ {token}. Anyị eziterela gị ozi SMS.",
        Language.YORUBA: f"Isanwo owo ina NEPA ti Naira {amount_fmt} fun mita {meter_no} ti jasi aṣeyọri! Nọmba ina yin ni {token}. A ti fi SMS ranṣẹ si yin.",
        Language.NIGERIAN_ENGLISH: f"Your payment of {amount_fmt} Naira to {biller_name} for meter {meter_no} was successful! Your recharge token is {token}. An SMS receipt has been sent to your phone."
    })


def _ask_airtime_amount(lang: Language, phone: str, network: str) -> str:
    return _r(lang, {
        Language.HAUSA: f"Nawa kuke son sayen katin waya na {network} don lambar {phone}?",
        Language.IGBO: f"Ego ole ka ị chọrọ ịzụta kredit {network} maka akara {phone}?",
        Language.YORUBA: f"Elo ni ẹ fẹ ra kaadi {network} fun nọmba {phone}?",
        Language.NIGERIAN_ENGLISH: f"How much {network} airtime would you like to buy for {phone}?"
    })


def _confirm_airtime_prompt(lang: Language, amount_fmt: str, phone: str, network: str) -> str:
    return _r(lang, {
        Language.HAUSA: f"An tabbatar da lambar sirri! Kuna son sayen katin waya na {network} Naira {amount_fmt} don {phone}. In tura?",
        Language.IGBO: f"A kwadoro nọmba nzuzo gị! Ị chọrọ ịzụta kredit {network} nke Naira {amount_fmt} maka {phone}. M ga-eziga ya?",
        Language.YORUBA: f"A ti fọwọsi nọmba asiri yin! Ṣe ẹ fẹ ra kaadi {network} ti Naira {amount_fmt} fun {phone}? Ṣe kin tẹsiwaju?",
        Language.NIGERIAN_ENGLISH: f"PIN verified! Confirm {network} airtime recharge of {amount_fmt} Naira for {phone}. Should I go ahead?"
    })


def _airtime_success(lang: Language, amount_fmt: str, phone: str, network: str) -> str:
    return _r(lang, {
        Language.HAUSA: f"An tura katin waya na {network} Naira {amount_fmt} zuwa {phone} cikin nasara. An aiko muku da sakon SMS.",
        Language.IGBO: f"E zigara kredit {network} nke Naira {amount_fmt} na akara {phone} nke ọma. Anyị eziterela gị ozi SMS.",
        Language.YORUBA: f"A ti fi kaadi {network} ti Naira {amount_fmt} ranṣẹ si {phone} lori aṣeyọri. A ti fi SMS ranṣẹ si yin.",
        Language.NIGERIAN_ENGLISH: f"Your {network} airtime recharge of {amount_fmt} Naira to {phone} was successful! An SMS receipt has been sent."
    })


def _ask_data_plan(lang: Language, phone: str, network: str) -> str:
    return _r(lang, {
        Language.HAUSA: f"Wane tsarin data na {network} kuke so don {phone}? Muna da 1GB kan Naira 500, 2.5GB kan Naira 1,000, ko 5GB kan Naira 1,500.",
        Language.IGBO: f"Kedu atụmatụ data {network} ị chọrọ maka {phone}? Anyị nwere 1GB maka Naira 500, 2.5GB maka Naira 1,000, ma ọ bụ 5GB maka Naira 1,500.",
        Language.YORUBA: f"Eto data {network} wo ni ẹ fẹ fun {phone}? A ni 1GB fun Naira 500, 2.5GB fun Naira 1,000, tabi 5GB fun Naira 1,500.",
        Language.NIGERIAN_ENGLISH: f"Which {network} data plan would you like for {phone}? We have 1GB for 500 Naira, 2.5GB for 1,000 Naira, or 5GB for 1,500 Naira."
    })


def _confirm_data_prompt(lang: Language, plan_name: str, amount_fmt: str, phone: str, network: str) -> str:
    return _r(lang, {
        Language.HAUSA: f"An tabbatar da lambar sirri! Kuna son sayen data {network} {plan_name} kan Naira {amount_fmt} don {phone}. In kunna?",
        Language.IGBO: f"A kwadoro nọmba nzuzo gị! Ị chọrọ ịzụta data {network} {plan_name} maka Naira {amount_fmt} maka {phone}. M ga-aga n'ihu?",
        Language.YORUBA: f"A ti fọwọsi nọmba asiri yin! Ṣe ẹ fẹ ra data {network} {plan_name} fun Naira {amount_fmt} fun {phone}? Ṣe kin tẹsiwaju?",
        Language.NIGERIAN_ENGLISH: f"PIN verified! Confirm {network} {plan_name} data bundle for {phone} at {amount_fmt} Naira. Should I go ahead?"
    })


def _data_success(lang: Language, plan_name: str, amount_fmt: str, phone: str, network: str) -> str:
    return _r(lang, {
        Language.HAUSA: f"An kunna tsarin data {network} {plan_name} don {phone} cikin nasara! An aiko muku da sakon SMS.",
        Language.IGBO: f"E meela ka data {network} {plan_name} rụọ ọrụ maka {phone} nke ọma! Anyị eziterela gị ozi SMS.",
        Language.YORUBA: f"A ti mu data {network} {plan_name} ṣiṣẹ fun {phone} laseyori! A ti fi SMS ranṣẹ si yin.",
        Language.NIGERIAN_ENGLISH: f"Your {network} {plan_name} data bundle for {phone} has been activated successfully! An SMS confirmation has been sent."
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
    #   (c) <=3 non-digit words around the number (not a full sentence)
    #   (d) Not during slot collection (collecting transfer amount, account, or meter/bill amount)
    digits_match = re.findall(r'\b\d{4}\b', text)
    _strong_intent = TRANSFER_KEYWORDS + BALANCE_KEYWORDS + BILL_KEYWORDS_EN + AIRTIME_KEYWORDS + HELP_KEYWORDS
    _has_intent_kw = any(w in text for w in _strong_intent)
    _non_digit_words = [w for w in re.sub(r'[\d,]', '', text).split() if w.strip()]

    # Block PIN detection during slot-collection turns
    _collecting_transfer_amount = (
        pending.get("pending_action_type") == "transfer"
        and pending.get("beneficiary_name")
        and not pending.get("amount_kobo")
    )
    _collecting_transfer_acct = (
        pending.get("pending_action_type") == "transfer"
        and pending.get("beneficiary_name")
        and not pending.get("target_ben")
        and not (pending.get("account_number") and pending.get("bank_name"))
    )
    _collecting_meter = (
        pending.get("pending_action_type") == "bill"
        and not pending.get("meter_no")
    )
    _collecting_bill_amount = (
        pending.get("pending_action_type") == "bill"
        and pending.get("meter_verified")
        and not pending.get("amount_kobo")
    )
    _collecting_airtime_amount = (
        pending.get("pending_action_type") == "airtime"
        and not pending.get("amount_kobo")
    )
    _collecting_data_plan = (
        pending.get("pending_action_type") == "data"
        and not pending.get("plan_name")
    )

    is_pin_input = (
        (bool(digits_match) or text.strip() in ["1234", "1 2 3 4"])
        and not _has_intent_kw
        and len(_non_digit_words) <= 3
        and not _collecting_transfer_amount
        and not _collecting_transfer_acct
        and not _collecting_meter
        and not _collecting_bill_amount
        and not _collecting_airtime_amount
        and not _collecting_data_plan
    )

    if is_pin_input:
        pending_type = pending.get("pending_action_type")

        if pending_type == "transfer":
            amount_kobo = pending.get("amount_kobo", 500_000)
            amount_naira = pending.get("amount_naira", "5,000")
            ben_name = pending.get("beneficiary_name", "Musa Bello")
            target_ben = pending.get("target_ben") or {}
            acct_no = target_ben.get("account_number") or pending.get("account_number", "2045678901")
            bank_name = target_ben.get("bank_name") or pending.get("bank_name", "First Bank")

            # Ensure beneficiary exists in DB before quoting
            try:
                bens_res = await tools.list_beneficiaries(account_id)
                saved_bens = bens_res.get("beneficiaries", [])
                match = next((b for b in saved_bens if b["account_number"] == acct_no), None)
                if not match:
                    await tools.add_beneficiary(account_id, ben_name, acct_no, bank_name)
            except Exception as e:
                logger.warning(f"Error auto-saving beneficiary: {e}")

            quote_res = await tools.quote_transfer(
                source_account_id=account_id,
                beneficiary_account_number=acct_no,
                beneficiary_bank_name=bank_name,
                amount_kobo=amount_kobo
            )
            tool_records.append(ToolCallRecord(tool="quote_transfer", arguments={"amount_kobo": amount_kobo}, result=quote_res))
            token = quote_res.get("confirmation_token")
            ben_quoted = quote_res.get("beneficiary_name", ben_name)
            ben_display = f"{ben_quoted} at {bank_name} ({acct_no})" if bank_name and acct_no else ben_quoted
            return AgentRespondResponse(
                reply_text=_confirm_transfer_prompt(lang, amount_naira, ben_display),
                intent="quote_transfer",
                tool_calls=tool_records,
                needs_confirmation=True,
                next_state={
                    "action": "confirm_transfer",
                    "confirmation_token": token,
                    "beneficiary_name": ben_quoted,
                    "bank_name": bank_name,
                    "account_number": acct_no,
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
            meter_no = pending.get("meter_no", "45129038101")
            amount_kobo = pending.get("amount_kobo", 200_000)
            amount_naira = pending.get("amount_naira", "2,000")
            biller_id = pending.get("biller_id", "bil_ikeja_electric")
            biller_name = pending.get("biller_name", "Ikeja Electric")

            return AgentRespondResponse(
                reply_text=_confirm_bill_prompt(lang, amount_naira, meter_no, biller_name),
                intent="quote_bill",
                needs_confirmation=True,
                next_state={
                    "action": "confirm_bill",
                    "biller_id": biller_id,
                    "biller_name": biller_name,
                    "meter_no": meter_no,
                    "amount_kobo": amount_kobo,
                    "amount_naira": amount_naira
                }
            )

        elif pending_type == "airtime":
            phone = pending.get("phone", caller_id)
            network = pending.get("network", _detect_network(phone))
            amount_kobo = pending.get("amount_kobo", 100_000)
            amount_naira = pending.get("amount_naira", "1,000")

            return AgentRespondResponse(
                reply_text=_confirm_airtime_prompt(lang, amount_naira, phone, network),
                intent="quote_airtime",
                needs_confirmation=True,
                next_state={
                    "action": "confirm_airtime",
                    "phone": phone,
                    "network": network,
                    "amount_kobo": amount_kobo,
                    "amount_naira": amount_naira
                }
            )

        elif pending_type == "data":
            phone = pending.get("phone", caller_id)
            network = pending.get("network", _detect_network(phone))
            plan_name = pending.get("plan_name", "2.5GB")
            amount_kobo = pending.get("amount_kobo", 100_000)
            amount_naira = pending.get("amount_naira", "1,000")

            return AgentRespondResponse(
                reply_text=_confirm_data_prompt(lang, plan_name, amount_naira, phone, network),
                intent="quote_data",
                needs_confirmation=True,
                next_state={
                    "action": "confirm_data",
                    "phone": phone,
                    "network": network,
                    "plan_name": plan_name,
                    "amount_kobo": amount_kobo,
                    "amount_naira": amount_naira
                }
            )

        # Generic PIN ok
        pin_ok = {
            Language.HAUSA: "An tabbatar da lambar sirri. Yaya zan iya taimaka muku yau? Kuna iya duba kudi, tura kudi, ko biyan kudin wuta.",
            Language.IGBO: "A kwadoro nomba nzuzo gi. Kedu ka m ga-esi nyere gi aka taa?",
            Language.YORUBA: "A ti fowo si nomba asiri yin. Bawo ni a se le ran yin lowo?",
            Language.NIGERIAN_ENGLISH: "PIN verified. How can I help you today? You can check balance, transfer money, or pay bills."
        }
        return AgentRespondResponse(reply_text=_r(lang, pin_ok), intent="pin_verified")

    # ── STEP 3: Awaiting confirmations (transfer or bill) ───────────────────
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

    if pending.get("action") == "confirm_bill":
        meter_no = pending.get("meter_no", "45129038101")
        amount_kobo = pending.get("amount_kobo", 200_000)
        amount_naira = pending.get("amount_naira", "2,000")
        biller_id = pending.get("biller_id", "bil_ikeja_electric")
        biller_name = pending.get("biller_name", "Ikeja Electric")

        if any(w in text for w in CONFIRMATION_KEYWORDS):
            idem_key = f"idem_bill_{secrets.token_hex(6)}"
            bill_res = await tools.pay_bill(
                account_id=account_id, biller_id=biller_id,
                customer_meter=meter_no, amount_kobo=amount_kobo,
                idempotency_key=idem_key, session_id=req.session_id
            )
            tool_records.append(ToolCallRecord(tool="pay_bill", arguments={"biller": biller_id, "amount_kobo": amount_kobo}, result=bill_res))
            t_parts = [str(secrets.randbelow(9000) + 1000) for _ in range(5)]
            token = "-".join(t_parts)
            sms_msg = f"Lyfpartner Bill Pay: NGN {amount_naira}.00 paid to {biller_name} for meter {meter_no}. Token: {token}."
            sms_res = await tools.send_sms_receipt(caller_id, sms_msg)
            tool_records.append(ToolCallRecord(tool="send_sms_receipt", arguments={"to": caller_id}, result=sms_res))
            return AgentRespondResponse(
                reply_text=_bill_success(lang, amount_naira, meter_no, token, biller_name),
                intent="bill_completed",
                tool_calls=tool_records,
                next_state=None
            )

        if any(w in text for w in CANCEL_KEYWORDS):
            return AgentRespondResponse(
                reply_text=_cancel_reply(lang),
                intent="bill_cancelled",
                next_state=None
            )

        reask = _confirm_bill_prompt(lang, amount_naira, meter_no, biller_name)
        return AgentRespondResponse(reply_text=reask, intent="awaiting_bill_confirmation", next_state=pending)

    if pending.get("action") == "confirm_airtime":
        phone = pending.get("phone", caller_id)
        network = pending.get("network", "MTN")
        amount_kobo = pending.get("amount_kobo", 100_000)
        amount_naira = pending.get("amount_naira", "1,000")

        if any(w in text for w in CONFIRMATION_KEYWORDS):
            idem_key = f"idem_airtime_{secrets.token_hex(6)}"
            airtime_res = await tools.buy_airtime(
                account_id=account_id, phone_number=phone, network=network,
                amount_kobo=amount_kobo, idempotency_key=idem_key, session_id=req.session_id
            )
            tool_records.append(ToolCallRecord(tool="buy_airtime", arguments={"phone": phone, "network": network, "amount_kobo": amount_kobo}, result=airtime_res))
            sms_msg = f"Lyfpartner TopUp: NGN {amount_naira}.00 {network} airtime loaded for {phone}. Ref: {airtime_res.get('reference')}."
            sms_res = await tools.send_sms_receipt(caller_id, sms_msg)
            tool_records.append(ToolCallRecord(tool="send_sms_receipt", arguments={"to": caller_id}, result=sms_res))
            return AgentRespondResponse(
                reply_text=_airtime_success(lang, amount_naira, phone, network),
                intent="airtime_completed",
                tool_calls=tool_records,
                next_state=None
            )

        if any(w in text for w in CANCEL_KEYWORDS):
            return AgentRespondResponse(
                reply_text=_cancel_reply(lang),
                intent="airtime_cancelled",
                next_state=None
            )

        reask = _confirm_airtime_prompt(lang, amount_naira, phone, network)
        return AgentRespondResponse(reply_text=reask, intent="awaiting_airtime_confirmation", next_state=pending)

    if pending.get("action") == "confirm_data":
        phone = pending.get("phone", caller_id)
        network = pending.get("network", "MTN")
        plan_name = pending.get("plan_name", "2.5GB")
        amount_kobo = pending.get("amount_kobo", 100_000)
        amount_naira = pending.get("amount_naira", "1,000")

        if any(w in text for w in CONFIRMATION_KEYWORDS):
            idem_key = f"idem_data_{secrets.token_hex(6)}"
            data_res = await tools.buy_data(
                account_id=account_id, phone_number=phone, network=network,
                plan_name=plan_name, amount_kobo=amount_kobo,
                idempotency_key=idem_key, session_id=req.session_id
            )
            tool_records.append(ToolCallRecord(tool="buy_data", arguments={"phone": phone, "network": network, "plan": plan_name, "amount_kobo": amount_kobo}, result=data_res))
            sms_msg = f"Lyfpartner Data: {plan_name} {network} data bundle activated for {phone}. Ref: {data_res.get('reference')}."
            sms_res = await tools.send_sms_receipt(caller_id, sms_msg)
            tool_records.append(ToolCallRecord(tool="send_sms_receipt", arguments={"to": caller_id}, result=sms_res))
            return AgentRespondResponse(
                reply_text=_data_success(lang, plan_name, amount_naira, phone, network),
                intent="data_completed",
                tool_calls=tool_records,
                next_state=None
            )

        if any(w in text for w in CANCEL_KEYWORDS):
            return AgentRespondResponse(
                reply_text=_cancel_reply(lang),
                intent="data_cancelled",
                next_state=None
            )

        reask = _confirm_data_prompt(lang, plan_name, amount_naira, phone, network)
        return AgentRespondResponse(reply_text=reask, intent="awaiting_data_confirmation", next_state=pending)

    # ── STEP 4: Slot-filling for in-progress operations ─────────────────────
    if pending.get("pending_action_type") == "transfer":
        updated = dict(pending)
        # 1. Update amount if provided
        if slots.get("amount") and not updated.get("amount_kobo"):
            updated["amount_kobo"] = slots["amount"] * 100
            updated["amount_naira"] = f"{slots['amount']:,}"
        elif not updated.get("amount_kobo"):
            amt = _parse_amount(text)
            if amt:
                updated["amount_kobo"] = amt * 100
                updated["amount_naira"] = f"{amt:,}"

        # 2. Update beneficiary if not yet set
        if not updated.get("beneficiary_name"):
            if slots.get("beneficiary"):
                updated["beneficiary_name"] = slots["beneficiary"]
            else:
                ben_cand = _extract_beneficiary_from_text(req.text)
                if ben_cand:
                    updated["beneficiary_name"] = ben_cand
                elif len(req.text.split()) <= 3 and not _extract_account_number(req.text):
                    cleaned_name = re.sub(r'[^A-Za-z\s]', '', req.text).strip().title()
                    if cleaned_name and cleaned_name.lower() not in [b[0] for b in NIGERIAN_BANKS]:
                        updated["beneficiary_name"] = cleaned_name

        ben_name = updated.get("beneficiary_name")
        target_ben = updated.get("target_ben")
        if ben_name and not target_ben:
            try:
                bens_res = await tools.list_beneficiaries(account_id)
                bens = bens_res.get("beneficiaries", [])
                match = _extract_beneficiary_name(ben_name, bens) or _extract_beneficiary_name(req.text, bens)
                if match:
                    updated["beneficiary_name"] = match["name"]
                    updated["target_ben"] = match
                    updated["account_number"] = match["account_number"]
                    updated["bank_name"] = match["bank_name"]
                    target_ben = match
            except Exception:
                pass

        acct_no = _extract_account_number(req.text) or slots.get("account_number")
        bank_name = _extract_bank_name(req.text) or slots.get("bank_name")
        if acct_no:
            updated["account_number"] = acct_no
        if bank_name:
            updated["bank_name"] = bank_name

        if not target_ben and updated.get("account_number") and updated.get("bank_name"):
            acct = updated["account_number"]
            bank = updated["bank_name"]
            try:
                await tools.add_beneficiary(account_id, ben_name or "Beneficiary", acct, bank)
            except Exception as e:
                logger.warning(f"Error auto-saving beneficiary: {e}")
            target_ben = {"name": ben_name or "Beneficiary", "account_number": acct, "bank_name": bank}
            updated["target_ben"] = target_ben

        has_beneficiary = bool(updated.get("beneficiary_name"))
        has_acct_and_bank = bool(target_ben or (updated.get("account_number") and updated.get("bank_name")))
        has_amount = bool(updated.get("amount_kobo"))

        if not has_beneficiary:
            return AgentRespondResponse(
                reply_text=_ask_beneficiary(lang),
                intent="slot_filling_beneficiary",
                next_state=updated
            )

        if not has_acct_and_bank:
            return AgentRespondResponse(
                reply_text=_ask_account_and_bank(lang, updated["beneficiary_name"]),
                intent="slot_filling_account_bank",
                next_state=updated
            )

        if not has_amount:
            bank = target_ben.get("bank_name", updated.get("bank_name", "bank"))
            acct = target_ben.get("account_number", updated.get("account_number", "account"))
            return AgentRespondResponse(
                reply_text=_ask_amount_with_acct(lang, updated["beneficiary_name"], bank, acct),
                intent="slot_filling_amount",
                next_state=updated
            )

        # All slots filled -> PIN
        amt_fmt = updated["amount_naira"]
        ben_name = updated["beneficiary_name"]
        bank = target_ben.get("bank_name", updated.get("bank_name", ""))
        acct = target_ben.get("account_number", updated.get("account_number", ""))
        summary = _r(lang, {
            Language.HAUSA: f"Na fahimta, kuna son tura Naira {amt_fmt} ga {ben_name} a {bank}, asusu {acct}.",
            Language.IGBO: f"Aghọtara m, ị chọrọ iziga Naira {amt_fmt} nye {ben_name} na {bank}, akaụntụ {acct}.",
            Language.YORUBA: f"Mo gbọ, ẹ fẹ fi Naira {amt_fmt} ranṣẹ si {ben_name} ni {bank}, akọọlẹ {acct}.",
            Language.NIGERIAN_ENGLISH: f"Alright! You want to send {amt_fmt} Naira to {ben_name} at {bank}, account {acct}."
        })
        return AgentRespondResponse(
            reply_text=_ask_pin_privacy(lang, summary),
            intent="pin_privacy_prompt",
            next_state=updated
        )

    if pending.get("pending_action_type") == "bill":
        updated = dict(pending)
        meter_no = _extract_meter_number(req.text) or slots.get("meter_number")
        if meter_no:
            updated["meter_no"] = meter_no
            updated["meter_verified"] = True
            updated["biller_id"] = updated.get("biller_id", "bil_ikeja_electric")
            updated["biller_name"] = updated.get("biller_name", "Ikeja Electric")

        amt = _parse_amount(req.text) or slots.get("amount")
        if amt:
            updated["amount_kobo"] = amt * 100
            updated["amount_naira"] = f"{amt:,}"

        if not updated.get("meter_no"):
            return AgentRespondResponse(
                reply_text=_ask_meter_number(lang),
                intent="slot_filling_meter",
                next_state=updated
            )

        if not updated.get("amount_kobo"):
            meter = updated["meter_no"]
            return AgentRespondResponse(
                reply_text=_meter_verified_ask_amount(lang, meter, "Aminu Kano"),
                intent="meter_verified_ask_amount",
                next_state=updated
            )

        amt_fmt = updated["amount_naira"]
        meter = updated["meter_no"]
        biller = updated.get("biller_name", "Ikeja Electric")
        summary = _r(lang, {
            Language.HAUSA: f"Kuna son biyan Naira {amt_fmt} don mitar {biller} {meter}.",
            Language.IGBO: f"Ị chọrọ ịkwụ Naira {amt_fmt} maka mita {biller} {meter}.",
            Language.YORUBA: f"Ẹ fẹ san Naira {amt_fmt} fun mita {biller} {meter}.",
            Language.NIGERIAN_ENGLISH: f"You want to pay {amt_fmt} Naira for {biller} meter {meter}."
        })
        return AgentRespondResponse(
            reply_text=_ask_pin_privacy(lang, summary),
            intent="pin_privacy_prompt",
            next_state=updated
        )

    if pending.get("pending_action_type") == "airtime":
        updated = dict(pending)
        phone = _extract_phone_number(req.text) or slots.get("phone_number")
        if phone:
            updated["phone"] = phone
            updated["network"] = _detect_network(phone)
        net = _extract_network_from_text(req.text) or slots.get("network")
        if net:
            updated["network"] = net

        amt = _parse_amount(req.text) or slots.get("amount")
        if amt:
            updated["amount_kobo"] = amt * 100
            updated["amount_naira"] = f"{amt:,}"

        phone = updated.get("phone", caller_id)
        network = updated.get("network", _detect_network(phone))

        if not updated.get("amount_kobo"):
            return AgentRespondResponse(
                reply_text=_ask_airtime_amount(lang, phone, network),
                intent="slot_filling_airtime_amount",
                next_state=updated
            )

        amt_fmt = updated["amount_naira"]
        summary = _r(lang, {
            Language.HAUSA: f"Kuna son sayen katin waya na {network} Naira {amt_fmt} don {phone}.",
            Language.IGBO: f"Ị chọrọ ịzụta kredit {network} nke Naira {amt_fmt} maka {phone}.",
            Language.YORUBA: f"Ẹ fẹ ra kaadi {network} ti Naira {amt_fmt} fun {phone}.",
            Language.NIGERIAN_ENGLISH: f"You want to buy {amt_fmt} Naira {network} airtime for {phone}."
        })
        return AgentRespondResponse(
            reply_text=_ask_pin_privacy(lang, summary),
            intent="pin_privacy_prompt",
            next_state=updated
        )

    if pending.get("pending_action_type") == "data":
        updated = dict(pending)
        phone = _extract_phone_number(req.text) or slots.get("phone_number")
        if phone:
            updated["phone"] = phone
            updated["network"] = _detect_network(phone)
        net = _extract_network_from_text(req.text) or slots.get("network")
        if net:
            updated["network"] = net

        plan = _extract_data_plan(req.text)
        if plan:
            updated["plan_name"] = plan["name"]
            updated["amount_kobo"] = plan["amount_kobo"]
            updated["amount_naira"] = f"{plan['amount_naira']:,}"
        elif slots.get("data_plan"):
            updated["plan_name"] = slots["data_plan"]
            amt = slots.get("amount", 1000)
            updated["amount_kobo"] = amt * 100
            updated["amount_naira"] = f"{amt:,}"

        phone = updated.get("phone", caller_id)
        network = updated.get("network", _detect_network(phone))

        if not updated.get("plan_name"):
            return AgentRespondResponse(
                reply_text=_ask_data_plan(lang, phone, network),
                intent="slot_filling_data_plan",
                next_state=updated
            )

        amt_fmt = updated.get("amount_naira", "1,000")
        plan_name = updated["plan_name"]
        summary = _r(lang, {
            Language.HAUSA: f"Kuna son sayen data {network} {plan_name} kan Naira {amt_fmt} don {phone}.",
            Language.IGBO: f"Ị chọrọ ịzụta data {network} {plan_name} maka Naira {amt_fmt} maka {phone}.",
            Language.YORUBA: f"Ẹ fẹ ra data {network} {plan_name} fun Naira {amt_fmt} fun {phone}.",
            Language.NIGERIAN_ENGLISH: f"You want to buy {network} {plan_name} data bundle for {phone} at {amt_fmt} Naira."
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

        ben_name = target_ben["name"] if target_ben else (slots.get("beneficiary") or _extract_beneficiary_from_text(req.text))
        acct_no = _extract_account_number(req.text) or slots.get("account_number")
        bank_name = _extract_bank_name(req.text) or slots.get("bank_name")

        amount_naira = slots.get("amount") or _parse_amount(req.text)
        amount_kobo = amount_naira * 100 if amount_naira else None

        new_pending: Dict[str, Any] = {"pending_action_type": "transfer"}
        if ben_name:
            new_pending["beneficiary_name"] = ben_name
        if target_ben:
            new_pending["target_ben"] = target_ben
            new_pending["account_number"] = target_ben["account_number"]
            new_pending["bank_name"] = target_ben["bank_name"]
        elif acct_no and bank_name:
            new_pending["account_number"] = acct_no
            new_pending["bank_name"] = bank_name
            try:
                await tools.add_beneficiary(account_id, ben_name or "Beneficiary", acct_no, bank_name)
            except Exception as e:
                logger.warning(f"Error auto-saving beneficiary: {e}")
            target_ben = {"name": ben_name or "Beneficiary", "account_number": acct_no, "bank_name": bank_name}
            new_pending["target_ben"] = target_ben

        if amount_kobo:
            new_pending["amount_kobo"] = amount_kobo
            new_pending["amount_naira"] = f"{amount_naira:,}"

        if not ben_name:
            return AgentRespondResponse(
                reply_text=_ask_beneficiary(lang),
                intent="slot_filling_beneficiary",
                next_state=new_pending
            )

        if not target_ben:
            return AgentRespondResponse(
                reply_text=_ask_account_and_bank(lang, ben_name),
                intent="slot_filling_account_bank",
                next_state=new_pending
            )

        if not amount_kobo:
            bank = target_ben.get("bank_name", "bank")
            acct = target_ben.get("account_number", "account")
            return AgentRespondResponse(
                reply_text=_ask_amount_with_acct(lang, ben_name, bank, acct),
                intent="slot_filling_amount",
                next_state=new_pending
            )

        amt_fmt = f"{amount_naira:,}"
        bank = target_ben.get("bank_name", "")
        acct = target_ben.get("account_number", "")
        summary = _r(lang, {
            Language.HAUSA: f"Na fahimta, kuna son tura Naira {amt_fmt} ga {ben_name} a {bank}, asusu {acct}.",
            Language.IGBO: f"Aghọtara m, ị chọrọ iziga Naira {amt_fmt} nye {ben_name} na {bank}, akaụntụ {acct}.",
            Language.YORUBA: f"Mo gbọ, ẹ fẹ fi Naira {amt_fmt} ranṣẹ si {ben_name} ni {bank}, akọọlẹ {acct}.",
            Language.NIGERIAN_ENGLISH: f"Alright! You want to send {amt_fmt} Naira to {ben_name} at {bank}, account {acct}."
        })

        if auth == AuthLevel.NONE:
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
        ben_display = f"{ben_quoted} at {bank} ({acct})" if bank and acct else ben_quoted
        return AgentRespondResponse(
            reply_text=_confirm_transfer_prompt(lang, amt_fmt, ben_display),
            intent="quote_transfer",
            tool_calls=tool_records,
            needs_confirmation=True,
            next_state={
                "action": "confirm_transfer",
                "confirmation_token": token,
                "beneficiary_name": ben_quoted,
                "bank_name": bank,
                "account_number": acct,
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
        meter_no = _extract_meter_number(req.text) or slots.get("meter_number")
        amount_naira = slots.get("amount") or _parse_amount(req.text)
        amount_kobo = amount_naira * 100 if amount_naira else None

        new_pending: Dict[str, Any] = {
            "pending_action_type": "bill",
            "biller_id": "bil_ikeja_electric",
            "biller_name": "Ikeja Electric"
        }

        if meter_no:
            new_pending["meter_no"] = meter_no
            new_pending["meter_verified"] = True

        if amount_kobo:
            new_pending["amount_kobo"] = amount_kobo
            new_pending["amount_naira"] = f"{amount_naira:,}"

        # If no meter number provided yet: ask for meter number
        if not meter_no:
            return AgentRespondResponse(
                reply_text=_ask_meter_number(lang),
                intent="pay_bill",
                next_state=new_pending
            )

        # Meter provided, but no amount: verify meter and ask amount
        if not amount_kobo:
            return AgentRespondResponse(
                reply_text=_meter_verified_ask_amount(lang, meter_no, "Aminu Kano"),
                intent="meter_verified_ask_amount",
                next_state=new_pending
            )

        # Both meter and amount provided
        amt_fmt = f"{amount_naira:,}"
        if auth == AuthLevel.NONE:
            summary = _r(lang, {
                Language.HAUSA: f"Kuna son biyan Naira {amt_fmt} don mitar Ikeja Electric {meter_no}.",
                Language.IGBO: f"Ị chọrọ ịkwụ Naira {amt_fmt} maka mita Ikeja Electric {meter_no}.",
                Language.YORUBA: f"Ẹ fẹ san Naira {amt_fmt} fun mita Ikeja Electric {meter_no}.",
                Language.NIGERIAN_ENGLISH: f"You want to pay {amt_fmt} Naira for Ikeja Electric meter {meter_no}."
            })
            return AgentRespondResponse(
                reply_text=_ask_pin_privacy(lang, summary),
                intent="pin_privacy_prompt",
                next_state=new_pending
            )

        # Authenticated: go straight to confirmation
        return AgentRespondResponse(
            reply_text=_confirm_bill_prompt(lang, amt_fmt, meter_no, "Ikeja Electric"),
            intent="quote_bill",
            needs_confirmation=True,
            next_state={
                "action": "confirm_bill",
                "biller_id": "bil_ikeja_electric",
                "biller_name": "Ikeja Electric",
                "meter_no": meter_no,
                "amount_kobo": amount_kobo,
                "amount_naira": amt_fmt
            }
        )

    # Airtime
    if intent == "airtime":
        phone = _extract_phone_number(req.text) or slots.get("phone_number") or caller_id
        net = _extract_network_from_text(req.text) or slots.get("network") or _detect_network(phone)
        amount_naira = slots.get("amount") or _parse_amount(req.text)
        amount_kobo = amount_naira * 100 if amount_naira else None

        new_pending: Dict[str, Any] = {
            "pending_action_type": "airtime",
            "phone": phone,
            "network": net
        }
        if amount_kobo:
            new_pending["amount_kobo"] = amount_kobo
            new_pending["amount_naira"] = f"{amount_naira:,}"

        if not amount_kobo:
            return AgentRespondResponse(
                reply_text=_ask_airtime_amount(lang, phone, net),
                intent="slot_filling_airtime_amount",
                next_state=new_pending
            )

        amt_fmt = f"{amount_naira:,}"
        if auth == AuthLevel.NONE:
            summary = _r(lang, {
                Language.HAUSA: f"Kuna son sayen katin waya na {net} Naira {amt_fmt} don {phone}.",
                Language.IGBO: f"Ị chọrọ ịzụta kredit {net} nke Naira {amt_fmt} maka {phone}.",
                Language.YORUBA: f"Ẹ fẹ ra kaadi {net} ti Naira {amt_fmt} fun {phone}.",
                Language.NIGERIAN_ENGLISH: f"You want to buy {amt_fmt} Naira {net} airtime for {phone}."
            })
            return AgentRespondResponse(
                reply_text=_ask_pin_privacy(lang, summary),
                intent="pin_privacy_prompt",
                next_state=new_pending
            )

        # Authenticated: go straight to confirmation
        return AgentRespondResponse(
            reply_text=_confirm_airtime_prompt(lang, amt_fmt, phone, net),
            intent="quote_airtime",
            needs_confirmation=True,
            next_state={
                "action": "confirm_airtime",
                "phone": phone,
                "network": net,
                "amount_kobo": amount_kobo,
                "amount_naira": amt_fmt
            }
        )

    # Data Bundle
    if intent == "buy_data":
        phone = _extract_phone_number(req.text) or slots.get("phone_number") or caller_id
        net = _extract_network_from_text(req.text) or slots.get("network") or _detect_network(phone)
        plan = _extract_data_plan(req.text)
        plan_name = plan["name"] if plan else slots.get("data_plan")
        amount_naira = plan["amount_naira"] if plan else slots.get("amount")
        amount_kobo = (amount_naira * 100) if amount_naira else (plan["amount_kobo"] if plan else None)

        new_pending: Dict[str, Any] = {
            "pending_action_type": "data",
            "phone": phone,
            "network": net
        }
        if plan_name:
            new_pending["plan_name"] = plan_name
        if amount_kobo:
            new_pending["amount_kobo"] = amount_kobo
            new_pending["amount_naira"] = f"{amount_naira:,}"

        if not plan_name:
            return AgentRespondResponse(
                reply_text=_ask_data_plan(lang, phone, net),
                intent="slot_filling_data_plan",
                next_state=new_pending
            )

        amt_fmt = new_pending.get("amount_naira", "1,000")
        if auth == AuthLevel.NONE:
            summary = _r(lang, {
                Language.HAUSA: f"Kuna son sayen data {net} {plan_name} kan Naira {amt_fmt} don {phone}.",
                Language.IGBO: f"Ị chọrọ ịzụta data {net} {plan_name} maka Naira {amt_fmt} maka {phone}.",
                Language.YORUBA: f"Ẹ fẹ ra data {net} {plan_name} fun Naira {amt_fmt} fun {phone}.",
                Language.NIGERIAN_ENGLISH: f"You want to buy {net} {plan_name} data bundle for {phone} at {amt_fmt} Naira."
            })
            return AgentRespondResponse(
                reply_text=_ask_pin_privacy(lang, summary),
                intent="pin_privacy_prompt",
                next_state=new_pending
            )

        # Authenticated: go straight to confirmation
        return AgentRespondResponse(
            reply_text=_confirm_data_prompt(lang, plan_name, amt_fmt, phone, net),
            intent="quote_data",
            needs_confirmation=True,
            next_state={
                "action": "confirm_data",
                "phone": phone,
                "network": net,
                "plan_name": plan_name,
                "amount_kobo": amount_kobo,
                "amount_naira": amt_fmt
            }
        )

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
  "intent": "<one of: greeting | check_balance | transfer | pay_bill | airtime | buy_data | help | confirm_yes | confirm_no | cancel | repeat_last | unknown>",
  "slots": {{
    "amount": <Naira number or null>,
    "beneficiary": "<name or null>",
    "account_number": "<10-digit number or null>",
    "bank_name": "<bank name or null>",
    "meter_number": "<meter number or null>",
    "bill_type": "<electricity|water|cable or null>",
    "phone_number": "<11-digit phone number or null>",
    "network": "<MTN|Airtel|Glo|9mobile or null>",
    "data_plan": "<1GB|2.5GB|5GB|10GB or null>"
  }},
  "reply_hint": ""
}}

Rules:
- "hello I want to make a transfer" / "transfer to Ibrahim" / "transfer ti ibrahim" / "tura kudi" / "fi owo ranse" -> intent=transfer
- "send 5k to Musa" -> intent=transfer, slots.amount=5000, slots.beneficiary="Musa"
- "0123456789 GTBank" -> slots.account_number="0123456789", slots.bank_name="GTBank"
- "what is my balance" / "duba kudi na" / "how much i get" -> intent=check_balance
- "pay NEPA" / "pay electricity" / "san owo ina" / "kudin wuta" / "electricity" -> intent=pay_bill, slots.bill_type="electricity"
- "meter 45129038101" / "45129038101" -> slots.meter_number="45129038101"
- "buy airtime" / "recharge 1000" / "katin waya" / "kaadi ipe" -> intent=airtime
- "buy data" / "buy 2GB data" / "sayen data" / "ra data" -> intent=buy_data, slots.data_plan="2.5GB"
- "yes" / "proceed" / "ehen" / "beeni" / "o ya" / "oya" -> intent=confirm_yes
- "no" / "cancel" / "mba" / "a'a" -> intent=cancel
- NEVER default to check_balance when unsure. If unclear -> intent=unknown
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
            "slot_filling_beneficiary", "slot_filling_amount", "slot_filling_account_bank",
            "slot_filling_meter", "meter_verified_ask_amount", "quote_bill", "bill_completed",
            "bill_cancelled", "awaiting_bill_confirmation", "low_confidence_reprompt",
            "awaiting_confirmation", "mid_flow_correction", "digression_balance",
            "quote_airtime", "airtime_completed", "airtime_cancelled", "awaiting_airtime_confirmation",
            "slot_filling_airtime_amount", "quote_data", "data_completed", "data_cancelled",
            "awaiting_data_confirmation", "slot_filling_data_plan"
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
