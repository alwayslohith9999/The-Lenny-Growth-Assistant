"""Integration tests for conversational message endpoints and RAG grounding."""
import pytest


def test_send_message_grounded(client, seed_transcripts):
    """Verifies that sending a query retrieves relevant chunks, cites sources, and stores metadata."""
    # 1. Create a session
    sess_res = client.post("/sessions", json={"title": "PLG Discussion", "provider_preference": "anthropic"})
    assert sess_res.status_code == 201
    session_id = sess_res.json()["id"]

    # 2. Send message matching seeded Elena Verna content
    msg_res = client.post(
        f"/sessions/{session_id}/messages",
        json={"content": "What does Elena Verna say about product-led growth and sales?"}
    )
    assert msg_res.status_code == 200
    data = msg_res.json()

    assert data["role"] == "assistant"
    assert len(data["content"]) > 20
    assert data["metadata"] is not None

    citations = data["metadata"]["citations"]
    assert len(citations) > 0
    assert any("Elena Verna" in c["episode_title"] for c in citations)
    assert data["metadata"]["latency_ms"] is not None
    assert data["metadata"]["latency_ms"] >= 0


def test_send_message_unrelated_topic(client, seed_transcripts):
    """Verifies that queries on unindexed topics return the out-of-scope fallback response."""
    sess_res = client.post("/sessions", json={"title": "Quantum Physics"})
    session_id = sess_res.json()["id"]

    msg_res = client.post(
        f"/sessions/{session_id}/messages",
        json={"content": "Explain quantum chromodynamics and gluon plasma physics."}
    )
    assert msg_res.status_code == 200
    data = msg_res.json()
    assert "not substantially covered" in data["content"].lower() or "not covered" in data["content"].lower()


def test_get_session_messages_history(client, seed_transcripts):
    """Verifies retrieving message history contains both user and assistant turns with metadata."""
    sess_res = client.post("/sessions", json={"title": "History Test"})
    session_id = sess_res.json()["id"]

    client.post(f"/sessions/{session_id}/messages", json={"content": "Tell me about growth loops."})

    get_res = client.get(f"/sessions/{session_id}/messages")
    assert get_res.status_code == 200
    messages = get_res.json()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["metadata"] is not None


def test_send_message_invalid_session(client):
    """Verifies 404 error when posting to a non-existent session."""
    res = client.post("/sessions/non-existent-uuid/messages", json={"content": "Hello"})
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "SESSION_NOT_FOUND"
