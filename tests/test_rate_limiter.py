from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.rate_limiter import InMemoryRateLimiter, RateLimitMiddleware


def test_in_memory_rate_limiter_blocks_after_limit():
    limiter = InMemoryRateLimiter()

    first = limiter.hit("127.0.0.1:/auth/login", limit=2, window_seconds=60)
    second = limiter.hit("127.0.0.1:/auth/login", limit=2, window_seconds=60)
    third = limiter.hit("127.0.0.1:/auth/login", limit=2, window_seconds=60)

    assert first[0] is True
    assert second[0] is True
    assert third[0] is False
    assert third[2] >= 1


def test_rate_limit_middleware_returns_429_after_limit():
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        rules={"/api/v1/auth/login": (1, 60)},
    )

    @app.post("/api/v1/auth/login")
    async def login():
        return {"ok": True}

    client = TestClient(app)

    first = client.post("/api/v1/auth/login")
    second = client.post("/api/v1/auth/login")

    assert first.status_code == 200
    assert first.headers["X-RateLimit-Limit"] == "1"
    assert first.headers["X-RateLimit-Remaining"] == "0"
    assert second.status_code == 429
    assert second.json()["message"] == "Too many requests. Please try again later."
    assert second.headers["Retry-After"]
