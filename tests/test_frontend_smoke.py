import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check_endpoint():
    """Verify backend health endpoint returns ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_static_frontend_index_serving():
    """Verify FastAPI serves index.html at root '/'."""
    response = client.get("/")
    assert response.status_code == 200
    assert "<title>Enterprise AI Research Platform</title>" in response.text
    assert "MODUS AI" in response.text

def test_static_frontend_css_and_js_serving():
    """Verify FastAPI serves CSS and JS static assets."""
    css_res = client.get("/css/styles.css")
    assert css_res.status_code == 200
    assert "Scrollbars" in css_res.text or "prose" in css_res.text

    js_res = client.get("/js/app.js")
    assert js_res.status_code == 200
    assert "API_BASE_URL" in js_res.text

def test_research_api_flow_smoke():
    """Smoke test creating research topic and retrieving status."""
    post_res = client.post("/api/research", json={"topic": "Smoke Test Topic"})
    assert post_res.status_code == 200
    data = post_res.json()
    assert "id" in data
    assert data["topic"] == "Smoke Test Topic"
    assert data["status"] in ["processing", "awaiting_approval"]

    topic_id = data["id"]
    get_res = client.get(f"/api/research/{topic_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["id"] == topic_id
