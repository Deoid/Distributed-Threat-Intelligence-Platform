import os
import sys
import logging
import random
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add root project path to sys.path so services.common can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from services.common.config import Config
from services.common.db import db
from services.common.redis_client import redis_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] (Collector) %(message)s")
logger = logging.getLogger("collector")

app = Flask(__name__)
CORS(app)

MOCK_IPS = [
    "185.220.101.5", "45.155.205.233", "193.142.146.88", "194.26.29.112",
    "195.54.160.149", "185.190.140.8", "91.240.118.242", "194.38.20.71",
    "146.70.189.155", "79.137.202.164", "198.98.57.195", "103.251.167.20",
    "42.236.10.125", "114.119.130.188", "218.92.0.188", "118.25.6.39",
    "180.163.220.59", "103.145.13.10", "185.156.73.54", "89.248.165.73",
    "195.22.126.155", "162.243.103.11", "104.244.72.115", "45.33.32.156"
]

MOCK_USERNAMES = ["root", "admin", "ubuntu", "test", "user", "guest", "oracle", "postgres", "support", "git", "ftp"]
MOCK_PASSWORDS = ["123456", "password", "root", "admin123", "toor", "12345678", "qwerty", "letmein", "default"]
MOCK_PORTS = [22, 23, 80, 443, 8080, 3389, 5900, 3306, 5432, 6379, 8443, 21]
MOCK_HONEYPOTS = ["cowrie-ssh", "cowrie-telnet", "dionaea-smb", "glastopf-web", "conpot-ics"]

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "service": "collector",
        "status": "healthy",
        "redis_connected": redis_client.is_connected,
        "database_type": "postgres" if db.use_postgres else "sqlite",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200

@app.route("/metrics", methods=["GET"])
def metrics():
    total_events = 0
    try:
        res = db.execute_query("SELECT COUNT(*) as count FROM threat_events")
        if res:
            total_events = res[0].get("count", 0)
    except Exception as e:
        logger.error(f"Failed to fetch metrics: {e}")

    return jsonify({
        "service": "collector",
        "total_events_ingested": total_events,
        "queue_name": Config.REDIS_QUEUE_KEY
    }), 200

def process_single_event(data: dict) -> dict:
    source_ip = data.get("source_ip") or data.get("src_ip")
    if not source_ip:
        raise ValueError("source_ip is required")

    honeypot_type = data.get("honeypot_type", "cowrie-ssh")
    protocol = data.get("protocol", "TCP").upper()
    destination_port = int(data.get("destination_port", 22))
    username = data.get("username")
    password = data.get("password")
    raw_payload = data.get("raw_payload", "")
    timestamp = data.get("timestamp") or datetime.now(timezone.utc).isoformat()

    # Insert into database with enriched=False
    query = """
    INSERT INTO threat_events (
        timestamp, source_ip, honeypot_type, protocol, destination_port,
        username, password, raw_payload, enriched, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        timestamp, source_ip, honeypot_type, protocol, destination_port,
        username, password, raw_payload, False, datetime.now(timezone.utc).isoformat()
    )

    event_id = db.execute_insert(query, params)

    event_payload = {
        "event_id": event_id,
        "timestamp": timestamp,
        "source_ip": source_ip,
        "honeypot_type": honeypot_type,
        "protocol": protocol,
        "destination_port": destination_port,
        "username": username,
        "password": password,
        "raw_payload": raw_payload
    }

    # Push to Redis Queue for enricher service to process
    redis_client.push_event(Config.REDIS_QUEUE_KEY, event_payload)
    return event_payload

@app.route("/ingest", methods=["POST"])
def ingest_event():
    body = request.get_json(silent=True) or {}
    
    # Handle single event or batch events
    if isinstance(body, list):
        results = []
        for item in body:
            try:
                processed = process_single_event(item)
                results.append({"status": "queued", "event_id": processed["event_id"]})
            except Exception as e:
                results.append({"status": "error", "message": str(e)})
        return jsonify({"status": "success", "processed": len(results), "items": results}), 202

    try:
        processed = process_single_event(body)
        return jsonify({
            "status": "queued",
            "message": "Honeypot event ingested and pushed to queue",
            "event": processed
        }), 202
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as ex:
        logger.exception("Error ingesting event")
        return jsonify({"error": "Internal server error", "details": str(ex)}), 500

@app.route("/simulate", methods=["POST"])
def simulate_attack():
    """Simulate realistic honeypot attack traffic (e.g., from an attacker IP or burst)"""
    body = request.get_json(silent=True) or {}
    count = int(body.get("count", 5))
    count = max(1, min(count, 100)) # clamp between 1 and 100

    target_ip = body.get("source_ip") or random.choice(MOCK_IPS)
    honeypot = body.get("honeypot_type") or random.choice(MOCK_HONEYPOTS)
    port = int(body.get("destination_port", random.choice(MOCK_PORTS)))

    generated = []
    for _ in range(count):
        payload = {
            "source_ip": target_ip,
            "honeypot_type": honeypot,
            "protocol": "TCP",
            "destination_port": port if random.random() > 0.3 else random.choice(MOCK_PORTS),
            "username": random.choice(MOCK_USERNAMES),
            "password": random.choice(MOCK_PASSWORDS),
            "raw_payload": f"SSH-2.0-OpenSSH_7.4p1 login probe; cmd: cat /etc/passwd",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        res = process_single_event(payload)
        generated.append(res)

    return jsonify({
        "status": "success",
        "simulated_events_count": len(generated),
        "source_ip": target_ip,
        "sample_event": generated[0] if generated else None
    }), 201

if __name__ == "__main__":
    logger.info(f"Starting Collector Microservice on port {Config.COLLECTOR_PORT}...")
    app.run(host="0.0.0.0", port=Config.COLLECTOR_PORT, debug=False)
