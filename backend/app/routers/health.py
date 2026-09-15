"""Health check and system configuration routes."""
import urllib.request
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import text
from app.config import settings
from app.database import get_db
from app.schemas import HealthCheckResponse, DependencyStatus

router = APIRouter(tags=["System & Observability"])


@router.get("/health", response_model=HealthCheckResponse, summary="System Health Check")
def health_check(db: DBSession = Depends(get_db)):
    """Verifies operational status of PostgreSQL/SQLite database, Ollama runtime, and configured LLM providers."""
    dependencies = {}

    # Check Database connection
    try:
        db.execute(text("SELECT 1"))
        db_type = "PostgreSQL" if "postgresql" in settings.DATABASE_URL else "SQLite"
        dependencies["database"] = DependencyStatus(status="ok", detail=f"{db_type} operational")
    except Exception as e:
        dependencies["database"] = DependencyStatus(status="fail", detail=str(e))

    # Check Ollama local service
    try:
        req = urllib.request.Request(f"{settings.OLLAMA_HOST}/api/version", method="GET")
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                dependencies["ollama"] = DependencyStatus(status="ok", detail="Ollama reachable")
            else:
                dependencies["ollama"] = DependencyStatus(status="fail", detail=f"HTTP {response.status}")
    except Exception as e:
        dependencies["ollama"] = DependencyStatus(status="degraded", detail=f"Local Ollama unreachable: {str(e)}")

    # Check Cloud Provider Key Configuration
    if settings.LLM_PROVIDER in ["anthropic", "openai"]:
        key = settings.ANTHROPIC_API_KEY if settings.LLM_PROVIDER == "anthropic" else settings.OPENAI_API_KEY
        if key and len(key) > 5:
            dependencies["llm_provider"] = DependencyStatus(
                status="ok",
                detail=f"{settings.LLM_PROVIDER.capitalize()} credentials configured"
            )
        else:
            dependencies["llm_provider"] = DependencyStatus(
                status="degraded",
                detail=f"Missing or placeholder key for '{settings.LLM_PROVIDER}'; offline synthesis will activate if needed"
            )
    else:
        dependencies["llm_provider"] = DependencyStatus(status="ok", detail="Using local Ollama provider")

    has_fatal = dependencies["database"].status == "fail"
    overall_status = "fail" if has_fatal else ("ok" if all(d.status == "ok" for d in dependencies.values()) else "degraded")

    return HealthCheckResponse(
        status=overall_status,
        dependencies=dependencies,
        active_provider=settings.LLM_PROVIDER,
        active_model=settings.LLM_MODEL
    )


@router.get("/config", summary="Public Client Configuration")
def get_config():
    """Returns non-sensitive runtime configuration parameters for the frontend client."""
    return {
        "project_name": settings.PROJECT_NAME,
        "active_provider": settings.LLM_PROVIDER,
        "active_model": settings.LLM_MODEL,
        "ollama_fallback": settings.OLLAMA_FALLBACK
    }