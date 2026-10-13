import os
import sys
import logging
from flask import Flask, jsonify
from flask_cors import CORS

# Add root project path to sys.path so services.common can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from services.common.config import Config
from services.common.db import db
from services.common.redis_client import redis_client
from services.api_server.routes import api_bp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] (API-Server) %(message)s")
logger = logging.getLogger("api_server")

app = Flask(__name__)
CORS(app)

app.register_blueprint(api_bp)

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "platform": "Distributed Threat Intelligence Platform",
        "version": "1.0.0",
        "services": {
            "collector": f"http://localhost:{Config.COLLECTOR_PORT}",
            "enricher": "http://localhost:5002",
            "api_server": f"http://localhost:{Config.API_PORT}"
        },
        "endpoints": [
            "/api/health",
            "/api/stats/overview",
            "/api/stats/timeline",
            "/api/stats/top-ips",
            "/api/stats/countries",
            "/api/stats/ports",
            "/api/events",
            "/api/clustering",
            "/api/blocklist",
            "/api/blocklist/export"
        ]
    })

def auto_seed_if_empty():
    try:
        count = (db.execute_query("SELECT COUNT(*) as c FROM threat_events")[0] or {}).get("c", 0)
        if count == 0:
            logger.info("Database is empty on start. Pre-populating demo honeypot attack data...")
            with app.test_client() as client:
                client.post("/api/events/seed?count=60")
    except Exception as e:
        logger.warning(f"Auto-seed skipped: {e}")

if __name__ == "__main__":
    auto_seed_if_empty()
    logger.info(f"Starting API Server on port {Config.API_PORT}...")
    app.run(host="0.0.0.0", port=Config.API_PORT, debug=False)
