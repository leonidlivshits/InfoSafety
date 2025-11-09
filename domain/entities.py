from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Union

from .constants import ALLOWED_GENRES, ALLOWED_KINDS, CURRENT_YEAR, MIN_YEAR, Status


@dataclass
class User:
    id: Optional[int]
    username: str
    email: Optional[str] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.username or not self.username.strip():
            raise ValueError("username must be a non-empty string")


@dataclass
class Media:
    id: Optional[int]
    title: str
    kind: str
    year: Optional[int] = None
    status: Optional[Union[Status, str]] = None
    owner_id: Optional[int] = None
    created_at: Optional[datetime] = None

    rating: Optional[float] = None
    genres: Optional[List[str]] = None
    favorite: bool = False

    def __post_init__(self):
        if not self.title or not self.title.strip():
            raise ValueError("title must be a non-empty string")

        if self.kind not in ALLOWED_KINDS:
            raise ValueError(f"kind must be one of {ALLOWED_KINDS}")

        if self.year is not None:
            if self.year < MIN_YEAR or self.year > CURRENT_YEAR:
                raise ValueError(f"year must be between {MIN_YEAR} and {CURRENT_YEAR}")

        if self.status is None:
            status_enum = None
        else:
            if isinstance(self.status, str):
                try:
                    status_enum = Status(self.status)
                except ValueError:
                    raise ValueError(f"status must be one of {[s.value for s in Status]}")
            elif isinstance(self.status, Status):
                status_enum = self.status
            else:
                try:
                    status_enum = Status(str(self.status))
                except Exception:
                    raise ValueError(f"status must be one of {[s.value for s in Status]}")
        self.status = status_enum

        if self.rating is not None:
            try:
                r = float(self.rating)
            except Exception:
                raise ValueError("rating must be a number between 0.0 and 10.0")
            if r < 0.0 or r > 10.0:
                raise ValueError("rating must be between 0.0 and 10.0")
            if self.status != Status.DONE:
                raise ValueError("rating is allowed only when film watched")

        if self.genres:
            if not isinstance(self.genres, list):
                raise ValueError("genres must be a list of strings")
            for g in self.genres:
                if g not in ALLOWED_GENRES:
                    raise ValueError(f"genre '{g}' is not allowed. Allowed: {ALLOWED_GENRES}")

        if not isinstance(self.favorite, bool):
            raise ValueError("favorite must be a boolean")
