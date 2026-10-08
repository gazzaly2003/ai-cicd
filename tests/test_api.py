from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)


def test_health():
    assert c.get("/healthz").status_code == 200


def test_predict():
    r = c.post("/predict", json={"features": [0.0] * 64})
    assert r.status_code == 200 and "prediction" in r.json()


def test_metrics():
    assert b"predict_latency_seconds" in c.get("/metrics").content