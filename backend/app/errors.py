from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime, timezone
from app.schemas import ErrorResponse, ErrorDetail


class APIException(HTTPException):
    def __init__(self, code: str, message: str, detail: str = None, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.detail_str = detail
        self.status_code = status_code


async def api_exception_handler(request: Request, exc: APIException):
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


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_err = errors[0] if errors else {}
    msg = first_err.get("msg", "Validation error")
    loc = " -> ".join([str(l) for l in first_err.get("loc", [])])
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message=msg,
                detail=f"Field location: {loc}",
                timestamp=datetime.now(timezone.utc)
            )
        ).model_dump(mode="json")
    )


async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected server error occurred.",
                detail=str(exc),
                timestamp=datetime.now(timezone.utc)
            )
        ).model_dump(mode="json")
    )
