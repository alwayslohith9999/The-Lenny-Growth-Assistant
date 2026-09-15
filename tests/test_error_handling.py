"""Unit and integration tests for error handling, schema validations, and security headers."""
import pytest


def test_empty_message_content_validation(client):
    """Verifies that empty string or whitespace-only messages are rejected with 422."""
    sess_res = client.post("/sessions", json={"title": "Validation Test"})
    session_id = sess_res.json()["id"]

    res1 = client.post(f"/sessions/{session_id}/messages", json={"content": ""})
    assert res1.status_code == 422
    assert res1.json()["error"]["code"] == "VALIDATION_ERROR"

    res2 = client.post(f"/sessions/{session_id}/messages", json={"content": "     "})
    assert res2.status_code == 422
    assert res2.json()["error"]["code"] == "VALIDATION_ERROR"


def test_oversized_session_title_validation(client):
    """Verifies that session titles exceeding 255 characters are rejected with 422."""
    oversized_title = "A" * 256
    res = client.post("/sessions", json={"title": oversized_title})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_security_headers_and_request_id(client):
    """Verifies that security headers and X-Request-ID are attached to all responses."""
    res = client.get("/health")
    assert res.status_code == 200
    headers = res.headers

    assert "X-Request-ID" in headers
    assert len(headers["X-Request-ID"]) > 10
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"


def test_invalid_provider_validation(client):
    """Verifies that unsupported provider values are rejected by schema validation."""
    res = client.post("/sessions", json={"title": "Test", "provider_preference": "unsupported_llm"})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"
