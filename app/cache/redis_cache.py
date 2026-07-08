import hashlib
import json

import redis

from app.config import settings

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True,
        )
    return _redis_client


def make_cache_key(portfolio_id: str, payload: dict) -> str:
    """Hash the request payload so cache invalidates automatically if holdings/prices change."""
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
    return f"portfolio_summary:{portfolio_id}:{digest}"


def get_cached_summary(key: str) -> dict | None:
    try:
        client = get_redis()
        raw = client.get(key)
        return json.loads(raw) if raw else None
    except redis.exceptions.RedisError:
        # Cache is an optimization, not a hard dependency — fail open.
        return None


def set_cached_summary(key: str, value: dict) -> None:
    try:
        client = get_redis()
        client.setex(key, settings.cache_ttl_seconds, json.dumps(value))
    except redis.exceptions.RedisError:
        pass
