import os
import sqlite3
import socket
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from services.common.config import Config

def is_socket_open(host: str, port: int, timeout: float = 0.2) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        return True
    except Exception:
        return False

class Database:
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or Config.DATABASE_URL
        self.use_postgres = False
        self._test_connection()

    def _test_connection(self):
        if PSYCOPG2_AVAILABLE and is_socket_open(Config.POSTGRES_HOST, Config.POSTGRES_PORT, timeout=0.2):
            try:
                conn = psycopg2.connect(
                    host=Config.POSTGRES_HOST,
                    port=Config.POSTGRES_PORT,
                    dbname=Config.POSTGRES_DB,
                    user=Config.POSTGRES_USER,
                    password=Config.POSTGRES_PASSWORD,
                    connect_timeout=1
                )
                conn.close()
                self.use_postgres = True
                logger.info("Connected successfully to PostgreSQL.")
                return
            except Exception as e:
                logger.warning(f"Could not connect to PostgreSQL ({e}). Falling back to SQLite.")
        else:
            logger.info("PostgreSQL server not reachable or driver missing. Using fast SQLite.")
        self.use_postgres = False
        self._init_sqlite()

    def _get_connection(self):
        if self.use_postgres:
            return psycopg2.connect(
                host=Config.POSTGRES_HOST,
                port=Config.POSTGRES_PORT,
                dbname=Config.POSTGRES_DB,
                user=Config.POSTGRES_USER,
                password=Config.POSTGRES_PASSWORD
            )
        else:
            conn = sqlite3.connect(Config.FALLBACK_SQLITE_PATH)
            conn.row_factory = sqlite3.Row
            return conn

    def _init_sqlite(self):
        conn = sqlite3.connect(Config.FALLBACK_SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS threat_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            source_ip TEXT NOT NULL,
            honeypot_type TEXT NOT NULL,
            protocol TEXT NOT NULL,
            destination_port INTEGER NOT NULL,
            username TEXT,
            password TEXT,
            raw_payload TEXT,
            country TEXT DEFAULT 'Unknown',
            country_code TEXT DEFAULT 'XX',
            city TEXT DEFAULT 'Unknown',
            latitude REAL,
            longitude REAL,
            asn TEXT DEFAULT 'Unknown',
            isp TEXT DEFAULT 'Unknown',
            threat_score INTEGER DEFAULT 0,
            enriched INTEGER DEFAULT 0,
            created_at TEXT
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ip_profiles (
            ip TEXT PRIMARY KEY,
            total_events INTEGER DEFAULT 0,
            first_seen TEXT,
            last_seen TEXT,
            targeted_ports_count INTEGER DEFAULT 0,
            targeted_ports_list TEXT,
            usernames_tried_count INTEGER DEFAULT 0,
            request_rate REAL DEFAULT 0.0,
            threat_score INTEGER DEFAULT 0,
            country TEXT DEFAULT 'Unknown',
            country_code TEXT DEFAULT 'XX',
            asn TEXT DEFAULT 'Unknown',
            cluster_label INTEGER DEFAULT -1,
            cluster_name TEXT DEFAULT 'Unassigned',
            is_blocked INTEGER DEFAULT 0,
            block_reason TEXT
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS blocklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT UNIQUE NOT NULL,
            reason TEXT NOT NULL,
            threat_score INTEGER NOT NULL,
            added_at TEXT,
            cluster_profile TEXT
        );
        """)
        conn.commit()
        conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            if self.use_postgres:
                pg_query = query.replace("?", "%s")
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(pg_query, params)
                    if cur.description:
                        rows = cur.fetchall()
                        return [dict(r) for r in rows]
                    conn.commit()
                    return []
            else:
                cur = conn.cursor()
                cur.execute(query, params)
                if cur.description:
                    rows = cur.fetchall()
                    return [dict(r) for r in rows]
                conn.commit()
                return []
        finally:
            conn.close()

    def execute_insert(self, query: str, params: tuple = ()) -> int:
        conn = self._get_connection()
        try:
            if self.use_postgres:
                pg_query = query.replace("?", "%s")
                if "RETURNING id" not in pg_query.upper():
                    pg_query += " RETURNING id"
                with conn.cursor() as cur:
                    cur.execute(pg_query, params)
                    inserted_id = cur.fetchone()[0]
                    conn.commit()
                    return inserted_id
            else:
                cur = conn.cursor()
                cur.execute(query, params)
                inserted_id = cur.lastrowid
                conn.commit()
                return inserted_id
        finally:
            conn.close()

    def execute_commit(self, query: str, params: tuple = ()):
        conn = self._get_connection()
        try:
            if self.use_postgres:
                pg_query = query.replace("?", "%s")
                with conn.cursor() as cur:
                    cur.execute(pg_query, params)
                    conn.commit()
            else:
                cur = conn.cursor()
                cur.execute(query, params)
                conn.commit()
        finally:
            conn.close()

db = Database()
