from fastapi.testclient import TestClient

from app.main import app
from app.middleware.rate_limiter import SimpleRateLimiterMiddleware

client = TestClient(app)


def _find_rate_limiter(obj):
    if isinstance(obj, SimpleRateLimiterMiddleware):
        return obj
    for attr in ("app", "inner_app", "__wrapped__"):
        nxt = getattr(obj, attr, None)
        if nxt is not None:
            found = _find_rate_limiter(nxt)
            if found:
                return found
    return None


def _reset_rate_limiter():
    limiter = None
    try:
        limiter = _find_rate_limiter(app.middleware_stack)
    except Exception:
        limiter = None
    if limiter:
        limiter._reset()


def test_rfc7807_error():
    _reset_rate_limiter()
    r = client.get("/nonexistent-path")
    assert r.status_code == 404
    body = r.json()
    assert (
        "type" in body
        and "title" in body
        and "status" in body
        and "detail" in body
        and "correlation_id" in body
    )
    assert body["status"] == 404


def test_validation_rejects_rating_if_not_done():
    _reset_rate_limiter()
    payload = {"title": "Bad Rating", "kind": "movie", "rating": 7.5}
    r = client.post("/media", json=payload)
    assert r.status_code in (400, 422)
    body = r.json()
    assert (
        body.get("title")
        in (
            "ValidationError",
            "ValueError",
            "BadRequest",
            "ValidationError",
        )
        or "Validation" in str(body.get("detail", ""))
        or "errors" in body
    )


def test_rate_limit_block():
    _reset_rate_limiter()
    got_429 = False
    for _ in range(200):
        r = client.get("/media")
        if r.status_code == 429:
            got_429 = True
            body = r.json()
            assert body.get("title") == "TooManyRequests"
            break

    assert got_429
