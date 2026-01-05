from fastapi.testclient import TestClient
from src.api.main_poc import app


client = TestClient(app)


def test_suggest_unavailable():
    # If predictor not loaded, expect 500
    resp = client.post("/suggest", json={"text": "sample text"})
    assert resp.status_code in (200, 500)


def test_feedback_write():
    resp = client.post("/feedback", json={"text": "payment for services", "selected_account": "4000", "confidence": 0.9})
    assert resp.status_code == 200
    body = resp.json()
    assert "id" in body
