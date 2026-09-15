# Entry point redirector — all routes live in app/main.py
# Used by: uvicorn main:app
from app.main import app  # noqa: F401
