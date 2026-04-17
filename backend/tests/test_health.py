"""
Smoke tests — verify the backend is importable and basic endpoints respond.
"""


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_sessions_start_requires_body(client):
    r = client.post("/api/sessions/start", json={})
    assert r.status_code == 422  # Pydantic validation error
