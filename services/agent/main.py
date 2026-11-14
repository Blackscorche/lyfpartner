"""Agent Dialogue & Tool Calling FastAPI Microservice."""
from fastapi import FastAPI
from shared.config import settings
from shared.logging_utils import RequestLoggingMiddleware, get_logger
from shared.schemas import AgentRespondRequest, AgentRespondResponse
from services.agent.provider import get_llm_provider
from services.agent.tools import ToolRegistry

logger = get_logger("agent_service")
app = FastAPI(title="Lyfpartner Agent Dialogue Service", version="1.0.0")
app.add_middleware(RequestLoggingMiddleware)

provider = get_llm_provider()
tool_registry = ToolRegistry()

@app.get("/health")
async def health():
    return {"status": "ok", "service": "agent", "llm_provider": settings.LLM_PROVIDER}

@app.post("/v1/agent/respond", response_model=AgentRespondResponse)
async def respond(req: AgentRespondRequest):
    logger.info(f"Agent responding to session {req.session_id} in {req.language}: text='{req.text}'")
    return await provider.respond(req, tool_registry)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.agent.main:app", host="0.0.0.0", port=8002, reload=True)
