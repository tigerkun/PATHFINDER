from __future__ import annotations

import time
from dataclasses import dataclass

try:
    import redis  # type: ignore
except ImportError:  # pragma: no cover - optional dependency at runtime
    redis = None


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after: int


class MemoryRateLimiter:
    def __init__(self, window_seconds: int, max_requests: int, store: dict[str, list[float]]):
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self.store = store

    def check(self, client_id: str) -> RateLimitResult:
        now = time.time()
        window_start = now - self.window_seconds
        timestamps = [t for t in self.store.get(client_id, []) if t >= window_start]
        is_allowed = len(timestamps) < self.max_requests
        if is_allowed:
            timestamps.append(now)
        self.store[client_id] = timestamps
        retry_after = self._compute_retry_after(now, timestamps)
        remaining = max(0, self.max_requests - len(timestamps))
        return RateLimitResult(allowed=is_allowed, remaining=remaining, retry_after=retry_after)

    def _compute_retry_after(self, now: float, timestamps: list[float]) -> int:
        if not timestamps:
            return self.window_seconds
        oldest = timestamps[0]
        return max(1, int(self.window_seconds - (now - oldest)))


class RedisRateLimiter:
    def __init__(self, redis_url: str, window_seconds: int, max_requests: int, key_prefix: str = "pf:rl"):
        if redis is None:
            raise RuntimeError("Redis mode requires 'redis' package to be installed.")
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self.key_prefix = key_prefix
        self.client = redis.Redis.from_url(redis_url, decode_responses=True)

    def check(self, client_id: str) -> RateLimitResult:
        key = self._key(client_id)
        current_count = int(self.client.incr(key))
        if current_count == 1:
            self.client.expire(key, self.window_seconds)
        ttl = int(self.client.ttl(key))
        retry_after = self.window_seconds if ttl < 0 else max(1, ttl)
        is_allowed = current_count <= self.max_requests
        remaining = max(0, self.max_requests - current_count)
        return RateLimitResult(allowed=is_allowed, remaining=remaining, retry_after=retry_after)

    def _key(self, client_id: str) -> str:
        return f"{self.key_prefix}:{client_id}"
