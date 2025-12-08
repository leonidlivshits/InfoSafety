import uuid

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def _make_problem(status: int, title: str, detail: str):
    return {
        "type": "about:blank",
        "title": title,
        "status": status,
        "detail": detail,
        "correlation_id": str(uuid.uuid4()),
    }


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = str(exc.detail) if exc.detail is not None else exc.__class__.__name__
    problem = _make_problem(status=exc.status_code, title=exc.__class__.__name__, detail=detail)
    return JSONResponse(status_code=exc.status_code, content=problem)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    try:
        errors = exc.errors()
        msgs = [f"{'.'.join(map(str, e.get('loc', [])))}: {e.get('msg','')}" for e in errors]
        detail = "; ".join(msgs)

    except Exception:
        detail = "validation error"
    problem = _make_problem(status=422, title="ValidationError", detail=detail)
    return JSONResponse(status_code=422, content=problem)


async def generic_exception_handler(request: Request, exc: Exception):
    detail = str(exc)
    problem = _make_problem(status=500, title="InternalServerError", detail=detail)
    return JSONResponse(status_code=500, content=problem)
