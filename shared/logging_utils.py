"""Structured JSON logging and sensitive data sanitization."""
import json
import logging
import re
import sys
import uuid
from typing import Any, Dict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

SENSITIVE_PATTERNS = [
    (re.compile(r'\b\d{4}\b'), '****'),  # 4-digit PINs
    (re.compile(r'\b\d{11}\b'), '***********'),  # BVN/NIN (11 digits)
]

def sanitize_text(text: str) -> str:
    """Mask sensitive patterns such as 4-digit PINs and 11-digit BVN/NINs."""
    if not isinstance(text, str):
        return text
    sanitized = text
    for pattern, mask in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(mask, sanitized)
    return sanitized

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": sanitize_text(record.getMessage()),
        }
        if hasattr(record, "request_id"):
            log_obj["request_id"] = getattr(record, "request_id")
        if hasattr(record, "session_id"):
            log_obj["session_id"] = getattr(record, "session_id")
        if hasattr(record, "extra_data"):
            log_obj["data"] = getattr(record, "extra_data")
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        session_id = request.headers.get("X-Session-Id", request.query_params.get("session_id", "none"))
        
        # Attach request_id to request state
        request.state.request_id = request_id
        request.state.session_id = session_id
        
        response: Response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response
