import time
from collections.abc import Callable
from threading import Lock

from fastapi import Request, status
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.schemas.common import ApiResponse


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, tuple[float, int]] = {}
        self._lock = Lock()

    def hit(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int, int]:
        now = time.time()

        with self._lock:
            window_start, count = self._buckets.get(key, (now, 0))
            if now - window_start >= window_seconds:
                window_start, count = now, 0

            if count >= limit:
                retry_after = max(1, int(window_seconds - (now - window_start)))
                return False, 0, retry_after

            count += 1
            self._buckets[key] = (window_start, count)
            remaining = max(0, limit - count)
            reset_after = max(1, int(window_seconds - (now - window_start)))
            self._cleanup(now, window_seconds)
            return True, remaining, reset_after

    def _cleanup(self, now: float, window_seconds: int) -> None:
        if len(self._buckets) < 1000:
            return

        expired_keys = [
            key
            for key, (window_start, _count) in self._buckets.items()
            if now - window_start >= window_seconds
        ]
        for key in expired_keys:
            self._buckets.pop(key, None)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        rules: dict[str, tuple[int, int]],
    ) -> None:
        super().__init__(app)
        self.rules = rules
        self.limiter = InMemoryRateLimiter()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        rule = self.rules.get(request.url.path)
        if rule is None:
            return await call_next(request)

        limit, window_seconds = rule
        client_ip = self._get_client_ip(request)
        allowed, remaining, reset_after = self.limiter.hit(
            key=f"{client_ip}:{request.url.path}",
            limit=limit,
            window_seconds=window_seconds,
        )

        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_after),
        }

        if not allowed:
            headers["Retry-After"] = str(reset_after)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=ApiResponse(
                    success=False,
                    message="Too many requests. Please try again later.",
                    data=None,
                ).model_dump(),
                headers=headers,
            )

        response = await call_next(request)
        response.headers.update(headers)
        return response

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        if request.client and request.client.host:
            return request.client.host
        return "unknown"
