"""FastAPI Application Entry Point for Lenny Growth Assistant.

Configures structured middleware, exception handlers, database lifecycle, and modular routers.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.database import engine, Base
from app.errors import APIException, api_exception_handler, validation_exception_handler, generic_exception_handler
from app.logging_config import setup_structured_logging, StructuredLoggingMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.routers import health_router, sessions_router, messages_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown lifecycle."""
    # Ensure database tables exist on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Internal tool enabling product and growth operators to query battle-tested Lenny's Podcast transcripts, "
        "synthesize grounded insights with full episode citations, and generate Ship 30 for 30 style essays."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Parse allowed CORS origins from settings
allowed_origins = [origin.strip() for origin in settings.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

# CORS Middleware (secure, non-wildcard with credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

# Request ID correlation & security headers middleware
app.add_middleware(RequestIDMiddleware)

# Structured JSON logging
setup_structured_logging()
app.add_middleware(StructuredLoggingMiddleware)

# Exception handlers
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Register modular routers
app.include_router(health_router)
app.include_router(sessions_router)
app.include_router(messages_router)
