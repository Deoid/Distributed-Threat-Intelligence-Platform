import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from services.api_server.app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_api_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["service"] == "api_server"
    assert data["status"] == "healthy"

def test_api_stats_overview(client):
    response = client.get("/api/stats/overview")
    assert response.status_code == 200
    data = response.get_json()
    assert "total_events" in data
    assert "unique_ips" in data

def test_api_clustering(client):
    response = client.get("/api/clustering")
    assert response.status_code == 200
    data = response.get_json()
    assert "status" in data

def test_api_blocklist_lifecycle(client):
    test_ip = "203.0.113.199"
    # 1. Add to blocklist
    post_res = client.post("/api/blocklist", json={
        "ip": test_ip,
        "reason": "Test unit block",
        "threat_score": 99,
        "cluster_profile": "Test Profile"
    })
    assert post_res.status_code == 201

    # 2. Get blocklist
    get_res = client.get("/api/blocklist")
    assert get_res.status_code == 200
    items = get_res.get_json()["blocklist"]
    assert any(b["ip"] == test_ip for b in items)

    # 3. Export blocklist as iptables
    export_res = client.get("/api/blocklist/export?format=iptables")
    assert export_res.status_code == 200
    assert test_ip in export_res.get_data(as_text=True)

    # 4. Remove from blocklist
    del_res = client.delete(f"/api/blocklist/{test_ip}")
    assert del_res.status_code == 200
