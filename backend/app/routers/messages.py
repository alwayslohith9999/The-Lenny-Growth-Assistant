"""Message sending, grounded RAG conversation, and essay skill generation routes."""
import logging
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DBSession
from app.database import get_db
from app.models import (
    Session as SessionModel,
    Message as MessageModel,
    MessageMetadata as MessageMetadataModel,
    TranscriptChunk
)
from app.schemas import (
    MessageCreateRequest,
    MessageResponse,
    MessageMetadataResponse,
    Citation,
    Artifact
)
from app.errors import APIException
from app.config import settings
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.skills.ship30_essay import Ship30EssaySkill

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions/{session_id}", tags=["Messages & Skills"])


@router.get("/messages", response_model=List[MessageResponse], summary="Get Session Messages")
def get_session_messages(
    session_id: str,
    limit: int = Query(100, ge=1, le=200, description="Maximum messages to retrieve"),
    db: DBSession = Depends(get_db)
):
    """Retrieves all conversation messages and attached metadata for a session."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise APIException(code="SESSION_NOT_FOUND", message=f"Session '{session_id}' not found", status_code=404)

    messages = (
        db.query(MessageModel)
        .filter(MessageModel.session_id == session_id)
        .order_by(MessageModel.created_at.asc())
        .limit(limit)
        .all()
    )

    response_list = []
    for msg in messages:
        meta_resp = None
        if msg.msg_metadata:
            meta = msg.msg_metadata
            citations_data = [Citation(**c) for c in (meta.citations or [])]
            artifact_data = Artifact(**meta.artifact) if meta.artifact else None

            meta_resp = MessageMetadataResponse(
                citations=citations_data,
                artifact=artifact_data,
                provider_used=meta.provider_used,
                model_used=meta.model_used,
                latency_ms=meta.latency_ms,
                prompt_tokens=meta.prompt_tokens,
                completion_tokens=meta.completion_tokens,
                is_fallback=meta.provider_used == "offline-grounded-fallback"
            )

        response_list.append(
            MessageResponse(
                id=msg.id,
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
                metadata=meta_resp
            )
        )

    return response_list


@router.post("/messages", response_model=MessageResponse, summary="Send Conversational Message")
def send_message(session_id: str, req: MessageCreateRequest, db: DBSession = Depends(get_db)):
    """Sends a user query, retrieves grounded transcript excerpts, invokes LLM, and persists citations."""
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

    try:
        # 2. Retrieve relevant context chunks
        retrieved_chunks = RAGService.retrieve_relevant_chunks(db, req.content, top_k=4)

        if not retrieved_chunks:
            assistant_content = (
                "I searched Lenny's Podcast transcripts, but this specific topic is not "
                "substantially covered in the ingested episodes."
            )
            citations_list = []
            provider_used = "system"
            model_used = "retrieval-filter"
            latency_ms = 10
            prompt_tokens = 0
            completion_tokens = 0
            is_fallback = False
        else:
            formatted_context, citations_list = RAGService.build_prompt_context(retrieved_chunks)

            system_prompt = (
                "You are the Lenny Growth Assistant, an expert AI grounded strictly in Lenny's Podcast transcripts.\n"
                "INSTRUCTIONS:\n"
                "1. Answer the user's question ONLY using the provided transcript context sources below.\n"
                "2. Cite your sources clearly using [Episode Title, Timestamp] references when stating key claims.\n"
                "3. If the provided context does not contain enough information to answer the question, explicitly state: "
                "'Based on Lenny's Podcast transcripts, this topic is not fully covered.' Do NOT make up facts outside the context.\n\n"
                f"PROVIDED TRANSCRIPT CONTEXT:\n{formatted_context}"
            )

            # Sliced conversation history (last 6 messages)
            prior_messages = (
                db.query(MessageModel)
                .filter(MessageModel.session_id == session_id, MessageModel.id != user_msg.id)
                .order_by(MessageModel.created_at.asc())
                .all()[-6:]
            )

            llm_messages = [{"role": m.role, "content": m.content} for m in prior_messages if m.role in ["user", "assistant"]]
            llm_messages.append({"role": "user", "content": req.content})

            # 3. Generate Response
            provider_choice = req.provider or session.provider_preference or settings.LLM_PROVIDER
            llm_result = LLMService.generate(
                messages=llm_messages,
                system=system_prompt,
                requested_provider=provider_choice
            )

            assistant_content = llm_result["content"]
            provider_used = llm_result.get("provider", provider_choice)
            model_used = llm_result.get("model", settings.LLM_MODEL)
            latency_ms = llm_result.get("latency_ms", 150)
            prompt_tokens = llm_result.get("prompt_tokens", 0)
            completion_tokens = llm_result.get("completion_tokens", 0)
            is_fallback = llm_result.get("is_fallback", False)

        # 4. Persist Assistant Response & Metadata
        assistant_msg = MessageModel(
            session_id=session_id,
            role="assistant",
            content=assistant_content
        )
        db.add(assistant_msg)
        db.flush()

        msg_meta = MessageMetadataModel(
            message_id=assistant_msg.id,
            citations=citations_list,
            provider_used=provider_used,
            model_used=model_used,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        db.add(msg_meta)
        db.commit()
        db.refresh(assistant_msg)

        meta_resp = MessageMetadataResponse(
            citations=[Citation(**c) for c in citations_list],
            artifact=None,
            provider_used=provider_used,
            model_used=model_used,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            is_fallback=is_fallback
        )

        return MessageResponse(
            id=assistant_msg.id,
            session_id=assistant_msg.session_id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            created_at=assistant_msg.created_at,
            metadata=meta_resp
        )

    except Exception as err:
        db.rollback()
        logger.error(f"Failed to process message in session {session_id}: {err}")
        raise APIException(code="MESSAGE_PROCESSING_ERROR", message="Failed to process message", detail=str(err), status_code=500)


@router.post("/essay", response_model=MessageResponse, summary="Generate Ship 30 for 30 Essay")
def generate_essay(session_id: str, req: MessageCreateRequest, db: DBSession = Depends(get_db)):
    """Generates an executive Ship 30 for 30 essay grounded in transcript context and attaches an artifact."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise APIException(code="SESSION_NOT_FOUND", message=f"Session '{session_id}' not found", status_code=404)

    # 1. Retrieve context chunks
    chunks = RAGService.retrieve_relevant_chunks(db, req.content, top_k=4)
    if not chunks:
        all_chunks = db.query(TranscriptChunk).limit(4).all()
        chunks = [
            {
                "chunk_id": c.id,
                "episode_id": c.episode_id,
                "episode_title": c.episode_title,
                "guest_name": c.guest_name,
                "timestamp_start": c.timestamp_start,
                "timestamp_end": c.timestamp_end,
                "episode_url": c.episode_url,
                "content": c.content,
                "score": 1.0
            }
            for c in all_chunks
        ]

    # 2. Save User Request Message
    user_msg = MessageModel(
        session_id=session_id,
        role="user",
        content=f"[Essay Request]: {req.content}"
    )
    db.add(user_msg)
    db.commit()

    try:
        # 3. Execute Ship 30 Essay Skill
        skill = Ship30EssaySkill()
        provider_choice = req.provider or session.provider_preference or settings.LLM_PROVIDER
        result = skill.run(req.content, chunks, provider_name=provider_choice)

        # 4. Save Assistant Response Message & Artifact Metadata
        assistant_msg = MessageModel(
            session_id=session_id,
            role="assistant",
            content=result["content"]
        )
        db.add(assistant_msg)
        db.flush()

        msg_meta = MessageMetadataModel(
            message_id=assistant_msg.id,
            citations=result["citations"],
            artifact=result["artifact"],
            provider_used=result.get("provider_used", provider_choice),
            model_used=result.get("model_used", settings.LLM_MODEL),
            latency_ms=result.get("latency_ms", 300)
        )
        db.add(msg_meta)
        db.commit()
        db.refresh(assistant_msg)

        meta_resp = MessageMetadataResponse(
            citations=[Citation(**c) for c in result["citations"]],
            artifact=Artifact(**result["artifact"]),
            provider_used=msg_meta.provider_used,
            model_used=msg_meta.model_used,
            latency_ms=msg_meta.latency_ms,
            is_fallback=result.get("is_fallback", False)
        )

        return MessageResponse(
            id=assistant_msg.id,
            session_id=assistant_msg.session_id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            created_at=assistant_msg.created_at,
            metadata=meta_resp
        )

    except Exception as err:
        db.rollback()
        logger.error(f"Failed to generate essay in session {session_id}: {err}")
        raise APIException(code="ESSAY_GENERATION_ERROR", message="Failed to generate Ship 30 essay", detail=str(err), status_code=500)
