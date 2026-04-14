"""
Cache Module — In-Memory Redis Mock
To switch to real Redis, replace CacheService with:
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    # then use r.get(key), r.setex(key, ttl, value)
"""
import time
import json
from typing import Optional

class CacheService:
    """Thread-safe in-memory cache that mimics Redis get/set/delete with TTL support."""
    
    def __init__(self):
        self._store: dict = {}  # key -> (value, expires_at)
    
    def get(self, key: str) -> Optional[dict]:
        if key not in self._store:
            return None
        value, expires_at = self._store[key]
        if expires_at and time.time() > expires_at:
            del self._store[key]
            print(f"[CACHE] MISS (expired): {key}")
            return None
        print(f"[CACHE] HIT: {key}")
        return json.loads(value)
    
    def set(self, key: str, value: dict, ttl_seconds: int = 60):
        expires_at = time.time() + ttl_seconds
        self._store[key] = (json.dumps(value, default=str), expires_at)
        print(f"[CACHE] SET: {key} (TTL={ttl_seconds}s)")
    
    def delete(self, key: str):
        if key in self._store:
            del self._store[key]
            print(f"[CACHE] INVALIDATED: {key}")
    
    def delete_pattern(self, prefix: str):
        keys_to_delete = [k for k in self._store if k.startswith(prefix)]
        for k in keys_to_delete:
            del self._store[k]
            print(f"[CACHE] INVALIDATED: {k}")

# Singleton cache instance
cache = CacheService()
