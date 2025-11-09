import uuid
from typing import Any, Dict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def make_problem_detail(
    *,
    status: int,
    title: str,
    detail: str,
    type_: str | None = None,
    extra: Dict[str, Any] | None = None,
):
    pd = {
        "type": type_ or "about:blank",
        "title": title,
        "status": status,
        "detail": detail,
        "correlation_id": str(uuid.uuid4()),
    }
    if extra:
        pd.update(extra)
    return pd


def _sanitize_value(v: Any):
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, dict):
        return {str(k): _sanitize_value(val) for k, val in v.items()}
    if isinstance(v, (list, tuple)):
        return [_sanitize_value(x) for x in v]
    try:
        return str(v)
    except Exception:
        return repr(v)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = str(exc.detail) if exc.detail is not None else exc.__class__.__name__
    problem = make_problem_detail(
        status=exc.status_code,
        title=exc.__class__.__name__,
        detail=detail,
    )
    return JSONResponse(status_code=exc.status_code, content=problem)


async def validation_exception_handler(request: Request, exc: Exception):
    try:
        errors = exc.errors()
    except Exception:
        errors = [{"msg": str(exc)}]

    sanitized = _sanitize_value(errors)
    detail = "Validation error"
    problem = make_problem_detail(
        status=422,
        title="ValidationError",
        detail=detail,
        extra={"errors": sanitized},
    )
    return JSONResponse(status_code=422, content=problem)


async def generic_exception_handler(request: Request, exc: Exception):
    detail = "Internal server error"
    problem = make_problem_detail(
        status=500,
        title="InternalServerError",
        detail=detail,
    )
    return JSONResponse(status_code=500, content=problem)
