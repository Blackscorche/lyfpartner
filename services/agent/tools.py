"""Agent dialogue tools and tool execution engine with direct in-process database execution."""
import json
import secrets
from typing import Any, Dict, List, Optional
import httpx
from sqlalchemy import select
from shared.config import settings
from shared.database import (
    async_session_maker, TicketModel, SessionModel, AuditLogModel, CustomerModel, AccountModel
)
from shared.schemas import Language, AuthLevel
from shared.logging_utils import get_logger
from services.bank.provider import get_bank_provider, STANDARD_BILLERS

logger = get_logger("agent_tools")

class ToolRegistry:
    def __init__(self, http_client: Optional[httpx.AsyncClient] = None):
        self.http_client = http_client
        self.bank_provider = get_bank_provider()

    async def check_balance(self, account_id: str) -> Dict[str, Any]:
        """Check current account balance."""
        async with async_session_maker() as session:
            try:
                acc = await self.bank_provider.get_account(session, account_id)
                kobo = acc.balance_kobo
                naira = kobo // 100
                return {"balance_kobo": kobo, "balance_naira": naira, "currency": "NGN"}
            except Exception as e:
                logger.warning(f"Error checking balance: {e}")
                return {"balance_kobo": 0, "balance_naira": 0, "currency": "NGN"}

    async def get_recent_transactions(self, account_id: str, limit: int = 3) -> Dict[str, Any]:
        """Fetch recent transaction history."""
        async with async_session_maker() as session:
            try:
                txs = await self.bank_provider.get_transactions(session, account_id, limit)
                return {"transactions": [t.model_dump() for t in txs]}
            except Exception as e:
                logger.warning(f"Error fetching transactions: {e}")
                return {"transactions": []}

    async def list_beneficiaries(self, account_id: str) -> Dict[str, Any]:
        """List saved beneficiaries."""
        async with async_session_maker() as session:
            try:
                bens = await self.bank_provider.list_beneficiaries(session, account_id)
                return {"beneficiaries": [b.model_dump() for b in bens]}
            except Exception as e:
                logger.warning(f"Error listing beneficiaries: {e}")
                return {"beneficiaries": []}

    async def add_beneficiary(self, account_id: str, name: str, account_number: str, bank_name: str, nickname: Optional[str] = None) -> Dict[str, Any]:
        """Add a new beneficiary to customer account."""
        async with async_session_maker() as session:
            try:
                ben = await self.bank_provider.add_beneficiary(
                    session=session,
                    account_id=account_id,
                    name=name,
                    account_number=account_number,
                    bank_name=bank_name,
                    nickname=nickname
                )
                return ben.model_dump()
            except Exception as e:
                logger.warning(f"Error adding beneficiary: {e}")
                return {"error": str(e)}

    async def quote_transfer(self, source_account_id: str, beneficiary_account_number: str, beneficiary_bank_name: str, amount_kobo: int) -> Dict[str, Any]:
        """Initiate transfer quote and retrieve 120s confirmation token."""
        async with async_session_maker() as session:
            try:
                quote = await self.bank_provider.quote_transfer(
                    session=session,
                    source_account_id=source_account_id,
                    beneficiary_account_number=beneficiary_account_number,
                    beneficiary_bank_name=beneficiary_bank_name,
                    amount_kobo=amount_kobo,
                    is_voice_channel=True
                )
                return quote.model_dump()
            except Exception as e:
                logger.error(f"Error quoting transfer: {e}")
                return {"error": str(e)}

    async def confirm_transfer(self, confirmation_token: str, idempotency_key: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute transfer using quote token."""
        async with async_session_maker() as session:
            try:
                res = await self.bank_provider.confirm_transfer(
                    session=session,
                    confirmation_token=confirmation_token,
                    idempotency_key=idempotency_key,
                    session_id=session_id
                )
                return res.model_dump()
            except Exception as e:
                logger.error(f"Error confirming transfer: {e}")
                return {"error": str(e)}

    async def list_billers(self) -> Dict[str, Any]:
        """List utility billers."""
        return {"billers": [b.model_dump() for b in STANDARD_BILLERS]}

    async def pay_bill(self, account_id: str, biller_id: str, customer_meter: str, amount_kobo: int, idempotency_key: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Pay utility bill."""
        async with async_session_maker() as session:
            try:
                tx = await self.bank_provider.pay_bill(
                    session=session,
                    account_id=account_id,
                    biller_id=biller_id,
                    customer_meter=customer_meter,
                    amount_kobo=amount_kobo,
                    idempotency_key=idempotency_key,
                    session_id=session_id
                )
                return tx.model_dump()
            except Exception as e:
                logger.error(f"Error paying bill: {e}")
                return {"error": str(e)}

    async def buy_airtime(self, account_id: str, phone_number: str, network: str, amount_kobo: int, idempotency_key: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Buy phone airtime top-up."""
        async with async_session_maker() as session:
            try:
                tx = await self.bank_provider.buy_airtime(
                    session=session,
                    account_id=account_id,
                    phone_number=phone_number,
                    network=network,
                    amount_kobo=amount_kobo,
                    idempotency_key=idempotency_key,
                    session_id=session_id
                )
                return tx.model_dump()
            except Exception as e:
                logger.error(f"Error buying airtime: {e}")
                return {"error": str(e)}

    async def buy_data(self, account_id: str, phone_number: str, network: str, plan_name: str, amount_kobo: int, idempotency_key: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Buy internet data bundle."""
        async with async_session_maker() as session:
            try:
                tx = await self.bank_provider.buy_data(
                    session=session,
                    account_id=account_id,
                    phone_number=phone_number,
                    network=network,
                    plan_name=plan_name,
                    amount_kobo=amount_kobo,
                    idempotency_key=idempotency_key,
                    session_id=session_id
                )
                return tx.model_dump()
            except Exception as e:
                logger.error(f"Error buying data: {e}")
                return {"error": str(e)}

    async def report_issue(self, session_id: str, customer_id: Optional[str], subject: str, description: str) -> Dict[str, Any]:
        """Log a customer complaint/ticket."""
        async with async_session_maker() as session:
            ticket_id = f"tck_{secrets.token_hex(4)}"
            ticket = TicketModel(
                ticket_id=ticket_id,
                session_id=session_id,
                customer_id=customer_id,
                subject=subject,
                description=description,
                status="open"
            )
            session.add(ticket)
            await session.commit()
            return {"ticket_id": ticket_id, "status": "open"}

    async def escalate_to_human(self, session_id: str, reason: str, summary: Optional[str] = None) -> Dict[str, Any]:
        """Escalate session to human agent."""
        async with async_session_maker() as session:
            # Update session
            s_res = await session.execute(select(SessionModel).where(SessionModel.session_id == session_id))
            sess = s_res.scalar_one_or_none()
            if sess:
                sess.outcome = "escalated"

            ticket_id = f"tck_esc_{secrets.token_hex(4)}"
            ticket = TicketModel(
                ticket_id=ticket_id,
                session_id=session_id,
                customer_id=sess.account_id if sess else None,
                caller_id=sess.caller_id if sess else None,
                subject=f"URGENT: Caller Escalation - {reason}",
                description=summary or f"Call escalated due to: {reason}",
                status="open"
            )
            session.add(ticket)
            audit = AuditLogModel(
                actor="caller",
                action="call_escalated",
                session_id=session_id,
                resource_id=ticket_id,
                result="escalated"
            )
            session.add(audit)
            await session.commit()
            return {"status": "escalated", "ticket_id": ticket_id}

    async def send_sms_receipt(self, to_phone: str, message: str) -> Dict[str, Any]:
        """Send SMS receipt."""
        logger.info(f"[SMS-RECEIPT] To {to_phone}: {message}")
        return {"status": "delivered", "to": to_phone, "message": message}
