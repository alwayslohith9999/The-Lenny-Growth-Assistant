from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime


# Standard Error Envelope Schemas
class ErrorDetail(BaseModel):
    code: str
    message: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    error: ErrorDetail


# Session Schemas
class SessionCreateRequest(BaseModel):
    title: Optional[str] = "New Growth Chat"
    provider_preference: Optional[str] = "anthropic"


class SessionResponse(BaseModel):
    id: str
    title: str
    provider_preference: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Message & Metadata Schemas
class Citation(BaseModel):
    chunk_id: str
    episode_title: str
    guest_name: Optional[str] = None
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None
    episode_url: Optional[str] = None
    content_snippet: Optional[str] = None
    score: Optional[float] = None


class Artifact(BaseModel):
    type: str  # 'markdown' | 'html'
    title: str
    content: str


class MessageMetadataResponse(BaseModel):
    citations: List[Citation] = []
    artifact: Optional[Artifact] = None
    provider_used: Optional[str] = None
    model_used: Optional[str] = None
    latency_ms: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None

    class Config:
        from_attributes = True


class MessageCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Message text content")
    provider: Optional[str] = None
    essay_mode: Optional[bool] = False


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime
    metadata: Optional[MessageMetadataResponse] = None

    class Config:
        from_attributes = True


# Health Check Schema
class DependencyStatus(BaseModel):
    status: str  # "ok" | "fail"
    detail: Optional[str] = None


class HealthCheckResponse(BaseModel):
    status: str  # "ok" | "degraded" | "error"
    dependencies: Dict[str, DependencyStatus]
    active_provider: str
    active_model: str
