from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path

# Resolve the project root (.env lives at the repo root, one level above backend/)
_THIS_DIR = Path(__file__).resolve().parent          # backend/app/
_BACKEND_DIR = _THIS_DIR.parent                       # backend/
_PROJECT_ROOT = _BACKEND_DIR.parent                   # project root

# Collect all .env paths that actually exist (project root first, then backend/)
_env_files = [
    p for p in [_PROJECT_ROOT / ".env", _BACKEND_DIR / ".env", Path(".env")]
    if p.exists()
]


class Settings(BaseSettings):
    PROJECT_NAME: str = "Lenny Growth Assistant"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/lenny_growth"

    # LLM Provider Configuration
    LLM_PROVIDER: str = "anthropic"  # options: anthropic, openai, ollama
    LLM_MODEL: str = "claude-3-5-sonnet-20241022"
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    OPENAI_MODEL: str = "gpt-4o"
    OLLAMA_MODEL: str = "llama3.2"

    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Ollama Configuration
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_FALLBACK: bool = True

    # Security & Logging
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=_env_files if _env_files else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
