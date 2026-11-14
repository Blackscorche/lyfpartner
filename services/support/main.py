"""Support, Escalation, and Call Transcripts FastAPI Microservice."""
from typing import List, Optional
import secrets
from fastapi import FastAPI, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_db, TicketModel, TranscriptModel, SessionModel, AuditLogModel, init_db
from shared.logging_utils import RequestLoggingMiddleware, get_logger
from shared.schemas import Ticket, TicketCreate, EscalationRequest, TranscriptTurn

logger = get_logger("support_service")
app = FastAPI(title="Lyfpartner Support Service", version="1.0.0")
app.add_middleware(RequestLoggingMiddleware)

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/health")
async def health():
    return {"status": "ok", "service": "support"}

@app.post("/v1/support/tickets", response_model=Ticket)
async def create_ticket(req: TicketCreate, db: AsyncSession = Depends(get_db)):
    ticket_id = f"tck_{secrets.token_hex(4)}"
    ticket = TicketModel(
        ticket_id=ticket_id,
        session_id=req.session_id,
        customer_id=req.customer_id,
        caller_id=req.caller_id,
        subject=req.subject,
        description=req.description,
        status="open"
    )
    db.add(ticket)
    
    audit = AuditLogModel(
        actor=req.customer_id or req.caller_id or "system",
        action="ticket_created",
        session_id=req.session_id,
        resource_id=ticket_id,
        result="success"
    )
    db.add(audit)
    await db.commit()
    logger.info(f"Support ticket {ticket_id} created for session {req.session_id}")
    return ticket

@app.get("/v1/support/tickets", response_model=List[Ticket])
async def list_tickets(status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    stmt = select(TicketModel).order_by(TicketModel.created_at.desc())
    if status:
        stmt = stmt.where(TicketModel.status == status)
    res = await db.execute(stmt)
    return res.scalars().all()

@app.post("/v1/support/escalate")
async def escalate(req: EscalationRequest, db: AsyncSession = Depends(get_db)):
    # Update session status to escalated
    s_res = await db.execute(select(SessionModel).where(SessionModel.session_id == req.session_id))
    session = s_res.scalar_one_or_none()
    if session:
        session.outcome = "escalated"

    ticket_id = f"tck_esc_{secrets.token_hex(4)}"
    ticket = TicketModel(
        ticket_id=ticket_id,
        session_id=req.session_id,
        customer_id=session.account_id if session else None,
        caller_id=session.caller_id if session else None,
        subject=f"URGENT: Caller Escalation - {req.reason}",
        description=req.summary or f"Call escalated due to: {req.reason}",
        status="open"
    )
    db.add(ticket)

    audit = AuditLogModel(
        actor="caller",
        action="call_escalated",
        session_id=req.session_id,
        resource_id=ticket_id,
        result="escalated"
    )
    db.add(audit)
    await db.commit()
    logger.info(f"Session {req.session_id} escalated to human agent. Ticket {ticket_id}")
    return {"status": "escalated", "ticket_id": ticket_id, "message": "Connecting caller to human customer support agent..."}

@app.get("/v1/support/transcripts/{session_id}", response_model=List[TranscriptTurn])
async def get_transcript(session_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(TranscriptModel)
        .where(TranscriptModel.session_id == session_id)
        .order_by(TranscriptModel.timestamp.asc())
    )
    turns = res.scalars().all()
    return [
        TranscriptTurn(
            speaker=t.speaker,
            text=t.text,
            timestamp=t.timestamp
        ) for t in turns
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.support.main:app", host="0.0.0.0", port=8007, reload=True)
