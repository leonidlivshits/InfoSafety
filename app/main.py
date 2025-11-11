import asyncio
import logging
import secrets
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from adapters.orm.media_repository import MediaRepositorySQLAlchemy
from adapters.orm.user_repository import UserRepositorySQLAlchemy
from adapters.persistence import Base, engine, get_db
from app.backup_scheduler import _run_backup_once, lifespan
from app.config import settings
from app.errors import (
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.middleware.rate_limiter import SimpleRateLimiterMiddleware
from domain.entities import User as DomainUser
from schemas.media import MediaCreate, MediaRead, MediaUpdate
from usecases.media_service import MediaService

app = FastAPI(title="Media Catalog", lifespan=lifespan)


logger = logging.getLogger(__name__)

app.add_middleware(SimpleRateLimiterMiddleware)

if not hasattr(app.state, "backup_lock"):
    app.state.backup_lock = asyncio.Lock()
if not hasattr(app.state, "backup_failures"):
    app.state.backup_failures = 0
if not hasattr(app.state, "backup_last_run"):
    app.state.backup_last_run = 0.0


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


def get_media_service(db: Session = Depends(get_db)) -> MediaService:
    repo = MediaRepositorySQLAlchemy(db)
    svc = MediaService(repo)
    return svc


@app.exception_handler(StarletteHTTPException)
async def _http_exception_handler(request: Request, exc: StarletteHTTPException):
    return await http_exception_handler(request, exc)


app.add_exception_handler(HTTPException, _http_exception_handler)


@app.exception_handler(RequestValidationError)
async def _validation_exception_handler(request: Request, exc: RequestValidationError):
    return await validation_exception_handler(request, exc)


@app.exception_handler(Exception)
async def _generic_exception_handler(request: Request, exc: Exception):
    return await generic_exception_handler(request, exc)


@app.post("/users", status_code=201)
def create_user(username: str, email: Optional[str] = None, db: Session = Depends(get_db)):
    user_repo = UserRepositorySQLAlchemy(db)
    existing = user_repo.get_by_username(username)
    if existing:
        raise HTTPException(status_code=400, detail="username exists")
    domain_user = DomainUser(id=None, username=username, email=email)
    created = user_repo.add(domain_user)
    return {"id": created.id, "username": created.username}


def _parse_actor_id(x_actor_id: Optional[str]) -> Optional[int]:
    if x_actor_id is None:
        return None
    try:
        return int(x_actor_id)
    except (ValueError, TypeError):
        return None


@app.post("/media", response_model=MediaRead, status_code=201)
def create_media(
    payload: MediaCreate,
    svc: MediaService = Depends(get_media_service),
    x_actor_id: Optional[str] = Header(None, alias="X-Actor-Id"),
):
    try:
        owner_from_header = _parse_actor_id(x_actor_id)
        owner = payload.owner_id if payload.owner_id is not None else owner_from_header
        media = svc.create(
            title=payload.title,
            kind=payload.kind,
            year=payload.year,
            status=payload.status,
            rating=payload.rating,
            genres=payload.genres,
            favorite=payload.favorite,
            owner_id=owner,
        )
        return media
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/media", response_model=list[MediaRead])
def list_media(
    kind: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    svc: MediaService = Depends(get_media_service),
):
    return svc.list(kind=kind, status=status, limit=limit)


@app.get("/media/{media_id}", response_model=MediaRead)
def get_media(media_id: int, svc: MediaService = Depends(get_media_service)):
    item = svc.get(media_id)
    if not item:
        raise HTTPException(status_code=404, detail="media not found")
    return item


@app.put("/media/{media_id}", response_model=MediaRead)
def update_media(
    media_id: int,
    payload: MediaUpdate,
    svc: MediaService = Depends(get_media_service),
    x_actor_id: Optional[str] = Header(None, alias="X-Actor-Id"),
):
    try:
        actor = _parse_actor_id(x_actor_id)
        updated = svc.update(media_id, actor_id=actor, **payload.dict(exclude_unset=True))
        return updated
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404 if "not found" in str(e) else 400, detail=str(e))


@app.delete("/media/{media_id}")
def delete_media(
    media_id: int,
    svc: MediaService = Depends(get_media_service),
    x_actor_id: Optional[str] = Header(None, alias="X-Actor-Id"),
):
    try:
        actor = _parse_actor_id(x_actor_id)
        svc.delete(media_id, actor_id=actor)
        return {"ok": True}
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def _is_valid_admin_token(token: str) -> bool:
    for t in settings.BACKUP_ADMIN_TOKENS:
        if secrets.compare_digest(token, t):
            return True
    return False


def require_backup_admin(x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    if not settings.BACKUP_ADMIN_TOKENS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="backup not allowed")
    if x_admin_token is None or not _is_valid_admin_token(x_admin_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return True


@app.post("/backup/run")
async def run_backup_endpoint(authorized: bool = Depends(require_backup_admin)):
    if not settings.BACKUP_ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="backup disabled")

    lock: asyncio.Lock = app.state.backup_lock
    if lock.locked():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="backup already running"
        )

    async with lock:
        try:
            out = await _run_backup_once()
            app.state.backup_failures = 0
            app.state.backup_last_run = asyncio.get_event_loop().time()
            logger.info("manual backup succeeded: %s", out)
            return {"ok": True, "path": out}
        except Exception as exc:
            app.state.backup_failures += 1
            logger.exception("Manual backup failed")
            if app.state.backup_failures >= settings.MAX_CONSECUTIVE_FAILURES:
                logger.error(
                    "backup: reached max consecutive failures (%s), "
                    "disabling future manual backups",
                    settings.MAX_CONSECUTIVE_FAILURES,
                )
                app.state.backup_disabled_due_errors = True
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="backup failed"
            ) from exc


@app.post("/auth/validate")
def auth_validate(x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    if not settings.BACKUP_ADMIN_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="no admin tokens configured"
        )
    if x_admin_token is None or not _is_valid_admin_token(x_admin_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid token")
    return {"ok": True, "is_admin": True}


@app.get("/health")
def health():
    return {"status": "ok"}
