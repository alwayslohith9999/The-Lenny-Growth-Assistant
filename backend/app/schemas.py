"""Pydantic request and response schemas for Lenny Growth Assistant API.

Provides strict input validation, data normalization, and complete OpenAPI/Swagger
documentation definitions.
"""
from typing import List, Optional, Dict, Literal
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict, field_validator


# Standard Error Envelope Schemas
class ErrorDetail(BaseModel):
    """Detailed error object returned within the standard error envelope."""
    code: str = Field(..., description="Machine-readable uppercase error identifier", examples=["SESSION_NOT_FOUND"])
    message: str = Field(..., description="Human-readable explanation of what went wrong", examples=["Session 'abc' not found"])
    detail: Optional[str] = Field(None, description="Optional extra diagnostic details or error context")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp of error occurrence")


class ErrorResponse(BaseModel):
    """Standardized top-level API error response envelope."""
    error: ErrorDetail


# Session Schemas
class SessionCreateRequest(BaseModel):
    """Payload to create a new conversational session."""
    title: Optional[str] = Field(
        "New Growth Chat",
        min_length=1,
        max_length=255,
        description="Title or topic label for the session",
        examples=["B2B PLG Strategy Discussion"]
    )
    provider_preference: Optional[Literal["anthropic", "openai", "ollama"]] = Field(
        "anthropic",
        description="Preferred LLM provider for this conversation",
        examples=["anthropic"]
    )

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return "New Growth Chat"
        return v


class SessionResponse(BaseModel):
    """Conversational session metadata."""
    id: str = Field(..., description="Unique UUID identifier of the session")
    title: str = Field(..., description="Human-readable title of the session")
    provider_preference: str = Field(..., description="Active default LLM provider")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last message timestamp")

    model_config = ConfigDict(from_attributes=True)


# Message & Metadata Schemas
class Citation(BaseModel):
    """Grounded transcript segment citation used as context for the answer."""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    episode_title: str = Field(..., description="Title of the source podcast episode")
    guest_name: Optional[str] = Field(None, description="Guest speaker featured in the episode")
    timestamp_start: Optional[str] = Field(None, description="Start timestamp of the segment", examples=["00:14:20"])
    timestamp_end: Optional[str] = Field(None, description="End timestamp of the segment", examples=["00:16:45"])
    episode_url: Optional[str] = Field(None, description="Link to the episode or transcript")
    content_snippet: Optional[str] = Field(None, description="Excerpt preview of the source text")
    score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Relevance similarity score (0.0 to 1.0)")


class Artifact(BaseModel):
    """Generated document artifact (e.g. Ship 30 for 30 essay)."""
    type: Literal["markdown", "html"] = Field(..., description="MIME format of the artifact content")
    title: str = Field(..., description="Title of the artifact document")
    content: str = Field(..., description="Raw Markdown or sanitized HTML payload")


class MessageMetadataResponse(BaseModel):
    """Execution telemetry and grounded metadata attached to assistant responses."""
    citations: List[Citation] = Field(default_factory=list, description="List of source citations grounded in transcripts")
    artifact: Optional[Artifact] = Field(None, description="Generated document artifact if created")
    provider_used: Optional[str] = Field(None, description="LLM provider that generated the response")
    model_used: Optional[str] = Field(None, description="Specific model identifier that generated the response")
    latency_ms: Optional[int] = Field(None, ge=0, description="End-to-end generation duration in milliseconds")
    prompt_tokens: Optional[int] = Field(None, ge=0, description="Prompt tokens consumed")
    completion_tokens: Optional[int] = Field(None, ge=0, description="Output tokens generated")
    is_fallback: Optional[bool] = Field(False, description="True if response was synthesized via offline/local fallback")

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class MessageCreateRequest(BaseModel):
    """Request payload to post a user message or generate an essay."""
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Query text or essay prompt",
        examples=["How do growth loops differ from traditional marketing funnels?"]
    )
    provider: Optional[Literal["anthropic", "openai", "ollama"]] = Field(
        None,
        description="Optional provider override for this message"
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message content cannot be empty or only whitespace")
        return stripped


class MessageResponse(BaseModel):
    """Full conversational message including role, content, and telemetry metadata."""
    id: str = Field(..., description="Unique message UUID")
    session_id: str = Field(..., description="Parent session UUID")
    role: str = Field(..., description="Message author: user | assistant | system")
    content: str = Field(..., description="Message text content")
    created_at: datetime = Field(..., description="Message creation timestamp")
    metadata: Optional[MessageMetadataResponse] = Field(None, description="Telemetry, citations, and artifacts")

    model_config = ConfigDict(from_attributes=True)


# Health Check Schema
class DependencyStatus(BaseModel):
    """Health status of an individual system dependency."""
    status: Literal["ok", "fail", "degraded"] = Field(..., description="Operational status of the component")
    detail: Optional[str] = Field(None, description="Descriptive status or error message")


class HealthCheckResponse(BaseModel):
    """System-wide health check report."""
    status: Literal["ok", "degraded", "fail"] = Field(..., description="Overall platform status")
    dependencies: Dict[str, DependencyStatus] = Field(..., description="Subsystem health statuses")
    active_provider: str = Field(..., description="Configured default LLM provider")
    active_model: str = Field(..., description="Configured default LLM model name")
