"""Integration tests for Ship 30 for 30 essay generation skill."""
import pytest


def test_generate_ship30_essay(client, seed_transcripts):
    """Verifies that the /essay endpoint generates structured essays with attached markdown artifacts."""
    sess_res = client.post("/sessions", json={"title": "Essay Session"})
    session_id = sess_res.json()["id"]

    essay_res = client.post(
        f"/sessions/{session_id}/essay",
        json={"content": "B2B Product-Led Growth Funnels"}
    )
    assert essay_res.status_code == 200
    data = essay_res.json()

    assert data["role"] == "assistant"
    assert data["metadata"] is not None

    artifact = data["metadata"]["artifact"]
    assert artifact is not None
    assert artifact["type"] == "markdown"
    assert len(artifact["title"]) > 0
    assert len(artifact["content"]) > 100

    citations = data["metadata"]["citations"]
    assert isinstance(citations, list)
    assert len(citations) > 0


def test_generate_essay_invalid_session(client):
    """Verifies 404 response when attempting to generate an essay for a missing session."""
    res = client.post("/sessions/non-existent-id/essay", json={"content": "Growth strategy"})
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "SESSION_NOT_FOUND"
