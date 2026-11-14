"""ASR FastAPI Microservice: Speech-to-Text for Nigerian languages."""
from fastapi import FastAPI, UploadFile, File, Form, Depends
from shared.config import settings
from shared.schemas import Language, ASRResponse, LanguageDetectResponse
from shared.logging_utils import RequestLoggingMiddleware, get_logger
from services.asr.provider import get_asr_provider

logger = get_logger("asr_service")
app = FastAPI(title="Lyfpartner ASR Service", version="1.0.0")
app.add_middleware(RequestLoggingMiddleware)

provider = get_asr_provider()

@app.get("/health")
async def health():
    return {"status": "ok", "service": "asr", "provider": settings.ASR_PROVIDER}

@app.post("/v1/asr/transcribe", response_model=ASRResponse)
async def transcribe(
    audio: UploadFile = File(...),
    language: str = Form("en-ng")
):
    audio_bytes = await audio.read()
    lang_enum = Language(language) if language in [e.value for e in Language] else Language.NIGERIAN_ENGLISH
    result = await provider.transcribe(audio_bytes, lang_enum)
    logger.info(f"Transcribed audio: text='{result.text}', confidence={result.confidence}, low_conf={result.is_low_confidence}")
    return result

@app.post("/v1/asr/detect-language", response_model=LanguageDetectResponse)
async def detect_language(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    return await provider.detect_language(audio_bytes)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.asr.main:app", host="0.0.0.0", port=8001, reload=True)
