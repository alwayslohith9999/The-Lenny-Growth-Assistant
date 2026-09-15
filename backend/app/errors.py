"""Centralized exception classes and FastAPI error handlers.

Guarantees a consistent JSON error envelope for all client and server errors,
while preventing sensitive internal trace/credential leakage in production.
"""
import logging
from datetime import datetime, timezone
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.schemas import ErrorResponse, ErrorDetail
from app.config import settings

logger = logging.getLogger(__name__)


class APIException(HTTPException):
    """Custom application-level API exception with structured code and message."""

    def __init__(
        self,
        code: str,
        message: str,
        detail: str = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.detail_str = detail
        self.status_code = status_code


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handles explicit APIException instances raised by business logic."""
    logger.warning(f"APIException [{exc.code}] on {request.method} {request.url.path}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                detail=exc.detail_str,
                timestamp=datetime.now(timezone.utc)
            )
        ).model_dump(mode="json")
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handles Pydantic input validation errors and aggregates all invalid fields."""
    errors = exc.errors()
    details = []
    for err in errors:
        loc = " -> ".join([str(l) for l in err.get("loc", [])])
        msg = err.get("msg", "Invalid value")
        details.append(f"{loc}: {msg}")

    summary_msg = f"Validation failed for {len(errors)} field(s)"
    combined_details = "; ".join(details)
    logger.info(f"ValidationError on {request.method} {request.url.path}: {combined_details}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message=summary_msg,
                detail=combined_details,
                timestamp=datetime.now(timezone.utc)
            )
        ).model_dump(mode="json")
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches unhandled server exceptions, logs full traceback, and masks details in production."""
    logger.exception(f"Unhandled 500 server error on {request.method} {request.url.path}: {exc}")

    detail_message = str(exc) if settings.DEBUG else "An internal server error occurred. Please contact support."

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected server error occurred.",
                detail=detail_message,
                timestamp=datetime.now(timezone.utc)
            )
        ).model_dump(mode="json")
    )
