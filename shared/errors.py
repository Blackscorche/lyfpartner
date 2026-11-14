"""Standard error envelope and application exceptions for Lyfpartner."""
from typing import Any, Optional
from fastapi import HTTPException
from pydantic import BaseModel

class ErrorDetail(BaseModel):
    code: str
    message: str
    retryable: bool = False
    details: Optional[Any] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail

class LyfpartnerException(HTTPException):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        retryable: bool = False,
        details: Optional[Any] = None
    ):
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = details
        super().__init__(
            status_code=status_code,
            detail={"code": code, "message": message, "retryable": retryable, "details": details}
        )

# Predefined Common Exceptions
class AuthenticationFailedException(LyfpartnerException):
    def __init__(self, message: str = "Authentication failed", retryable: bool = True):
        super().__init__(code="AUTH_FAILED", message=message, status_code=401, retryable=retryable)

class AccountLockedException(LyfpartnerException):
    def __init__(self, message: str = "Account locked due to consecutive failed attempts"):
        super().__init__(code="ACCOUNT_LOCKED", message=message, status_code=403, retryable=False)

class InsufficientFundsException(LyfpartnerException):
    def __init__(self, message: str = "Insufficient balance for this transaction"):
        super().__init__(code="INSUFFICIENT_FUNDS", message=message, status_code=400, retryable=False)

class LimitExceededException(LyfpartnerException):
    def __init__(self, message: str = "Voice channel transaction limit exceeded"):
        super().__init__(code="LIMIT_EXCEEDED", message=message, status_code=400, retryable=False)

class BeneficiaryNotAllowedException(LyfpartnerException):
    def __init__(self, message: str = "New beneficiaries not permitted over voice without caregiver OTP"):
        super().__init__(code="BENEFICIARY_RESTRICTED", message=message, status_code=403, retryable=False)

class QuoteExpiredException(LyfpartnerException):
    def __init__(self, message: str = "Transfer quote has expired. Please request a new quote."):
        super().__init__(code="QUOTE_EXPIRED", message=message, status_code=400, retryable=True)

class SessionNotFoundException(LyfpartnerException):
    def __init__(self, session_id: str):
        super().__init__(code="SESSION_NOT_FOUND", message=f"Session {session_id} not found", status_code=404, retryable=False)
