import json
import time
import socket
import logging
from typing import Optional, Any
from collections import deque
from threading import Lock

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

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

class RedisClient:
    def __init__(self):
        self.client = None
        self.is_connected = False
        self._memory_cache = {}
        self._memory_cache_expiry = {}
        self._memory_queues = {}
        self._lock = Lock()
        self._init_connection()

    def _init_connection(self):
        if REDIS_AVAILABLE and is_socket_open(Config.REDIS_HOST, Config.REDIS_PORT, timeout=0.2):
            try:
                r = redis.Redis(
                    host=Config.REDIS_HOST,
                    port=Config.REDIS_PORT,
                    password=Config.REDIS_PASSWORD,
                    socket_connect_timeout=1,
                    decode_responses=True
                )
                r.ping()
                self.client = r
                self.is_connected = True
                logger.info("Connected to Redis server.")
                return
            except Exception as e:
                logger.warning(f"Could not connect to Redis ({e}). Falling back to in-memory store.")
        else:
            logger.info("Redis server not reachable. Using fast in-memory store.")
        self.is_connected = False

    def push_event(self, queue_name: str, event_data: dict) -> bool:
        serialized = json.dumps(event_data)
        if self.is_connected and self.client:
            try:
                self.client.rpush(queue_name, serialized)
                return True
            except Exception as e:
                logger.error(f"Redis rpush failed: {e}")
        with self._lock:
            if queue_name not in self._memory_queues:
                self._memory_queues[queue_name] = deque()
            self._memory_queues[queue_name].append(serialized)
        return True

    def pop_event(self, queue_name: str, timeout: int = 1) -> Optional[dict]:
        if self.is_connected and self.client:
            try:
                item = self.client.blpop(queue_name, timeout=timeout)
                if item:
                    return json.loads(item[1])
            except Exception as e:
                logger.error(f"Redis blpop failed: {e}")

        with self._lock:
            if queue_name in self._memory_queues and len(self._memory_queues[queue_name]) > 0:
                raw = self._memory_queues[queue_name].popleft()
                return json.loads(raw)
        return None

    def get_cache(self, key: str) -> Optional[Any]:
        if self.is_connected and self.client:
            try:
                val = self.client.get(key)
                if val:
                    return json.loads(val)
                return None
            except Exception as e:
                logger.error(f"Redis get failed: {e}")

        with self._lock:
            if key in self._memory_cache:
                expiry = self._memory_cache_expiry.get(key)
                if expiry and time.time() > expiry:
                    del self._memory_cache[key]
                    del self._memory_cache_expiry[key]
                    return None
                return self._memory_cache[key]
        return None

    def set_cache(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        ttl = ttl or Config.REDIS_CACHE_TTL
        serialized = json.dumps(value)
        if self.is_connected and self.client:
            try:
                self.client.setex(key, ttl, serialized)
                return True
            except Exception as e:
                logger.error(f"Redis setex failed: {e}")

        with self._lock:
            self._memory_cache[key] = value
            self._memory_cache_expiry[key] = time.time() + ttl
        return True

    def invalidate_cache_pattern(self, pattern: str = "stats:*") -> None:
        if self.is_connected and self.client:
            try:
                keys = self.client.keys(pattern)
                if keys:
                    self.client.delete(*keys)
            except Exception as e:
                logger.error(f"Redis invalidate failed: {e}")

        with self._lock:
            prefix = pattern.replace("*", "")
            keys_to_del = [k for k in self._memory_cache.keys() if k.startswith(prefix)]
            for k in keys_to_del:
                del self._memory_cache[k]
                if k in self._memory_cache_expiry:
                    del self._memory_cache_expiry[k]

redis_client = RedisClient()
