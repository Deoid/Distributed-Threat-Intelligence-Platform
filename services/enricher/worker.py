import os
import sys
import time
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Any

# Add root project path to sys.path so services.common can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from services.common.config import Config
from services.common.db import db
from services.common.redis_client import redis_client
from services.enricher.geoip import resolve_geoip

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] (Enricher) %(message)s")
logger = logging.getLogger("enricher")

HIGH_RISK_PORTS = {22, 23, 80, 443, 445, 1433, 3306, 3389, 5432, 6379, 8080, 8443}
CRITICAL_USERS = {"root", "admin", "administrator", "postgres", "oracle", "sa", "toor"}

def calculate_threat_score(event: Dict[str, Any]) -> int:
    score = 25
    username = (event.get("username") or "").lower()
    port = int(event.get("destination_port", 0))
    raw_payload = (event.get("raw_payload") or "").lower()

    if username in CRITICAL_USERS:
        score += 25
    elif username:
        score += 10

    if port in HIGH_RISK_PORTS:
        score += 20

    if any(sig in raw_payload for sig in ["/etc/passwd", "curl", "wget", "sh", "bash", "cmd.exe", "eval", "union select"]):
        score += 25

    return min(100, max(10, score))

def enrich_event(event_data: Dict[str, Any]) -> bool:
    event_id = event_data.get("event_id")
    source_ip = event_data.get("source_ip")
    if not source_ip:
        return False

    geo = resolve_geoip(source_ip)
    score = calculate_threat_score(event_data)

    # 1. Update threat_events record
    update_event_query = """
    UPDATE threat_events
    SET country = ?, country_code = ?, city = ?, latitude = ?, longitude = ?,
        asn = ?, isp = ?, threat_score = ?, enriched = ?
    WHERE id = ?
    """
    params = (
        geo["country"], geo["country_code"], geo["city"], geo["lat"], geo["lon"],
        geo["asn"], geo["isp"], score, True, event_id
    )
    db.execute_commit(update_event_query, params)

    # 2. Update or insert into ip_profiles table
    now_str = datetime.now(timezone.utc).isoformat()
    existing_profile = db.execute_query("SELECT * FROM ip_profiles WHERE ip = ?", (source_ip,))

    port_val = str(event_data.get("destination_port", ""))
    username_val = event_data.get("username")

    if existing_profile:
        prof = existing_profile[0]
        total_events = prof.get("total_events", 0) + 1
        
        # Merge ports list
        ports_set = set(filter(None, (prof.get("targeted_ports_list") or "").split(",")))
        if port_val:
            ports_set.add(port_val)
        targeted_ports_list = ",".join(sorted(ports_set))
        targeted_ports_count = len(ports_set)

        # Increment username count
        usernames_tried_count = prof.get("usernames_tried_count", 0) + (1 if username_val else 0)

        # Estimate request rate (events per minute approx)
        rate = round(total_events / 1.5, 2)
        combined_score = min(100, max(score, int(prof.get("threat_score", 0) * 0.7 + score * 0.3)))

        update_prof_query = """
        UPDATE ip_profiles
        SET total_events = ?, last_seen = ?, targeted_ports_count = ?,
            targeted_ports_list = ?, usernames_tried_count = ?, request_rate = ?,
            threat_score = ?, country = ?, country_code = ?, asn = ?
        WHERE ip = ?
        """
        db.execute_commit(update_prof_query, (
            total_events, now_str, targeted_ports_count, targeted_ports_list,
            usernames_tried_count, rate, combined_score,
            geo["country"], geo["country_code"], geo["asn"], source_ip
        ))
    else:
        insert_prof_query = """
        INSERT INTO ip_profiles (
            ip, total_events, first_seen, last_seen, targeted_ports_count,
            targeted_ports_list, usernames_tried_count, request_rate,
            threat_score, country, country_code, asn
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        db.execute_commit(insert_prof_query, (
            source_ip, 1, now_str, now_str, 1, port_val,
            1 if username_val else 0, 1.0, score,
            geo["country"], geo["country_code"], geo["asn"]
        ))

    # Auto block if score is 90+
    if score >= 90:
        db.execute_commit(
            "INSERT OR IGNORE INTO blocklist (ip, reason, threat_score, added_at, cluster_profile) VALUES (?, ?, ?, ?, ?)"
            if not db.use_postgres else
            "INSERT INTO blocklist (ip, reason, threat_score, added_at, cluster_profile) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (ip) DO NOTHING",
            (source_ip, f"Critical threat score ({score}) exceeding threshold", score, now_str, "High Severity Attacker")
        )

    return True

def process_unprocessed_db_events():
    """Fallback: process events in database that were not yet enriched"""
    try:
        events = db.execute_query(
            "SELECT id, source_ip, destination_port, username, raw_payload, timestamp FROM threat_events WHERE enriched = 0 OR enriched = FALSE LIMIT ?",
            (Config.ENRICHER_BATCH_SIZE,)
        )
        for ev in events:
            payload = {
                "event_id": ev["id"],
                "source_ip": ev["source_ip"],
                "destination_port": ev.get("destination_port", 0),
                "username": ev.get("username"),
                "raw_payload": ev.get("raw_payload", ""),
                "timestamp": ev.get("timestamp")
            }
            enrich_event(payload)
        if events:
            logger.info(f"Enriched {len(events)} batch events directly from database.")
            redis_client.invalidate_cache_pattern("stats:*")
    except Exception as e:
        logger.error(f"Error checking unprocessed events: {e}")

def run_enricher_loop():
    logger.info("Enricher worker started. Listening for honeypot events...")
    while True:
        try:
            # 1. Pop from Redis queue
            event = redis_client.pop_event(Config.REDIS_QUEUE_KEY, timeout=1)
            if event:
                enrich_event(event)
                # Invalidate stats cache so dashboard gets fresh data
                redis_client.invalidate_cache_pattern("stats:*")
            else:
                # 2. Check for backlog in DB
                process_unprocessed_db_events()
                time.sleep(Config.ENRICHER_POLL_INTERVAL)
        except Exception as e:
            logger.exception(f"Unexpected error in enricher loop: {e}")
            time.sleep(2)

def start_health_server():
    from flask import Flask, jsonify
    app = Flask("enricher_health")
    
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({
            "service": "enricher",
            "status": "healthy",
            "database_type": "postgres" if db.use_postgres else "sqlite",
            "redis_connected": redis_client.is_connected,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200

    app.run(host="0.0.0.0", port=5002, debug=False)

if __name__ == "__main__":
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    run_enricher_loop()
