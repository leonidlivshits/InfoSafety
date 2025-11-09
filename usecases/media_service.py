from typing import List, Optional, Union

from domain.constants import Status
from domain.entities import Media
from domain.repositories import MediaRepository


class MediaService:

    def __init__(self, repo: MediaRepository):
        self.repo = repo

    def create(
        self,
        title: str,
        kind: str,
        year: Optional[int] = None,
        status: Optional[Union[Status, str]] = None,
        owner_id: Optional[int] = None,
        rating: Optional[float] = None,
        genres: Optional[List[str]] = None,
        favorite: Optional[bool] = False,
        actor_id: Optional[int] = None,
    ) -> Media:
        status_enum = Status(status) if status is not None else None

        if rating is not None and status_enum != Status.DONE:
            raise ValueError("rating is allowed only when film watched")

        media = Media(
            id=None,
            title=title,
            kind=kind,
            year=year,
            status=status_enum,
            owner_id=owner_id,
            rating=rating,
            genres=genres,
            favorite=bool(favorite),
        )
        return self.repo.add(media)

    def get(self, media_id: int) -> Optional[Media]:
        return self.repo.get(media_id)

    def list(
        self,
        kind: Optional[str] = None,
        status: Optional[Union[Status, str]] = None,
        limit: int = 100,
    ) -> List[Media]:
        status_value = (
            status.value
            if hasattr(status, "value")
            else (str(status) if status is not None else None)
        )
        return self.repo.list(kind=kind, status=status_value, limit=limit)

    def update(self, media_id: int, actor_id: Optional[int] = None, **fields) -> Media:
        existing = self.repo.get(media_id)
        if existing is None:
            raise ValueError("media not found")

        if actor_id is not None and existing.owner_id is not None and existing.owner_id != actor_id:
            raise PermissionError("actor is not the owner")

        title = fields.get("title", existing.title)
        kind = fields.get("kind", existing.kind)
        year = fields.get("year", existing.year)
        status_field = fields.get("status", existing.status)
        status_enum = Status(status_field) if status_field is not None else existing.status
        rating = fields.get("rating", existing.rating)
        genres = fields.get("genres", existing.genres)
        favorite = fields.get("favorite", existing.favorite)
        owner_id = (
            existing.owner_id if existing.owner_id is not None else fields.get("owner_id", None)
        )

        if rating is not None and status_enum != Status.DONE:
            raise ValueError("rating is allowed only when film watched")

        updated = Media(
            id=media_id,
            title=title,
            kind=kind,
            year=year,
            status=status_enum,
            owner_id=owner_id,
            rating=rating,
            genres=genres,
            favorite=bool(favorite),
        )
        return self.repo.update(updated)

    def delete(self, media_id: int, actor_id: Optional[int] = None) -> None:
        existing = self.repo.get(media_id)
        if existing is None:
            raise ValueError("media not found")
        if actor_id is not None and existing.owner_id is not None and existing.owner_id != actor_id:
            raise PermissionError("actor is not the owner")
        self.repo.delete(media_id)
