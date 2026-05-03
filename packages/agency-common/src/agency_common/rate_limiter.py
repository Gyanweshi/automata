"""Simple token-bucket rate limiter using stdlib only."""
from __future__ import annotations

import time
from threading import Lock


class RateLimiter:
    """Token-bucket rate limiter.

    Args:
        calls: Maximum number of calls allowed in the window.
        period: Time window in seconds.

    Usage:
        limiter = RateLimiter(calls=10, period=60)
        limiter.wait()   # blocks until a token is available
    """

    def __init__(self, calls: int = 10, period: float = 60.0):
        self.calls = calls
        self.period = period
        self._lock = Lock()
        self._timestamps: list[float] = []

    def wait(self) -> None:
        """Block until a request token is available."""
        with self._lock:
            now = time.monotonic()
            # Drop timestamps outside the current window
            self._timestamps = [t for t in self._timestamps if now - t < self.period]
            if len(self._timestamps) >= self.calls:
                # Sleep until oldest token expires
                sleep_for = self.period - (now - self._timestamps[0])
                if sleep_for > 0:
                    time.sleep(sleep_for)
                now = time.monotonic()
                self._timestamps = [t for t in self._timestamps if now - t < self.period]
            self._timestamps.append(time.monotonic())

    def __call__(self, fn):
        """Use as a decorator."""
        from functools import wraps

        @wraps(fn)
        def wrapper(*args, **kwargs):
            self.wait()
            return fn(*args, **kwargs)

        return wrapper


# Pre-built limiters matching platform constraints
instagram_limiter = RateLimiter(calls=200, period=3600)   # ~200/hour
apify_limiter = RateLimiter(calls=60, period=60)          # 60/min
facebook_limiter = RateLimiter(calls=200, period=3600)    # Graph API
