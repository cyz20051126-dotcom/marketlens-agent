from fastapi.testclient import TestClient

from marketlens.api import create_app


MARGIN_QUERY = "\u745e\u5e78\u4ef7\u683c\u6218\u5bf9\u5229\u6da6\u7387\u6709\u4ec0\u4e48\u5f71\u54cd\uff1f"


def test_agent_chat_endpoint_returns_run_payload(tmp_path):
    app = create_app(
        session_dir=tmp_path / "sessions",
        search_cache_dir=tmp_path / "search_cache",
    )
    client = TestClient(app)

    response = client.post("/api/agent/chat", json={"query": MARGIN_QUERY})

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"].startswith("run_")
    assert payload["answer"]
    assert payload["trace_events"]


def test_agent_chat_endpoint_rejects_empty_query(tmp_path):
    app = create_app(
        session_dir=tmp_path / "sessions",
        search_cache_dir=tmp_path / "search_cache",
    )
    client = TestClient(app)

    response = client.post("/api/agent/chat", json={"query": "  "})

    assert response.status_code == 422


def test_agent_run_endpoint_loads_saved_run(tmp_path):
    app = create_app(
        session_dir=tmp_path / "sessions",
        search_cache_dir=tmp_path / "search_cache",
    )
    client = TestClient(app)

    created = client.post("/api/agent/chat", json={"query": MARGIN_QUERY}).json()
    loaded = client.get(f"/api/agent/runs/{created['run_id']}")

    assert loaded.status_code == 200
    assert loaded.json()["run_id"] == created["run_id"]


def test_agent_run_endpoint_rejects_missing_run(tmp_path):
    app = create_app(
        session_dir=tmp_path / "sessions",
        search_cache_dir=tmp_path / "search_cache",
    )
    client = TestClient(app)

    response = client.get("/api/agent/runs/run_missing")

    assert response.status_code == 404
