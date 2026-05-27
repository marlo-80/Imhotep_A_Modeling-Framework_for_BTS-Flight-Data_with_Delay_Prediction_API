from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_predict_endpoint():
    response = client.post("/predict", json={
        "origin": "JFK",
        "dest": "LAX",
        "crs_dep_time": 900,
        "distance": 2475
    })
    assert response.status_code == 200
    assert "prediction" in response.json()