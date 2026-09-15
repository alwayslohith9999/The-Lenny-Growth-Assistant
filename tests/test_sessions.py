def test_create_session(client):
    res = client.post("/sessions", json={"title": "Growth Strategy Session"})
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Growth Strategy Session"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_session_default_title(client):
    res = client.post("/sessions", json={})
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "New Growth Chat"
    assert data["provider_preference"] == "anthropic"


def test_list_sessions(client):
    client.post("/sessions", json={"title": "Session 1"})
    client.post("/sessions", json={"title": "Session 2"})
    res = client.get("/sessions")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 2


def test_get_session(client):
    create_res = client.post("/sessions", json={"title": "Fetch Me"})
    session_id = create_res.json()["id"]

    res = client.get(f"/sessions/{session_id}")
    assert res.status_code == 200
    assert res.json()["title"] == "Fetch Me"


def test_get_session_not_found(client):
    res = client.get("/sessions/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404
    body = res.json()
    assert body["error"]["code"] == "SESSION_NOT_FOUND"


def test_delete_session(client):
    s_res = client.post("/sessions", json={"title": "To Delete"})
    session_id = s_res.json()["id"]

    del_res = client.delete(f"/sessions/{session_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    get_res = client.get(f"/sessions/{session_id}")
    assert get_res.status_code == 404


def test_delete_session_not_found(client):
    res = client.delete("/sessions/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404


def test_get_messages_empty(client):
    s_res = client.post("/sessions", json={"title": "Empty Chat"})
    session_id = s_res.json()["id"]

    res = client.get(f"/sessions/{session_id}/messages")
    assert res.status_code == 200
    assert res.json() == []


def test_get_messages_not_found_session(client):
    res = client.get("/sessions/00000000-0000-0000-0000-000000000000/messages")
    assert res.status_code == 404


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "dependencies" in data
    assert "active_provider" in data
    assert "active_model" in data


def test_config_endpoint(client):
    res = client.get("/config")
    assert res.status_code == 200
    data = res.json()
    assert "active_provider" in data
    assert "active_model" in data
    assert "ollama_fallback" in data
