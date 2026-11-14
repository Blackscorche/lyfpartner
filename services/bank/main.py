"""Mock Core Banking FastAPI Microservice."""
from typing import List, Optional
from fastapi import FastAPI, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_db, init_db
from shared.logging_utils import RequestLoggingMiddleware, get_logger
from shared.schemas import (
    Account, Transaction, Beneficiary, TransferQuoteRequest, TransferQuoteResponse,
    TransferConfirmRequest, TransferConfirmResponse, Biller, BillPaymentRequest,
    AirtimePurchaseRequest, DailyLimitsResponse
)
from services.bank.provider import get_bank_provider, STANDARD_BILLERS

logger = get_logger("bank_service")
app = FastAPI(title="Lyfpartner Mock Core Banking", version="1.0.0")
app.add_middleware(RequestLoggingMiddleware)

provider = get_bank_provider()

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/health")
async def health():
    return {"status": "ok", "service": "bank"}

@app.get("/v1/accounts/{id}", response_model=Account)
async def get_account(id: str, db: AsyncSession = Depends(get_db)):
    return await provider.get_account(db, id)

@app.get("/v1/accounts/{id}/balance")
async def get_balance(id: str, db: AsyncSession = Depends(get_db)):
    balance_kobo = await provider.get_balance(db, id)
    return {"account_id": id, "balance_kobo": balance_kobo, "currency": "NGN"}

@app.get("/v1/accounts/{id}/transactions", response_model=List[Transaction])
async def get_transactions(id: str, limit: int = Query(5, ge=1, le=50), db: AsyncSession = Depends(get_db)):
    return await provider.get_transactions(db, id, limit)

@app.get("/v1/accounts/{id}/beneficiaries", response_model=List[Beneficiary])
async def list_beneficiaries(id: str, db: AsyncSession = Depends(get_db)):
    return await provider.list_beneficiaries(db, id)

@app.post("/v1/accounts/{id}/beneficiaries", response_model=Beneficiary)
async def add_beneficiary(id: str, data: dict, db: AsyncSession = Depends(get_db)):
    return await provider.add_beneficiary(
        db, id, data["name"], data["account_number"], data["bank_name"], data.get("nickname")
    )

@app.post("/v1/transfers/quote", response_model=TransferQuoteResponse)
async def quote_transfer(req: TransferQuoteRequest, is_voice: bool = True, db: AsyncSession = Depends(get_db)):
    return await provider.quote_transfer(
        db,
        source_account_id=req.source_account_id,
        beneficiary_account_number=req.beneficiary_account_number,
        beneficiary_bank_name=req.beneficiary_bank_name,
        amount_kobo=req.amount_kobo,
        narration=req.narration or "Voice transfer",
        is_voice_channel=is_voice
    )

@app.post("/v1/transfers/confirm", response_model=TransferConfirmResponse)
async def confirm_transfer(
    req: TransferConfirmRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
    db: AsyncSession = Depends(get_db)
):
    key = idempotency_key or req.idempotency_key
    return await provider.confirm_transfer(db, req.confirmation_token, key, session_id=x_session_id)

@app.get("/v1/billers", response_model=List[Biller])
async def list_billers():
    return STANDARD_BILLERS

@app.post("/v1/bills/pay", response_model=Transaction)
async def pay_bill(
    req: BillPaymentRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
    db: AsyncSession = Depends(get_db)
):
    key = idempotency_key or req.idempotency_key
    return await provider.pay_bill(
        db, req.account_id, req.biller_id, req.customer_meter_or_id, req.amount_kobo, key, session_id=x_session_id
    )

@app.post("/v1/airtime/buy", response_model=Transaction)
async def buy_airtime(
    req: AirtimePurchaseRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
    db: AsyncSession = Depends(get_db)
):
    key = idempotency_key or req.idempotency_key
    return await provider.buy_airtime(
        db, req.account_id, req.phone_number, req.network, req.amount_kobo, key, session_id=x_session_id
    )

@app.get("/v1/limits/{id}", response_model=DailyLimitsResponse)
async def get_limits(id: str, db: AsyncSession = Depends(get_db)):
    return await provider.get_limits(db, id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.bank.main:app", host="0.0.0.0", port=8005, reload=True)
