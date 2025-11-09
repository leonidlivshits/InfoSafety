from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from adapters.orm.media_repository import MediaRepositorySQLAlchemy
from adapters.orm.user_repository import UserRepositorySQLAlchemy
from adapters.persistence import Base, engine, get_db
from app.errors import (
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.middleware.rate_limiter import SimpleRateLimiterMiddleware
from domain.entities import User as DomainUser
from schemas.media import MediaCreate, MediaRead, MediaUpdate
from usecases.media_service import MediaService

FastAPIHTTPException = HTTPException

app = FastAPI(title="Media Catalog")
app.add_middleware(SimpleRateLimiterMiddleware)


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


app.add_exception_handler(FastAPIHTTPException, _http_exception_handler)


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


@app.get("/health")
def health():
    return {"status": "ok"}
