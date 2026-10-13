import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from services.collector.app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_collector_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["service"] == "collector"
    assert data["status"] == "healthy"

def test_collector_ingest_single(client):
    payload = {
        "source_ip": "185.220.101.5",
        "honeypot_type": "cowrie-ssh",
        "protocol": "TCP",
        "destination_port": 22,
        "username": "root",
        "password": "password123",
        "raw_payload": "SSH login attempt"
    }
    response = client.post("/ingest", json=payload)
    assert response.status_code == 202
    data = response.get_json()
    assert data["status"] == "queued"
    assert "event" in data
    assert data["event"]["source_ip"] == "185.220.101.5"

def test_collector_ingest_missing_ip(client):
    response = client.post("/ingest", json={"protocol": "TCP"})
    assert response.status_code == 400

def test_collector_simulate(client):
    response = client.post("/simulate", json={"count": 3})
    assert response.status_code == 201
    data = response.get_json()
    assert data["simulated_events_count"] == 3
