from fastapi.testclient import TestClient

import os
import sys


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from service.ml_server import app

client = TestClient(app)


def test_explain_delay_smoke():
    payload = {"order_id": "B9999", "note": "Gate locked; waiting for access code"}
    response = client.post("/explain_delay", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == payload["order_id"]
    assert 0.0 <= data["confidence"] <= 1.0
    assert data["label"]
