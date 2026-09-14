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


@app.get("/config")
def get_config():
    return {
        "active_provider": settings.LLM_PROVIDER,
        "active_model": settings.LLM_MODEL,
        "ollama_fallback": settings.OLLAMA_FALLBACK,
        "ollama_host": settings.OLLAMA_HOST
    }



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

    # 1. Save User Message
    user_msg = MessageModel(
        session_id=session_id,
        role="user",
        content=req.content
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 2. Retrieve relevant context chunks
    import sys
    from pathlib import Path
    ingestion_path = str(Path(__file__).parent.parent.parent / "ingestion")
    if ingestion_path not in sys.path:
        sys.path.append(ingestion_path)
    
    from retriever import retrieve_relevant_chunks
    from app.llm import generate_with_fallback

    retrieved_chunks = retrieve_relevant_chunks(db, req.content, top_k=4)

    # 3. Handle empty retrieval / low relevance
    if not retrieved_chunks:
        assistant_content = "I searched Lenny's Podcast transcripts, but this topic is not covered in the ingested episodes."
        citations = []
    else:
        # Build Context Block & Citations
        context_blocks = []
        citations = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            context_blocks.append(
                f"[Source {i}]: Episode '{chunk['episode_title']}' by {chunk['guest_name']} "
                f"({chunk['timestamp_start']}-{chunk['timestamp_end']})\n"
                f"URL: {chunk['episode_url']}\n"
                f"Content: {chunk['content']}\n"
            )
            citations.append({
                "chunk_id": chunk["chunk_id"],
                "episode_title": chunk["episode_title"],
                "guest_name": chunk["guest_name"],
                "timestamp_start": chunk["timestamp_start"],
                "timestamp_end": chunk["timestamp_end"],
                "episode_url": chunk["episode_url"],
                "content_snippet": chunk["content"][:150] + "...",
                "score": chunk["score"]
            })

        formatted_context = "\n---\n".join(context_blocks)

        system_prompt = (
            "You are the Lenny Growth Assistant, an expert AI grounded strictly in Lenny's Podcast transcripts.\n"
            "INSTRUCTIONS:\n"
            "1. Answer the user's question ONLY using the provided transcript context sources below.\n"
            "2. Cite your sources clearly using [Episode Title, Timestamp] references when stating key claims.\n"
            "3. If the provided context does not contain enough information to answer the question, explicitly state: "
            "'Based on Lenny's Podcast transcripts, this topic is not fully covered.' Do NOT make up or extrapolate facts outside the context.\n\n"
            f"PROVIDED TRANSCRIPT CONTEXT:\n{formatted_context}"
        )

        # Build windowed conversation history
        prior_messages = db.query(MessageModel).filter(
            MessageModel.session_id == session_id,
            MessageModel.id != user_msg.id
        ).order_by(MessageModel.created_at.asc()).all()[-6:]

        llm_messages = []
        for m in prior_messages:
            if m.role in ["user", "assistant"]:
                llm_messages.append({"role": m.role, "content": m.content})
        llm_messages.append({"role": "user", "content": req.content})

        # 4. Generate Response from LLM
        provider_choice = req.provider or session.provider_preference or settings.LLM_PROVIDER
        llm_result = generate_with_fallback(
            messages=llm_messages,
            system=system_prompt,
            requested_provider=provider_choice
        )
        assistant_content = llm_result["content"]
        provider_used = llm_result.get("provider", provider_choice)
        model_used = llm_result.get("model", settings.LLM_MODEL)
        prompt_tokens = llm_result.get("prompt_tokens", 0)
        completion_tokens = llm_result.get("completion_tokens", 0)


    # 5. Persist Assistant Response & Message Metadata
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
        citations=citations,
        provider_used=provider_used if 'provider_used' in locals() else settings.LLM_PROVIDER,
        model_used=model_used if 'model_used' in locals() else settings.LLM_MODEL,
        latency_ms=150,
        prompt_tokens=prompt_tokens if 'prompt_tokens' in locals() else 0,
        completion_tokens=completion_tokens if 'completion_tokens' in locals() else 0
    )
    db.add(msg_meta)
    db.commit()
    db.refresh(msg_meta)

    meta_resp = MessageMetadataResponse(
        citations=citations,
        artifact=None,
        provider_used=msg_meta.provider_used,
        model_used=msg_meta.model_used,
        latency_ms=msg_meta.latency_ms,
        prompt_tokens=msg_meta.prompt_tokens,
        completion_tokens=msg_meta.completion_tokens
    )

    return MessageResponse(
        id=assistant_msg.id,
        session_id=assistant_msg.session_id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        created_at=assistant_msg.created_at,
        metadata=meta_resp
    )

