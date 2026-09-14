from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import text
from typing import List
import urllib.request
import urllib.error

from app.config import settings
from app.database import engine, get_db, Base
from app.models import Session as SessionModel, Message as MessageModel, MessageMetadata as MessageMetadataModel
from app.schemas import (
    SessionCreateRequest, SessionResponse,
    MessageCreateRequest, MessageResponse, MessageMetadataResponse,
    HealthCheckResponse, DependencyStatus
)
from app.errors import APIException, api_exception_handler, validation_exception_handler, generic_exception_handler

# Create database tables automatically on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.get("/health", response_model=HealthCheckResponse)
def health_check(db: DBSession = Depends(get_db)):
    dependencies = {}

    # Check Database
    try:
        db.execute(text("SELECT 1"))
        dependencies["database"] = DependencyStatus(status="ok", detail="PostgreSQL connected")
    except Exception as e:
        dependencies["database"] = DependencyStatus(status="fail", detail=str(e))

    # Check Ollama status
    try:
        req = urllib.request.Request(f"{settings.OLLAMA_HOST}/api/version", method="GET")
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                dependencies["ollama"] = DependencyStatus(status="ok", detail="Ollama endpoint reachable")
            else:
                dependencies["ollama"] = DependencyStatus(status="fail", detail=f"HTTP {response.status}")
    except Exception as e:
        dependencies["ollama"] = DependencyStatus(status="fail", detail=f"Ollama unreachable: {str(e)}")

    # Check Cloud Provider Key Config
    if settings.LLM_PROVIDER in ["anthropic", "openai"]:
        key = settings.ANTHROPIC_API_KEY if settings.LLM_PROVIDER == "anthropic" else settings.OPENAI_API_KEY
        if key and len(key) > 5:
            dependencies["llm_provider"] = DependencyStatus(status="ok", detail=f"{settings.LLM_PROVIDER.capitalize()} API key configured")
        else:
            dependencies["llm_provider"] = DependencyStatus(status="fail", detail=f"Missing API key for provider '{settings.LLM_PROVIDER}'")
    else:
        dependencies["llm_provider"] = DependencyStatus(status="ok", detail="Using local Ollama provider")

    overall_status = "ok" if all(dep.status == "ok" for dep in dependencies.values()) else "degraded"

    return HealthCheckResponse(
        status=overall_status,
        dependencies=dependencies,
        active_provider=settings.LLM_PROVIDER,
        active_model=settings.LLM_MODEL
    )


@app.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(req: SessionCreateRequest, db: DBSession = Depends(get_db)):
    new_session = SessionModel(
        title=req.title or "New Growth Chat",
        provider_preference=req.provider_preference or settings.LLM_PROVIDER
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


@app.get("/sessions", response_model=List[SessionResponse])
def list_sessions(db: DBSession = Depends(get_db)):
    return db.query(SessionModel).order_by(SessionModel.updated_at.desc()).all()


@app.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: DBSession = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise APIException(code="SESSION_NOT_FOUND", message=f"Session '{session_id}' not found", status_code=404)
    return session


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: DBSession = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise APIException(code="SESSION_NOT_FOUND", message=f"Session '{session_id}' not found", status_code=404)
    db.delete(session)
    db.commit()
    return {"status": "deleted", "id": session_id}


@app.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
def get_session_messages(session_id: str, db: DBSession = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise APIException(code="SESSION_NOT_FOUND", message=f"Session '{session_id}' not found", status_code=404)
    
    messages = db.query(MessageModel).filter(MessageModel.session_id == session_id).order_by(MessageModel.created_at.asc()).all()
    
    response_list = []
    for msg in messages:
        meta_resp = None
        if msg.msg_metadata:
            meta_resp = MessageMetadataResponse(
                citations=msg.msg_metadata.citations or [],
                artifact=msg.msg_metadata.artifact,
                provider_used=msg.msg_metadata.provider_used,
                model_used=msg.msg_metadata.model_used,
                latency_ms=msg.msg_metadata.latency_ms,
                prompt_tokens=msg.msg_metadata.prompt_tokens,
                completion_tokens=msg.msg_metadata.completion_tokens
            )
        response_list.append(MessageResponse(
            id=msg.id,
            session_id=msg.session_id,
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at,
            metadata=meta_resp
        ))
    return response_list


@app.post("/sessions/{session_id}/messages", response_model=MessageResponse)
def send_message(session_id: str, req: MessageCreateRequest, db: DBSession = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise APIException(code="SESSION_NOT_FOUND", message=f"Session '{session_id}' not found", status_code=404)

    # Save User Message
    user_msg = MessageModel(
        session_id=session_id,
        role="user",
        content=req.content
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # Stub response logic (Echo for Step 3, will be wired to RAG in Step 6)
    assistant_content = f"Echo response: {req.content}"
    
    assistant_msg = MessageModel(
        session_id=session_id,
        role="assistant",
        content=assistant_content
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    msg_meta = MessageMetadataModel(
        message_id=assistant_msg.id,
        citations=[],
        provider_used=req.provider or settings.LLM_PROVIDER,
        model_used=settings.LLM_MODEL,
        latency_ms=10
    )
    db.add(msg_meta)
    db.commit()
    db.refresh(msg_meta)

    meta_resp = MessageMetadataResponse(
        citations=[],
        artifact=None,
        provider_used=msg_meta.provider_used,
        model_used=msg_meta.model_used,
        latency_ms=10
    )

    return MessageResponse(
        id=assistant_msg.id,
        session_id=assistant_msg.session_id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        created_at=assistant_msg.created_at,
        metadata=meta_resp
    )
