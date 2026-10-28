import time

from fastapi import HTTPException, status


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self) -> None:
        self.requests: dict[str, list[float]] = {}

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is allowed based on rate limit."""
        now = time.time()

        if key not in self.requests:
            self.requests[key] = []

        # Remove old requests outside the window
        self.requests[key] = [
            req_time
            for req_time in self.requests[key]
            if now - req_time < window_seconds
        ]

        # Check if under limit
        if len(self.requests[key]) < max_requests:
            self.requests[key].append(now)
            return True

        return False

    def get_remaining(self, key: str, max_requests: int, window_seconds: int) -> int:
        """Get remaining requests allowed."""
        now = time.time()

        if key not in self.requests:
            return max_requests

        # Remove old requests outside the window
        self.requests[key] = [
            req_time
            for req_time in self.requests[key]
            if now - req_time < window_seconds
        ]

        return max(0, max_requests - len(self.requests[key]))


# Global rate limiter instance
rate_limiter = RateLimiter()


def check_rate_limit(
    key: str,
    max_requests: int = 100,
    window_seconds: int = 3600,
    raise_exception: bool = True,
) -> bool:
    """Check rate limit for a given key."""
    is_allowed = rate_limiter.is_allowed(key, max_requests, window_seconds)

    if not is_allowed and raise_exception:
        remaining = rate_limiter.get_remaining(key, max_requests, window_seconds)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again later. Remaining: {remaining}",
            headers={
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(int(time.time()) + window_seconds),
            },
        )

    return is_allowed


def get_rate_limit_headers(
    key: str,
    max_requests: int = 100,
    window_seconds: int = 3600,
) -> dict[str, str]:
    """Get rate limit headers for response."""
    remaining = rate_limiter.get_remaining(key, max_requests, window_seconds)

    return {
        "X-RateLimit-Limit": str(max_requests),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(int(time.time()) + window_seconds),
    }
