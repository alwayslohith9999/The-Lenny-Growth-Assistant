"""Session management API routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session as DBSession
from app.database import get_db
from app.models import Session as SessionModel
from app.schemas import SessionCreateRequest, SessionResponse
from app.errors import APIException
from app.config import settings

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED, summary="Create Session")
def create_session(req: SessionCreateRequest, db: DBSession = Depends(get_db)):
    """Creates a new conversational growth session."""
    new_session = SessionModel(
        title=req.title or "New Growth Chat",
        provider_preference=req.provider_preference or settings.LLM_PROVIDER
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


@router.get("", response_model=List[SessionResponse], summary="List Sessions")
def list_sessions(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of sessions to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: DBSession = Depends(get_db)
):
    """Lists conversation sessions ordered by most recently updated."""
    return db.query(SessionModel).order_by(SessionModel.updated_at.desc()).offset(offset).limit(limit).all()


@router.get("/{session_id}", response_model=SessionResponse, summary="Get Session")
def get_session(session_id: str, db: DBSession = Depends(get_db)):
    """Retrieves session metadata by UUID."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise APIException(code="SESSION_NOT_FOUND", message=f"Session '{session_id}' not found", status_code=404)
    return session


@router.delete("/{session_id}", summary="Delete Session")
def delete_session(session_id: str, db: DBSession = Depends(get_db)):
    """Deletes a session and cascades deletion to all associated messages and artifacts."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise APIException(code="SESSION_NOT_FOUND", message=f"Session '{session_id}' not found", status_code=404)
    db.delete(session)
    db.commit()
    return {"status": "deleted", "id": session_id}
