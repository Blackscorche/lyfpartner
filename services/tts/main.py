"""TTS FastAPI Microservice: Text-to-Speech generation."""
from fastapi import FastAPI, Response
from shared.config import settings
from shared.schemas import TTSRequest, Language
from shared.logging_utils import RequestLoggingMiddleware, get_logger
from services.tts.provider import get_tts_provider

logger = get_logger("tts_service")
app = FastAPI(title="Lyfpartner TTS Service", version="1.0.0")
app.add_middleware(RequestLoggingMiddleware)

provider = get_tts_provider()

@app.get("/health")
async def health():
    return {"status": "ok", "service": "tts", "provider": settings.TTS_PROVIDER}

@app.post("/v1/tts/speak")
async def speak(request: TTSRequest):
    logger.info(f"Synthesizing speech for language {request.language}, text length: {len(request.text)}")
    audio_bytes = await provider.speak(request.text, request.language, request.sample_rate)
    return Response(content=audio_bytes, media_type="audio/wav")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.tts.main:app", host="0.0.0.0", port=8003, reload=True)
