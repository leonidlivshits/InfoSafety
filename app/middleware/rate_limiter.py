import time
from typing import Optional

from starlette.types import ASGIApp, Receive, Scope, Send


class SimpleRateLimiterMiddleware:

    def __init__(
        self,
        app: ASGIApp,
        max_requests: int = 100,
        window_seconds: int = 60,
        exempt_paths: Optional[set] = None,
    ):
        self.app = app
        self.max_requests = int(max_requests)
        self.window = int(window_seconds)
        self.exempt_paths = exempt_paths or {"/health"}
        self._store: dict[str, list[float]] = {}

    def _now(self) -> float:
        return time.time()

    def _key_for_scope(self, scope: Scope) -> str:
        client = scope.get("client")
        ip = client[0] if client and isinstance(client, (list, tuple)) else "unknown"
        path = scope.get("path", "")
        method = scope.get("method", "")
        return f"{ip}:{method}:{path}"

    def _prune(self, timestamps: list[float]) -> list[float]:
        cutoff = self._now() - self.window
        return [t for t in timestamps if t >= cutoff]

    def _reset(self) -> None:
        self._store.clear()

    reset = _reset

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in self.exempt_paths:
            await self.app(scope, receive, send)
            return

        key = self._key_for_scope(scope)
        timestamps = self._store.get(key, [])
        timestamps = self._prune(timestamps)

        if len(timestamps) >= self.max_requests:
            from starlette.responses import JSONResponse

            problem = {
                "type": "about:blank",
                "title": "TooManyRequests",
                "status": 429,
                "detail": "rate limit exceeded",
                "correlation_id": "",
            }
            await JSONResponse(status_code=429, content=problem)(scope, receive, send)
            return

        timestamps.append(self._now())
        self._store[key] = timestamps
        await self.app(scope, receive, send)
