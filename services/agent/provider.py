"""LLM Dialogue Provider interface and Multi-lingual Mock / Adapter implementations."""
import re
import secrets
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from shared.config import settings
from shared.schemas import (
    Language, AuthLevel, AgentRespondRequest, AgentRespondResponse, ToolCallRecord
)
from services.agent.tools import ToolRegistry

DISTRESS_KEYWORDS = [
    "person", "human", "agent", "angry", "fraud", "scam", "thief", "police",
    "stolen", "operator", "talk to human", "speak to someone", "customer care",
    "mutum", "dan adam", "onye", "eniyan", "daadaa"
]

CONFIRMATION_KEYWORDS = [
    "yes", "confirm", "proceed", "send it", "pay it", "okay", "ok", "correct",
    "eh", "ehen", "bee ne", "haka ne", "ee", "e-e", "beeni", "o ya", "oya"
]

REVISION_KEYWORDS = [
    "no", "cancel", "stop", "a'a", "mba", "rara", "don't"
]

REPEAT_KEYWORDS = [
    "repeat", "say again", "pardon", "maimaita", "kwuo ozo", "so leekan si", "what did you say"
]

class LLMProvider(ABC):
    @abstractmethod
    async def respond(self, req: AgentRespondRequest, tools: ToolRegistry) -> AgentRespondResponse:
        pass

class MockLLMProvider(LLMProvider):
    async def respond(self, req: AgentRespondRequest, tools: ToolRegistry) -> AgentRespondResponse:
        text = req.text.lower().strip()
        lang = req.language
        account_id = req.account_id or "acc_aminu_001"
        caller_id = req.caller_id or "+2348000000001"
        pending = req.pending_action or {}
        tool_records: List[ToolCallRecord] = []

        # 1. Rule: Low ASR confidence -> politely ask caller to repeat
        if req.is_low_confidence:
            reask_phrases = {
                Language.HAUSA: "Ban ji ku da kyau ba. Don Allah ku sake magana.",
                Language.IGBO: "Anughi m gi nke oma. Biko kwuo ozo.",
                Language.YORUBA: "Ejo, mi o gbo yin daadaa. E jowo tun so.",
                Language.NIGERIAN_ENGLISH: "I didn't quite catch that. Please could you repeat what you said?"
            }
            return AgentRespondResponse(
                reply_text=reask_phrases.get(lang, reask_phrases[Language.NIGERIAN_ENGLISH]),
                intent="low_confidence_reprompt",
                next_state=pending
            )

        # 2. Rule: Repeat last utterance shortcut
        if any(w in text for w in REPEAT_KEYWORDS):
            repeat_replies = {
                Language.HAUSA: "Ina nan don taimaka muku da duba kudi, tura kudi, ko biyan kudi.",
                Language.IGBO: "Anom ebe a iji nyere gi aka ile ego gi, iziga ego, ma obu kwuo ugwo.",
                Language.YORUBA: "Mo wa nibi lati ran yin lowo lati wo iye owo yin, gbe owo, tabi san owo.",
                Language.NIGERIAN_ENGLISH: "I am here to help you check your balance, send money, or pay bills. How can I help you today?"
            }
            return AgentRespondResponse(
                reply_text=repeat_replies.get(lang, repeat_replies[Language.NIGERIAN_ENGLISH]),
                intent="repeat_last"
            )

        # 2b. Rule: PIN Verification or PIN Inquiry Request
        if any(w in text for w in ["pin", "password", "secret number", "lambar sirri", "nomba asiri", "nomba nzuzo"]) and not re.search(r'\b\d{4}\b', text):
            pin_inquiry_replies = {
                Language.HAUSA: "Don tsaronka, da fatan kana wuri mai natsuwa da sirri ba a cikin jama'a ba. Za ka iya danna lambar sirrinka ta PIN a kan keypad ko kuma ka fadi ta a fili.",
                Language.IGBO: "Maka nchekwa gi, anyi nwere olileanya na ino n'ebe zoro ezo nwere nchekwa. Biko pia nomba nzuzo PIN gi na keypad ma obu kwuo ya n'olu.",
                Language.YORUBA: "Fun aabo re, a lero pe o wa ni aye ikoko ti o ni aabo. Jowo te nomba asiri PIN re lori keypad tabi ki o so o jade.",
                Language.NIGERIAN_ENGLISH: "For your security, hope you are in a private space and have your privacy. Please punch in your 4-digit PIN on the keypad, or say it out loud."
            }
            return AgentRespondResponse(
                reply_text=pin_inquiry_replies.get(lang, pin_inquiry_replies[Language.NIGERIAN_ENGLISH]),
                intent="pin_privacy_prompt"
            )

        # 2c. Rule: 4-digit PIN submitted
        digits_match = re.findall(r'\b\d{4}\b', text)
        if digits_match or text.strip() in ["1234", "1 2 3 4"]:
            pin_success_replies = {
                Language.HAUSA: "An tabbatar da lambar sirri cikin nasara. Yaya zan iya taimaka muku yau?",
                Language.IGBO: "A kwadoro nomba nzuzo gi nke oma. Kedu ka m ga-esi nyere gi aka taa?",
                Language.YORUBA: "A ti fowo si nomba asiri yin laseyori. Bawo ni a se le ran yin lowo loni?",
                Language.NIGERIAN_ENGLISH: "PIN verified successfully. How can I help you today?"
            }
            return AgentRespondResponse(
                reply_text=pin_success_replies.get(lang, pin_success_replies[Language.NIGERIAN_ENGLISH]),
                intent="pin_verified"
            )

        # 3. Rule: Distress words or explicit request for human -> escalate
        if any(w in text for w in DISTRESS_KEYWORDS):
            res = await tools.escalate_to_human(req.session_id, reason="Caller distress or human agent requested", summary=text)
            tool_records.append(ToolCallRecord(tool="escalate_to_human", arguments={"session_id": req.session_id, "reason": "distress"}, result=res))
            
            escalate_replies = {
                Language.HAUSA: "Na fahimta. Ina mika ku ga wakilin mu yanzu. Don Allah ku dakata.",
                Language.IGBO: "Aghotara m. Ana m ebufe gi na aka onye oru anyi ugbua. Biko chere obere.",
                Language.YORUBA: "Mo gbo yin ye. Mo n gbe yin lo si odo osise wa bayi. E jowo duro die.",
                Language.NIGERIAN_ENGLISH: "I understand. I am transferring you to a human customer care representative now. Please hold on."
            }
            return AgentRespondResponse(
                reply_text=escalate_replies.get(lang, escalate_replies[Language.NIGERIAN_ENGLISH]),
                intent="escalate_to_human",
                tool_calls=tool_records,
                escalate=True,
                escalate_reason="Caller requested human agent"
            )

        # 4. Check if pending confirmation is active (e.g. transfer confirmation)
        if pending.get("action") == "confirm_transfer":
            token = pending.get("confirmation_token")
            beneficiary_name = pending.get("beneficiary_name", "the recipient")
            amount_naira = pending.get("amount_naira", "5,000")

            if any(w in text for w in CONFIRMATION_KEYWORDS):
                # User confirmed! Execute transfer
                idem_key = f"idem_tx_{secrets.token_hex(8)}"
                tx_res = await tools.confirm_transfer(token, idem_key, session_id=req.session_id)
                tool_records.append(ToolCallRecord(tool="confirm_transfer", arguments={"token": token}, result=tx_res))

                # Send SMS receipt
                sms_msg = f"Lyfpartner Debit: NGN {amount_naira}.00 to {beneficiary_name}. Ref: {tx_res.get('reference')}. Bal: NGN {tx_res.get('balance_after_kobo', 0)//100:,}.00"
                sms_res = await tools.send_sms_receipt(caller_id, sms_msg)
                tool_records.append(ToolCallRecord(tool="send_sms_receipt", arguments={"to": caller_id}, result=sms_res))

                confirm_replies = {
                    Language.HAUSA: f"An tura Naira {amount_naira} ga {beneficiary_name} cikin nasara. An aiko muku da sakon SMS.",
                    Language.IGBO: f"E zigara Naira {amount_naira} nye {beneficiary_name} nke oma. Anyi ziterela gi ozi SMS.",
                    Language.YORUBA: f"A ti fi Naira {amount_naira} ranse si {beneficiary_name} laseyori. A ti fi SMS ranse si yin.",
                    Language.NIGERIAN_ENGLISH: f"Your transfer of {amount_naira} Naira to {beneficiary_name} is successful. An SMS receipt has been sent."
                }
                return AgentRespondResponse(
                    reply_text=confirm_replies.get(lang, confirm_replies[Language.NIGERIAN_ENGLISH]),
                    intent="transfer_completed",
                    tool_calls=tool_records,
                    next_state=None
                )
            elif any(w in text for w in REVISION_KEYWORDS):
                cancel_replies = {
                    Language.HAUSA: "An soke wannan aikin. Me kuma kuke son yi?",
                    Language.IGBO: "A kagbuola ya. Gini ozo ka m ga-emere gi?",
                    Language.YORUBA: "A ti fagile e. Kini nkan miiran ti e fe se?",
                    Language.NIGERIAN_ENGLISH: "The transfer has been cancelled. What else can I help you with?"
                }
                return AgentRespondResponse(
                    reply_text=cancel_replies.get(lang, cancel_replies[Language.NIGERIAN_ENGLISH]),
                    intent="transfer_cancelled",
                    next_state=None
                )

        # 5. Intent: Money Transfer (e.g. "Send 5,000 naira to Musa")
        if any(w in text for w in ["send", "transfer", "tura", "ziga", "fi ranse", "give"]):
            amount_kobo = 500_000 # default 5,000 NGN
            amount_naira = 5000
            match_num = re.findall(r'\d+', text.replace(",", ""))
            if match_num:
                parsed_val = int(match_num[0])
                if parsed_val < 100_000:
                    amount_naira = parsed_val
                    amount_kobo = parsed_val * 100

            bens_res = await tools.list_beneficiaries(account_id)
            tool_records.append(ToolCallRecord(tool="list_beneficiaries", arguments={"account_id": account_id}, result=bens_res))
            
            bens = bens_res.get("beneficiaries", [])
            target_ben = bens[0] if bens else None
            for b in bens:
                b_name = b["name"].lower()
                b_nick = (b.get("nickname") or "").lower()
                if b_nick and b_nick in text:
                    target_ben = b
                    break
                if b_name.split()[0] in text:
                    target_ben = b
                    break

            if not target_ben:
                target_ben = {
                    "name": "Musa Bello",
                    "account_number": "2045678901",
                    "bank_name": "First Bank"
                }

            quote_res = await tools.quote_transfer(
                source_account_id=account_id,
                beneficiary_account_number=target_ben["account_number"],
                beneficiary_bank_name=target_ben["bank_name"],
                amount_kobo=amount_kobo
            )
            tool_records.append(ToolCallRecord(tool="quote_transfer", arguments={"amount_kobo": amount_kobo}, result=quote_res))

            token = quote_res.get("confirmation_token")
            ben_name = quote_res.get("beneficiary_name", target_ben["name"])
            amt_fmt = f"{amount_naira:,}"

            ask_confirm_replies = {
                Language.HAUSA: f"Kuna son tura Naira {amt_fmt} ga {ben_name}. In tura?",
                Language.IGBO: f"I choro iziga Naira {amt_fmt} nye {ben_name}. M ga-eziga ya?",
                Language.YORUBA: f"Se e fe fi Naira {amt_fmt} ranse si {ben_name}? Se kin tesiwaju?",
                Language.NIGERIAN_ENGLISH: f"You want to transfer {amt_fmt} Naira to {ben_name}. Should I proceed with this transfer?"
            }

            return AgentRespondResponse(
                reply_text=ask_confirm_replies.get(lang, ask_confirm_replies[Language.NIGERIAN_ENGLISH]),
                intent="quote_transfer",
                tool_calls=tool_records,
                needs_confirmation=True,
                next_state={
                    "action": "confirm_transfer",
                    "confirmation_token": token,
                    "beneficiary_name": ben_name,
                    "amount_naira": amt_fmt,
                    "amount_kobo": amount_kobo
                }
            )

        # 6. Intent: Pay Bill (electricity, nepa, utility)
        is_bill_request = False
        if any(w in text for w in ["electricity", "nepa", "biller", "light bill", "meter", "ikedc", "ekedc"]):
            is_bill_request = True
        elif lang == Language.YORUBA and any(w in text for w in ["owo ina", "ina", "san owo ina"]):
            is_bill_request = True
        elif lang == Language.IGBO and any(w in text for w in ["oku", "ugwo oku", "kwo ugwo oku"]):
            is_bill_request = True
        elif lang == Language.HAUSA and any(w in text for w in ["kudin wuta", "wutan lantarki", "biya wuta"]):
            is_bill_request = True

        if is_bill_request:
            biller_id = "bil_ikeja_electric"
            meter_no = "45129038101"
            amount_kobo = 200_000 # 2,000 NGN
            idem_key = f"idem_bill_{secrets.token_hex(6)}"

            bill_res = await tools.pay_bill(
                account_id=account_id,
                biller_id=biller_id,
                customer_meter=meter_no,
                amount_kobo=amount_kobo,
                idempotency_key=idem_key,
                session_id=req.session_id
            )
            tool_records.append(ToolCallRecord(tool="pay_bill", arguments={"biller": biller_id, "amount_kobo": amount_kobo}, result=bill_res))

            bill_replies = {
                Language.HAUSA: "An biya kudin wutan NEPA Naira 2,000 cikin nasara.",
                Language.IGBO: "A kwuola ugwo oku eletrik nke Naira puku abuo nke oma.",
                Language.YORUBA: "A ti san owo ina NEPA ti egbaji Naira meji laseyori.",
                Language.NIGERIAN_ENGLISH: "Your electricity bill payment of 2,000 Naira has been successfully paid."
            }
            return AgentRespondResponse(
                reply_text=bill_replies.get(lang, bill_replies[Language.NIGERIAN_ENGLISH]),
                intent="pay_bill",
                tool_calls=tool_records
            )

        # 7. Intent: Check Balance
        if any(w in text for w in ["balance", "duba kudi", "kudi na", "kudi", "ego ole", "ile ego", "iye owo", "owo mi", "how much", "how much i get", "check my account"]):
            bal_res = await tools.check_balance(account_id)
            tool_records.append(ToolCallRecord(tool="check_balance", arguments={"account_id": account_id}, result=bal_res))
            
            naira_val = f"{bal_res.get('balance_naira', 0):,}"
            bal_replies = {
                Language.HAUSA: f"Kudin ku a asusun banki Naira {naira_val} ne.",
                Language.IGBO: f"Ego ole i nwere na akauntu gi bu Naira {naira_val}.",
                Language.YORUBA: f"Owo to wa ninu akanti yin je Naira {naira_val}.",
                Language.NIGERIAN_ENGLISH: f"Your current account balance is {naira_val} Naira."
            }
            return AgentRespondResponse(
                reply_text=bal_replies.get(lang, bal_replies[Language.NIGERIAN_ENGLISH]),
                intent="check_balance",
                tool_calls=tool_records
            )

        # 8. Intent: Buy Airtime
        if any(w in text for w in ["airtime", "recharge", "credit", "katin", "kaadi"]):
            amount_kobo = 100_000 # 1,000 NGN
            idem_key = f"idem_airtime_{secrets.token_hex(6)}"
            airtime_res = await tools.buy_airtime(
                account_id=account_id,
                phone_number=caller_id,
                network="MTN",
                amount_kobo=amount_kobo,
                idempotency_key=idem_key,
                session_id=req.session_id
            )
            tool_records.append(ToolCallRecord(tool="buy_airtime", arguments={"phone": caller_id}, result=airtime_res))

            airtime_replies = {
                Language.HAUSA: "An tura katin waya na Naira 1,000 zuwa lambar ku.",
                Language.IGBO: "E zigara kredit nke Naira otu puku na akara ekwenti gi.",
                Language.YORUBA: "A ti ra kaadi foonu ti egbewa Naira kan si noba yin.",
                Language.NIGERIAN_ENGLISH: "1,000 Naira airtime top-up has been credited to your phone number."
            }
            return AgentRespondResponse(
                reply_text=airtime_replies.get(lang, airtime_replies[Language.NIGERIAN_ENGLISH]),
                intent="buy_airtime",
                tool_calls=tool_records
            )

        # 9. Intent: Onboarding / Start KYC
        if any(w in text for w in ["onboard", "open account", "register", "bvn", "nin", "fara"]):
            return AgentRespondResponse(
                reply_text="Please speak your 11-digit BVN or National Identity Number clearly to open your account.",
                intent="start_kyc",
                next_state={"action": "await_bvn"}
            )

        # 10. Default Friendly Greeting / Assistance in selected language
        greetings = {
            Language.HAUSA: "Sannu! Barka da zuwa Lyfpartner. Zan iya taimaka muku duba kudi ko tura kudi.",
            Language.IGBO: "Ndewo! Nno na Lyfpartner. Enwere m ike inyere gi aka ile ego gi ma obu ziga ego.",
            Language.YORUBA: "Bawo! E kaabo si Lyfpartner. Mo le ran yin lowo lati wo owo yin tabi fi owo ranse.",
            Language.NIGERIAN_ENGLISH: "Welcome to Lyfpartner hotline! I can help you check balance, transfer money, or pay bills."
        }
        return AgentRespondResponse(
            reply_text=greetings.get(lang, greetings[Language.NIGERIAN_ENGLISH]),
            intent="greeting"
        )

class GroqLLMProvider(LLMProvider):
    """
    Live LLM dialogue reasoning powered by Groq (openai/gpt-oss-20b).
    Provides natural multi-turn responses across Hausa, Yoruba, Igbo, and Nigerian English
    while ensuring banking domain accuracy.
    """
    def __init__(self):
        self._mock = MockLLMProvider()
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL or "openai/gpt-oss-20b"

    async def respond(self, req: AgentRespondRequest, tools: ToolRegistry) -> AgentRespondResponse:
        # First let MockLLMProvider handle core deterministic banking intents
        mock_res = await self._mock.respond(req, tools)
        if mock_res.intent != "greeting":
            return mock_res

        if not self.api_key:
            return mock_res

        lang_names = {
            Language.HAUSA: "Hausa",
            Language.YORUBA: "Yoruba",
            Language.IGBO: "Igbo",
            Language.NIGERIAN_ENGLISH: "Nigerian English"
        }
        lang_name = lang_names.get(req.language, "Nigerian English")

        system_prompt = (
            f"You are Lyfpartner, an inclusive voice banking phone assistant in Nigeria for everyday citizens. "
            f"The caller is speaking {lang_name}. "
            f"Rules:\n"
            f"1. Respond directly in {lang_name} in a warm, polite, natural voice.\n"
            f"2. Keep it to 1-2 spoken sentences maximum. Do NOT use markdown, asterisks, or lists.\n"
            f"3. Account context: Caller balance is Naira 250,000.00. Common beneficiary is Musa Bello.\n"
            f"4. If they ask about services, state they can check balance, transfer money, pay electric bills, or buy airtime.\n"
            f"5. MANDATORY SECURITY & PRIVACY RULE: Whenever asking the caller for their PIN or discussing authentication, ALWAYS ask them to confirm they are in a private space and have their privacy (not in a public place where people can overhear), and tell them that they can punch in their 4-digit PIN on their phone keypad or say it out loud."
        )

        try:
            import httpx
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": req.text}
                        ],
                        "temperature": 0.4,
                        "max_tokens": 120
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    raw_reply = data["choices"][0]["message"]["content"].strip()
                    clean_reply = re.sub(r"<think>.*?</think>", "", raw_reply, flags=re.DOTALL).strip()
                    if clean_reply:
                        return AgentRespondResponse(
                            reply_text=clean_reply,
                            intent="natural_dialogue"
                        )
        except Exception:
            pass

        return mock_res

def get_llm_provider() -> LLMProvider:
    if settings.LLM_PROVIDER in ["groq", "live"] and settings.GROQ_API_KEY:
        return GroqLLMProvider()
    return MockLLMProvider()
