"""SQLAlchemy data models for Lenny Growth Assistant.

Defines database schemas for users, sessions, messages, telemetry metadata,
and indexed transcript chunks.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, JSON, Index
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    """Generate a standard UUID4 string for primary keys."""
    return str(uuid.uuid4())


class UserMetadata(Base):
    """User profile record for multi-tenant and ownership support."""
    __tablename__ = "user_metadata"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="user")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    """Chat session conversation container."""
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("user_metadata.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False, default="New Growth Chat")
    provider_preference = Column(String(50), default="anthropic")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("UserMetadata", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    """Individual conversational message within a session."""
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    session = relationship("Session", back_populates="messages")
    msg_metadata = relationship("MessageMetadata", back_populates="message", uselist=False, cascade="all, delete-orphan")


class MessageMetadata(Base):
    """Execution telemetry, citations, and generated artifacts associated with an assistant message."""
    __tablename__ = "message_metadata"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    citations = Column(JSON, default=list)  # Array of {episode_title, timestamp, chunk_id, score}
    artifact = Column(JSON, nullable=True)   # {type: 'markdown'|'html', title: str, content: str}
    provider_used = Column(String(50), nullable=True)
    model_used = Column(String(100), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    message = relationship("Message", back_populates="msg_metadata")


class TranscriptChunk(Base):
    """Chunked and embedded podcast transcript segment for grounded retrieval."""
    __tablename__ = "transcript_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    episode_id = Column(String(100), nullable=False, index=True)
    episode_title = Column(String(255), nullable=False)
    episode_url = Column(String(500), nullable=True)
    guest_name = Column(String(255), nullable=True)
    timestamp_start = Column(String(50), nullable=True)
    timestamp_end = Column(String(50), nullable=True)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # Store list of floats for portability
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_transcript_episode_time", "episode_id", "timestamp_start"),
    )
