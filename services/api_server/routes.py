import logging
import random
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, Response

from services.common.config import Config
from services.common.db import db
from services.common.redis_client import redis_client
from services.enricher.geoip import resolve_geoip
from services.enricher.worker import enrich_event
from services.api_server.clustering import run_kmeans_clustering

logger = logging.getLogger("api_server")
api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "service": "api_server",
        "status": "healthy",
        "database_type": "postgres" if db.use_postgres else "sqlite",
        "redis_connected": redis_client.is_connected,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200

@api_bp.route("/stats/overview", methods=["GET"])
def stats_overview():
    cached = redis_client.get_cache("stats:overview")
    if cached:
        return jsonify({**cached, "source": "redis_cache"}), 200

    try:
        total_events = (db.execute_query("SELECT COUNT(*) as c FROM threat_events")[0] or {}).get("c", 0)
        unique_ips = (db.execute_query("SELECT COUNT(DISTINCT source_ip) as c FROM threat_events")[0] or {}).get("c", 0)
        countries_count = (db.execute_query("SELECT COUNT(DISTINCT country) as c FROM threat_events WHERE country != 'Unknown'")[0] or {}).get("c", 0)
        high_severity = (db.execute_query("SELECT COUNT(*) as c FROM threat_events WHERE threat_score >= 70")[0] or {}).get("c", 0)
        blocked_count = (db.execute_query("SELECT COUNT(*) as c FROM blocklist")[0] or {}).get("c", 0)

        # Average threat score
        avg_score_res = db.execute_query("SELECT AVG(threat_score) as avg_score FROM threat_events")
        avg_threat = round(float((avg_score_res[0] or {}).get("avg_score") or 0), 1)

        data = {
            "total_events": total_events,
            "unique_ips": unique_ips,
            "countries_count": countries_count,
            "high_severity_count": high_severity,
            "blocked_ips_count": blocked_count,
            "average_threat_score": avg_threat
        }
        redis_client.set_cache("stats:overview", data, ttl=Config.REDIS_CACHE_TTL)
        return jsonify({**data, "source": "database"}), 200
    except Exception as e:
        logger.error(f"Error fetching stats overview: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route("/stats/timeline", methods=["GET"])
def stats_timeline():
    cached = redis_client.get_cache("stats:timeline")
    if cached:
        return jsonify({**cached, "source": "redis_cache"}), 200

    try:
        # Fetch timestamp distribution (group by hours or days)
        rows = db.execute_query("""
            SELECT substr(timestamp, 1, 13) as hour_bucket, COUNT(*) as count
            FROM threat_events
            WHERE timestamp IS NOT NULL
            GROUP BY hour_bucket
            ORDER BY hour_bucket DESC
            LIMIT 24
        """)

        labels = []
        counts = []
        for r in reversed(rows):
            bucket = r.get("hour_bucket") or ""
            # Format nicely
            labels.append(bucket.replace("T", " ") + ":00" if "T" in bucket else bucket)
            counts.append(r.get("count", 0))

        data = {
            "labels": labels,
            "series": counts
        }
        redis_client.set_cache("stats:timeline", data, ttl=Config.REDIS_CACHE_TTL)
        return jsonify({**data, "source": "database"}), 200
    except Exception as e:
        logger.error(f"Error fetching timeline: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route("/stats/top-ips", methods=["GET"])
def stats_top_ips():
    cached = redis_client.get_cache("stats:top-ips")
    if cached:
        return jsonify({**cached, "source": "redis_cache"}), 200

    try:
        rows = db.execute_query("""
            SELECT ip, total_events, targeted_ports_count, usernames_tried_count,
                   request_rate, threat_score, country, country_code, asn, cluster_name
            FROM ip_profiles
            ORDER BY total_events DESC, threat_score DESC
            LIMIT 10
        """)
        data = {"top_ips": rows}
        redis_client.set_cache("stats:top-ips", data, ttl=Config.REDIS_CACHE_TTL)
        return jsonify({**data, "source": "database"}), 200
    except Exception as e:
        logger.error(f"Error fetching top IPs: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route("/stats/countries", methods=["GET"])
def stats_countries():
    cached = redis_client.get_cache("stats:countries")
    if cached:
        return jsonify({**cached, "source": "redis_cache"}), 200

    try:
        rows = db.execute_query("""
            SELECT country, country_code, COUNT(*) as event_count
            FROM threat_events
            WHERE country != 'Unknown'
            GROUP BY country, country_code
            ORDER BY event_count DESC
            LIMIT 10
        """)
        data = {"countries": rows}
        redis_client.set_cache("stats:countries", data, ttl=Config.REDIS_CACHE_TTL)
        return jsonify({**data, "source": "database"}), 200
    except Exception as e:
        logger.error(f"Error fetching countries: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route("/stats/ports", methods=["GET"])
def stats_ports():
    cached = redis_client.get_cache("stats:ports")
    if cached:
        return jsonify({**cached, "source": "redis_cache"}), 200

    try:
        rows = db.execute_query("""
            SELECT destination_port as port, protocol, COUNT(*) as count
            FROM threat_events
            GROUP BY destination_port, protocol
            ORDER BY count DESC
            LIMIT 8
        """)
        data = {"ports": rows}
        redis_client.set_cache("stats:ports", data, ttl=Config.REDIS_CACHE_TTL)
        return jsonify({**data, "source": "database"}), 200
    except Exception as e:
        logger.error(f"Error fetching ports: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route("/events", methods=["GET"])
def get_events():
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    search = request.args.get("search", "").strip()

    limit = min(max(1, limit), 200)

    try:
        if search:
            query = """
                SELECT id, timestamp, source_ip, honeypot_type, protocol,
                       destination_port, username, raw_payload, country,
                       country_code, city, asn, isp, threat_score, enriched
                FROM threat_events
                WHERE source_ip LIKE ? OR country LIKE ? OR username LIKE ? OR honeypot_type LIKE ?
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            """
            s = f"%{search}%"
            events = db.execute_query(query, (s, s, s, s, limit, offset))
        else:
            query = """
                SELECT id, timestamp, source_ip, honeypot_type, protocol,
                       destination_port, username, raw_payload, country,
                       country_code, city, asn, isp, threat_score, enriched
                FROM threat_events
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            """
            events = db.execute_query(query, (limit, offset))

        total = (db.execute_query("SELECT COUNT(*) as c FROM threat_events")[0] or {}).get("c", 0)

        return jsonify({
            "total": total,
            "limit": limit,
            "offset": offset,
            "events": events
        }), 200
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route("/clustering", methods=["GET", "POST"])
def get_or_run_clustering():
    k = int(request.args.get("k", request.json.get("k", 4) if request.is_json else 4))
    res = run_kmeans_clustering(k=k)
    return jsonify(res), 200

@api_bp.route("/blocklist", methods=["GET", "POST"])
def manage_blocklist():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        ip = data.get("ip")
        reason = data.get("reason", "Manual block via Security Dashboard")
        threat_score = int(data.get("threat_score", 95))
        profile = data.get("cluster_profile", "Custom Block")

        if not ip:
            return jsonify({"error": "IP is required"}), 400

        now_str = datetime.now(timezone.utc).isoformat()
        try:
            if db.use_postgres:
                db.execute_commit(
                    "INSERT INTO blocklist (ip, reason, threat_score, added_at, cluster_profile) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (ip) DO NOTHING",
                    (ip, reason, threat_score, now_str, profile)
                )
            else:
                db.execute_commit(
                    "INSERT OR IGNORE INTO blocklist (ip, reason, threat_score, added_at, cluster_profile) VALUES (?, ?, ?, ?, ?)",
                    (ip, reason, threat_score, now_str, profile)
                )
            redis_client.invalidate_cache_pattern("stats:*")
            return jsonify({"status": "success", "message": f"IP {ip} added to firewall blocklist"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # GET blocklist
    try:
        rows = db.execute_query("SELECT id, ip, reason, threat_score, added_at, cluster_profile FROM blocklist ORDER BY threat_score DESC, id DESC")
        return jsonify({"blocklist": rows, "count": len(rows)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/blocklist/<ip>", methods=["DELETE"])
def remove_from_blocklist(ip: str):
    try:
        db.execute_commit("DELETE FROM blocklist WHERE ip = ?", (ip,))
        redis_client.invalidate_cache_pattern("stats:*")
        return jsonify({"status": "success", "message": f"IP {ip} unblocked"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/blocklist/export", methods=["GET"])
def export_blocklist():
    format_type = request.args.get("format", "iptables").lower()
    min_score = int(request.args.get("min_score", 0))

    rows = db.execute_query(
        "SELECT ip, reason, threat_score FROM blocklist WHERE threat_score >= ? ORDER BY threat_score DESC",
        (min_score,)
    )

    if format_type == "iptables":
        lines = [
            "# Generated by Distributed Threat Intelligence Platform Firewall Engine",
            f"# Timestamp: {datetime.now(timezone.utc).isoformat()}",
            f"# Total Rules: {len(rows)}",
            ""
        ]
        for r in rows:
            lines.append(f"iptables -A INPUT -s {r['ip']} -j DROP -m comment --comment \"Score:{r['threat_score']} - {r['reason']}\"")
        content = "\n".join(lines)
        return Response(content, mimetype="text/plain", headers={"Content-Disposition": "attachment;filename=threatintel_iptables.rules"})

    elif format_type == "ufw":
        lines = [
            "# UFW rules generated by Threat Intelligence Platform",
            ""
        ]
        for r in rows:
            lines.append(f"ufw deny from {r['ip']} comment \"ThreatScore {r['threat_score']}\"")
        content = "\n".join(lines)
        return Response(content, mimetype="text/plain", headers={"Content-Disposition": "attachment;filename=threatintel_ufw.sh"})

    elif format_type == "plain":
        content = "\n".join(r["ip"] for r in rows)
        return Response(content, mimetype="text/plain", headers={"Content-Disposition": "attachment;filename=threat_ips.txt"})

    else: # json
        return jsonify({"rules": rows, "count": len(rows)})

@api_bp.route("/events/seed", methods=["POST"])
def seed_dataset():
    """Generates realistic honeypot attack telemetry to seed fresh databases"""
    from services.collector.app import MOCK_IPS, MOCK_USERNAMES, MOCK_PASSWORDS, MOCK_PORTS, MOCK_HONEYPOTS

    count = int(request.args.get("count", 40))
    count = min(count, 150)

    now = datetime.now(timezone.utc)
    seeded_count = 0

    for i in range(count):
        ip = random.choice(MOCK_IPS)
        # distribute timestamps across the past 24 hours
        time_offset = timedelta(minutes=random.randint(5, 1440))
        event_time = (now - time_offset).isoformat()
        port = random.choice(MOCK_PORTS)
        honeypot = random.choice(MOCK_HONEYPOTS)
        username = random.choice(MOCK_USERNAMES) if random.random() > 0.2 else None
        password = random.choice(MOCK_PASSWORDS) if username else None
        
        insert_query = """
        INSERT INTO threat_events (
            timestamp, source_ip, honeypot_type, protocol, destination_port,
            username, password, raw_payload, enriched, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            event_time, ip, honeypot, "TCP", port,
            username, password, f"SYN scan / auth attempt {username}:{password}", False, event_time
        )
        eid = db.execute_insert(insert_query, params)
        enrich_event({
            "event_id": eid,
            "source_ip": ip,
            "honeypot_type": honeypot,
            "destination_port": port,
            "username": username,
            "raw_payload": f"SYN scan / auth attempt {username}:{password}",
            "timestamp": event_time
        })
        seeded_count += 1

    # Run K-Means right after seeding to create initial clusters
    run_kmeans_clustering(k=4)
    redis_client.invalidate_cache_pattern("stats:*")

    return jsonify({
        "status": "success",
        "message": f"Seeded and enriched {seeded_count} realistic threat events across honeypots."
    }), 201
