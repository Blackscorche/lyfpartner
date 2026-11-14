"""Core Banking Provider interface and SQLite/Mock implementation."""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import json
import secrets
from typing import List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from shared.config import settings
from shared.database import (
    CustomerModel, AccountModel, TransactionModel, BeneficiaryModel,
    TransferQuoteModel, IdempotencyModel, AuditLogModel
)
from shared.errors import (
    InsufficientFundsException, LimitExceededException,
    BeneficiaryNotAllowedException, QuoteExpiredException, LyfpartnerException
)
from shared.schemas import (
    Account, Transaction, Beneficiary, TransferQuoteResponse,
    TransferConfirmResponse, Biller, DailyLimitsResponse
)

STANDARD_BILLERS = [
    Biller(biller_id="bil_ikeja_electric", category="electricity", name="Ikeja Electric (IKEDC)"),
    Biller(biller_id="bil_eko_electric", category="electricity", name="Eko Electricity (EKEDC)"),
    Biller(biller_id="bil_abuja_electric", category="electricity", name="Abuja Electricity (AEDC)"),
    Biller(biller_id="bil_dstv", category="cable", name="DStv Subscription"),
    Biller(biller_id="bil_gotv", category="cable", name="GOtv Nigeria"),
    Biller(biller_id="bil_lagos_water", category="water", name="Lagos State Water Corporation")
]

class BankProvider(ABC):
    @abstractmethod
    async def get_account(self, session: AsyncSession, account_id: str) -> Account:
        pass

    @abstractmethod
    async def get_balance(self, session: AsyncSession, account_id: str) -> int:
        pass

    @abstractmethod
    async def get_transactions(self, session: AsyncSession, account_id: str, limit: int = 5) -> List[Transaction]:
        pass

    @abstractmethod
    async def list_beneficiaries(self, session: AsyncSession, account_id: str) -> List[Beneficiary]:
        pass

    @abstractmethod
    async def add_beneficiary(self, session: AsyncSession, account_id: str, name: str, account_number: str, bank_name: str, nickname: Optional[str] = None) -> Beneficiary:
        pass

    @abstractmethod
    async def quote_transfer(self, session: AsyncSession, source_account_id: str, beneficiary_account_number: str, beneficiary_bank_name: str, amount_kobo: int, narration: str = "Voice transfer", is_voice_channel: bool = True, caregiver_verified: bool = False) -> TransferQuoteResponse:
        pass

    @abstractmethod
    async def confirm_transfer(self, session: AsyncSession, confirmation_token: str, idempotency_key: str, session_id: Optional[str] = None) -> TransferConfirmResponse:
        pass

    @abstractmethod
    async def pay_bill(self, session: AsyncSession, account_id: str, biller_id: str, customer_meter: str, amount_kobo: int, idempotency_key: str, session_id: Optional[str] = None) -> Transaction:
        pass

    @abstractmethod
    async def buy_airtime(self, session: AsyncSession, account_id: str, phone_number: str, network: str, amount_kobo: int, idempotency_key: str, session_id: Optional[str] = None) -> Transaction:
        pass

    @abstractmethod
    async def get_limits(self, session: AsyncSession, account_id: str) -> DailyLimitsResponse:
        pass

class MockBankProvider(BankProvider):
    async def get_account(self, session: AsyncSession, account_id: str) -> Account:
        res = await session.execute(
            select(AccountModel, CustomerModel)
            .join(CustomerModel, AccountModel.customer_id == CustomerModel.customer_id)
            .where((AccountModel.account_id == account_id) | (AccountModel.account_number == account_id))
        )
        row = res.first()
        if not row:
            raise LyfpartnerException("ACCOUNT_NOT_FOUND", f"Account {account_id} not found", status_code=404)
        acc, cust = row
        return Account(
            account_id=acc.account_id,
            account_number=acc.account_number,
            customer_id=acc.customer_id,
            name=cust.full_name,
            phone_number=cust.phone_number,
            balance_kobo=acc.balance_kobo,
            currency=acc.currency,
            bvn=cust.bvn,
            nin=cust.nin,
            status=acc.status,
            created_at=acc.created_at
        )

    async def get_balance(self, session: AsyncSession, account_id: str) -> int:
        acc = await self.get_account(session, account_id)
        return acc.balance_kobo

    async def get_transactions(self, session: AsyncSession, account_id: str, limit: int = 5) -> List[Transaction]:
        acc = await self.get_account(session, account_id)
        res = await session.execute(
            select(TransactionModel)
            .where(TransactionModel.account_id == acc.account_id)
            .order_by(TransactionModel.created_at.desc())
            .limit(limit)
        )
        txs = res.scalars().all()
        return [
            Transaction(
                transaction_id=t.transaction_id,
                account_id=t.account_id,
                type=t.type,
                amount_kobo=t.amount_kobo,
                narration=t.narration,
                reference=t.reference,
                balance_after_kobo=t.balance_after_kobo,
                created_at=t.created_at
            ) for t in txs
        ]

    async def list_beneficiaries(self, session: AsyncSession, account_id: str) -> List[Beneficiary]:
        acc = await self.get_account(session, account_id)
        res = await session.execute(
            select(BeneficiaryModel).where(BeneficiaryModel.account_id == acc.account_id)
        )
        bens = res.scalars().all()
        return [
            Beneficiary(
                beneficiary_id=b.beneficiary_id,
                account_id=b.account_id,
                name=b.name,
                account_number=b.account_number,
                bank_name=b.bank_name,
                nickname=b.nickname
            ) for b in bens
        ]

    async def add_beneficiary(self, session: AsyncSession, account_id: str, name: str, account_number: str, bank_name: str, nickname: Optional[str] = None) -> Beneficiary:
        acc = await self.get_account(session, account_id)
        ben_id = f"ben_{secrets.token_hex(4)}"
        ben = BeneficiaryModel(
            beneficiary_id=ben_id,
            account_id=acc.account_id,
            name=name,
            account_number=account_number,
            bank_name=bank_name,
            nickname=nickname
        )
        session.add(ben)
        await session.commit()
        return Beneficiary(
            beneficiary_id=ben.beneficiary_id,
            account_id=ben.account_id,
            name=ben.name,
            account_number=ben.account_number,
            bank_name=ben.bank_name,
            nickname=ben.nickname
        )

    async def get_limits(self, session: AsyncSession, account_id: str) -> DailyLimitsResponse:
        acc = await self.get_account(session, account_id)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        res = await session.execute(
            select(func.sum(TransactionModel.amount_kobo))
            .where(
                and_(
                    TransactionModel.account_id == acc.account_id,
                    TransactionModel.type == "debit",
                    TransactionModel.created_at >= today_start
                )
            )
        )
        spent_today = res.scalar() or 0
        remaining_today = max(0, settings.DAILY_TRANSFER_LIMIT_KOBO - spent_today)
        return DailyLimitsResponse(
            account_id=acc.account_id,
            per_transfer_limit_kobo=settings.PER_TRANSFER_LIMIT_KOBO,
            daily_transfer_limit_kobo=settings.DAILY_TRANSFER_LIMIT_KOBO,
            spent_today_kobo=spent_today,
            remaining_today_kobo=remaining_today
        )

    async def quote_transfer(
        self,
        session: AsyncSession,
        source_account_id: str,
        beneficiary_account_number: str,
        beneficiary_bank_name: str,
        amount_kobo: int,
        narration: str = "Voice transfer",
        is_voice_channel: bool = True,
        caregiver_verified: bool = False
    ) -> TransferQuoteResponse:
        acc = await self.get_account(session, source_account_id)

        # 1. Check integer kobo and amount positive
        if amount_kobo <= 0:
            raise LyfpartnerException("INVALID_AMOUNT", "Transfer amount must be greater than zero", status_code=400)

        # 2. Check balance
        fee_kobo = 1000 if amount_kobo < 500_000 else 2500 # NIP fee: 10 NGN or 25 NGN
        total_debit = amount_kobo + fee_kobo
        if acc.balance_kobo < total_debit:
            raise InsufficientFundsException()

        # 3. Check voice channel limits
        if is_voice_channel:
            if amount_kobo > settings.PER_TRANSFER_LIMIT_KOBO:
                raise LimitExceededException(f"Per-transfer limit is {settings.PER_TRANSFER_LIMIT_KOBO // 100} NGN")
            limits = await self.get_limits(session, acc.account_id)
            if limits.spent_today_kobo + amount_kobo > settings.DAILY_TRANSFER_LIMIT_KOBO:
                raise LimitExceededException(f"Daily transfer limit of {settings.DAILY_TRANSFER_LIMIT_KOBO // 100} NGN exceeded")

            # 4. Check saved beneficiary rule
            if settings.REQUIRE_SAVED_BENEFICIARY_FOR_VOICE and not caregiver_verified:
                bens = await self.list_beneficiaries(session, acc.account_id)
                match = next((b for b in bens if b.account_number == beneficiary_account_number), None)
                if not match:
                    # Look up if name matches any saved beneficiary
                    raise BeneficiaryNotAllowedException()

        # Resolve or mock beneficiary name
        bens = await self.list_beneficiaries(session, acc.account_id)
        match = next((b for b in bens if b.account_number == beneficiary_account_number), None)
        beneficiary_name = match.name if match else "Beneficiary Customer"

        # Generate quote and token
        token = f"quote_{secrets.token_urlsafe(16)}"
        expires_at = datetime.utcnow() + timedelta(seconds=settings.TRANSFER_QUOTE_EXPIRY_SECONDS)

        quote = TransferQuoteModel(
            token=token,
            source_account_id=acc.account_id,
            beneficiary_account_number=beneficiary_account_number,
            beneficiary_name=beneficiary_name,
            amount_kobo=amount_kobo,
            fee_kobo=fee_kobo,
            total_debit_kobo=total_debit,
            expires_at=expires_at,
            used=False
        )
        session.add(quote)
        await session.commit()

        return TransferQuoteResponse(
            confirmation_token=token,
            source_account_id=acc.account_id,
            beneficiary_account_number=beneficiary_account_number,
            beneficiary_name=beneficiary_name,
            amount_kobo=amount_kobo,
            fee_kobo=fee_kobo,
            total_debit_kobo=total_debit,
            expires_at=expires_at
        )

    async def confirm_transfer(self, session: AsyncSession, confirmation_token: str, idempotency_key: str, session_id: Optional[str] = None) -> TransferConfirmResponse:
        # Check idempotency
        idempotent_rec = await session.execute(
            select(IdempotencyModel).where(IdempotencyModel.idempotency_key == idempotency_key)
        )
        existing = idempotent_rec.scalar_one_or_none()
        if existing:
            data = json.loads(existing.response_json)
            return TransferConfirmResponse(**data)

        # Retrieve quote
        res = await session.execute(
            select(TransferQuoteModel).where(TransferQuoteModel.token == confirmation_token)
        )
        quote = res.scalar_one_or_none()
        if not quote:
            raise LyfpartnerException("INVALID_TOKEN", "Confirmation token invalid", status_code=400)
        if quote.used:
            raise LyfpartnerException("TOKEN_ALREADY_USED", "This confirmation token has already been executed", status_code=400)
        if quote.expires_at < datetime.utcnow():
            raise QuoteExpiredException()

        # Debit source account
        acc_res = await session.execute(
            select(AccountModel).where(AccountModel.account_id == quote.source_account_id)
        )
        acc = acc_res.scalar_one_or_none()
        if not acc or acc.balance_kobo < quote.total_debit_kobo:
            raise InsufficientFundsException()

        acc.balance_kobo -= quote.total_debit_kobo
        quote.used = True

        tx_id = f"tx_{secrets.token_hex(6)}"
        ref = f"NIP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4).upper()}"
        tx = TransactionModel(
            transaction_id=tx_id,
            account_id=acc.account_id,
            type="debit",
            amount_kobo=quote.amount_kobo,
            narration=f"Transfer to {quote.beneficiary_name} ({quote.beneficiary_account_number})",
            reference=ref,
            balance_after_kobo=acc.balance_kobo
        )
        session.add(tx)

        # Audit log entry
        audit = AuditLogModel(
            actor=acc.customer_id,
            action="transfer_confirmed",
            session_id=session_id,
            resource_id=tx_id,
            result="success",
            details_json=json.dumps({
                "amount_kobo": quote.amount_kobo,
                "fee_kobo": quote.fee_kobo,
                "beneficiary": quote.beneficiary_name,
                "token": quote.token
            })
        )
        session.add(audit)

        response = TransferConfirmResponse(
            transaction_id=tx_id,
            reference=ref,
            status="successful",
            amount_kobo=quote.amount_kobo,
            beneficiary_name=quote.beneficiary_name,
            source_account_id=acc.account_id,
            balance_after_kobo=acc.balance_kobo
        )

        # Save idempotency record
        idem = IdempotencyModel(
            idempotency_key=idempotency_key,
            action="transfer_confirm",
            response_json=json.dumps(response.model_dump(), default=str)
        )
        session.add(idem)
        await session.commit()

        return response

    async def pay_bill(self, session: AsyncSession, account_id: str, biller_id: str, customer_meter: str, amount_kobo: int, idempotency_key: str, session_id: Optional[str] = None) -> Transaction:
        # Check idempotency
        idempotent_rec = await session.execute(
            select(IdempotencyModel).where(IdempotencyModel.idempotency_key == idempotency_key)
        )
        existing = idempotent_rec.scalar_one_or_none()
        if existing:
            data = json.loads(existing.response_json)
            return Transaction(**data)

        acc = await self.get_account(session, account_id)
        if acc.balance_kobo < amount_kobo:
            raise InsufficientFundsException()

        acc_model = await session.get(AccountModel, acc.account_id)
        acc_model.balance_kobo -= amount_kobo

        biller = next((b for b in STANDARD_BILLERS if b.biller_id == biller_id), None)
        biller_name = biller.name if biller else biller_id

        tx_id = f"tx_bill_{secrets.token_hex(6)}"
        ref = f"BILL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
        tx = TransactionModel(
            transaction_id=tx_id,
            account_id=acc.account_id,
            type="debit",
            amount_kobo=amount_kobo,
            narration=f"Bill payment: {biller_name} (Meter/ID: {customer_meter})",
            reference=ref,
            balance_after_kobo=acc_model.balance_kobo
        )
        session.add(tx)

        audit = AuditLogModel(
            actor=acc.customer_id,
            action="bill_paid",
            session_id=session_id,
            resource_id=tx_id,
            result="success",
            details_json=json.dumps({"biller": biller_name, "meter": customer_meter, "amount_kobo": amount_kobo})
        )
        session.add(audit)

        tx_response = Transaction(
            transaction_id=tx.transaction_id,
            account_id=tx.account_id,
            type=tx.type,
            amount_kobo=tx.amount_kobo,
            narration=tx.narration,
            reference=tx.reference,
            balance_after_kobo=tx.balance_after_kobo,
            created_at=datetime.utcnow()
        )

        idem = IdempotencyModel(
            idempotency_key=idempotency_key,
            action="bill_pay",
            response_json=json.dumps(tx_response.model_dump(), default=str)
        )
        session.add(idem)
        await session.commit()
        return tx_response

    async def buy_airtime(self, session: AsyncSession, account_id: str, phone_number: str, network: str, amount_kobo: int, idempotency_key: str, session_id: Optional[str] = None) -> Transaction:
        # Check idempotency
        idempotent_rec = await session.execute(
            select(IdempotencyModel).where(IdempotencyModel.idempotency_key == idempotency_key)
        )
        existing = idempotent_rec.scalar_one_or_none()
        if existing:
            data = json.loads(existing.response_json)
            return Transaction(**data)

        acc = await self.get_account(session, account_id)
        if acc.balance_kobo < amount_kobo:
            raise InsufficientFundsException()

        acc_model = await session.get(AccountModel, acc.account_id)
        acc_model.balance_kobo -= amount_kobo

        tx_id = f"tx_airtime_{secrets.token_hex(6)}"
        ref = f"TOPUP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
        tx = TransactionModel(
            transaction_id=tx_id,
            account_id=acc.account_id,
            type="debit",
            amount_kobo=amount_kobo,
            narration=f"Airtime top-up: {network.upper()} ({phone_number})",
            reference=ref,
            balance_after_kobo=acc_model.balance_kobo
        )
        session.add(tx)

        audit = AuditLogModel(
            actor=acc.customer_id,
            action="airtime_purchased",
            session_id=session_id,
            resource_id=tx_id,
            result="success",
            details_json=json.dumps({"phone": phone_number, "network": network, "amount_kobo": amount_kobo})
        )
        session.add(audit)

        tx_response = Transaction(
            transaction_id=tx.transaction_id,
            account_id=tx.account_id,
            type=tx.type,
            amount_kobo=tx.amount_kobo,
            narration=tx.narration,
            reference=tx.reference,
            balance_after_kobo=tx.balance_after_kobo,
            created_at=datetime.utcnow()
        )

        idem = IdempotencyModel(
            idempotency_key=idempotency_key,
            action="airtime_buy",
            response_json=json.dumps(tx_response.model_dump(), default=str)
        )
        session.add(idem)
        await session.commit()
        return tx_response

def get_bank_provider() -> BankProvider:
    return MockBankProvider()
