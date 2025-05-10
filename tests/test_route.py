import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.azuremain import app

client = TestClient(app)

def test_route_responds():
    response = client.post("/route", json={"trip_id": "test123"})
    assert response.status_code == 200
    data = response.json()
    assert "baseline_minutes" in data
    assert "optimized_minutes" in data
    assert "recommended_departure_offset_min" in data
