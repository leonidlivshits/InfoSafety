import os
import time
from typing import Callable, Dict, Tuple

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.errors import make_problem_detail


class SimpleRateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, **kwargs) -> None:
        super().__init__(app)
        self._ensure_init()

    def _ensure_init(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self.limit = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        self._store: Dict[str, Tuple[int, int]] = {}
        self._initialized = True

    def _get_client_key(self, request: Request) -> str:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
        client = request.client.host if request.client else "unknown"
        return client

    async def dispatch(self, request: Request, call_next: Callable):
        self._ensure_init()

        key = self._get_client_key(request)
        now = int(time.time())

        window_start, count = self._store.get(key, (now, 0))
        if now - window_start >= self.window:
            window_start, count = now, 0
        count += 1
        self._store[key] = (window_start, count)

        if count > self.limit:
            retry_after = self.window - (now - window_start)
            if retry_after < 0:
                retry_after = 0
            detail = f"Too many requests, retry after {retry_after} seconds"
            problem = make_problem_detail(status=429, title="TooManyRequests", detail=detail)
            headers = {"Retry-After": str(retry_after)}
            return JSONResponse(status_code=429, content=problem, headers=headers)

        response = await call_next(request)
        return response

    def _reset(self) -> None:
        self._ensure_init()
        self._store.clear()
