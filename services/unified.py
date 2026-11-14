"""Unified Application combining all Lyfpartner services for easy single-process execution."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.database import init_db
from shared.seed_data import seed_database
from shared.logging_utils import RequestLoggingMiddleware

# Import sub-apps
from services.gateway.main import app as gateway_app
from services.asr.main import app as asr_app
from services.agent.main import app as agent_app
from services.tts.main import app as tts_app
from services.auth.main import app as auth_app
from services.bank.main import app as bank_app
from services.kyc.main import app as kyc_app
from services.support.main import app as support_app
from services.admin.main import app as admin_app
from services.notify.main import app as notify_app

unified_app = FastAPI(
    title="Lyfpartner: Voice-First Inclusive Banking Hotline API",
    version="1.0.0",
    description="Full API suite for voice banking in Hausa, Igbo, Yoruba and Nigerian English"
)

unified_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
unified_app.add_middleware(RequestLoggingMiddleware)

@unified_app.on_event("startup")
async def startup_event():
    await init_db()
    await seed_database()

@unified_app.get("/health")
async def health():
    return {"status": "ok", "service": "unified", "version": "1.0.0"}

# Mount all service routes
unified_app.include_router(gateway_app.router)
unified_app.include_router(asr_app.router)
unified_app.include_router(agent_app.router)
unified_app.include_router(tts_app.router)
unified_app.include_router(auth_app.router)
unified_app.include_router(bank_app.router)
unified_app.include_router(kyc_app.router)
unified_app.include_router(support_app.router)
unified_app.include_router(admin_app.router)
unified_app.include_router(notify_app.router)

# Mount web frontend if dist exists
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

if os.path.exists("web/dist"):
    if os.path.exists("web/dist/assets"):
        unified_app.mount("/assets", StaticFiles(directory="web/dist/assets"), name="assets")

    @unified_app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join("web/dist", full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse("web/dist/index.html")
