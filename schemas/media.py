# schemas/media.py
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from domain.constants import ALLOWED_GENRES, ALLOWED_KINDS, CURRENT_YEAR, MIN_YEAR, Status


class MediaCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str
    kind: str
    year: Optional[int] = None
    status: Optional[Status] = None
    rating: Optional[float] = None
    genres: Optional[List[str]] = None
    favorite: Optional[bool] = False
    owner_id: Optional[int] = None

    @field_validator("kind", mode="after")
    def validate_kind(cls, v):
        if v not in ALLOWED_KINDS:
            raise ValueError(f"kind must be one of {ALLOWED_KINDS}")
        return v

    @field_validator("year", mode="after")
    def validate_year(cls, v):
        if v is None:
            return v
        if v < MIN_YEAR or v > CURRENT_YEAR:
            raise ValueError(f"year must be between {MIN_YEAR} and {CURRENT_YEAR}")
        return v

    @field_validator("rating", mode="after")
    def validate_rating_range(cls, v):
        if v is None:
            return v
        if v < 0.0 or v > 10.0:
            raise ValueError("rating must be between 0.0 and 10.0")
        return v

    @field_validator("genres", mode="after")
    def validate_genres_list(cls, v):
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError("genres must be a list of strings")
        for item in v:
            if item not in ALLOWED_GENRES:
                raise ValueError(f"genre '{item}' is not allowed. Allowed: {ALLOWED_GENRES}")
        return v

    @model_validator(mode="after")
    def rating_allowed_only_if_done(self):
        if self.rating is not None:
            if self.status is None or self.status != Status.DONE:
                raise ValueError("rating is allowed only when status == 'done' (film watched)")
        return self


class MediaUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: Optional[str] = None
    kind: Optional[str] = None
    year: Optional[int] = None
    status: Optional[Status] = None
    rating: Optional[float] = None
    genres: Optional[List[str]] = None
    favorite: Optional[bool] = None

    @field_validator("kind", mode="after")
    def validate_kind(cls, v):
        if v is None:
            return v
        if v not in ALLOWED_KINDS:
            raise ValueError(f"kind must be one of {ALLOWED_KINDS}")
        return v

    @field_validator("year", mode="after")
    def validate_year(cls, v):
        if v is None:
            return v
        if v < MIN_YEAR or v > CURRENT_YEAR:
            raise ValueError(f"year must be between {MIN_YEAR} and {CURRENT_YEAR}")
        return v

    @field_validator("rating", mode="after")
    def validate_rating_range(cls, v):
        if v is None:
            return v
        if v < 0.0 or v > 10.0:
            raise ValueError("rating must be between 0.0 and 10.0")
        return v

    @field_validator("genres", mode="after")
    def validate_genres_list(cls, v):
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError("genres must be a list of strings")
        for item in v:
            if item not in ALLOWED_GENRES:
                raise ValueError(f"genre '{item}' is not allowed. Allowed: {ALLOWED_GENRES}")
        return v

    @model_validator(mode="after")
    def rating_allowed_only_if_done_partial(self):
        if self.rating is not None and self.status is not None and self.status != Status.DONE:
            raise ValueError("rating is allowed only when status == 'done' (film watched)")
        return self


class MediaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    kind: str
    year: Optional[int]
    status: Optional[Status]
    owner_id: Optional[int]
    created_at: Optional[datetime]
    rating: Optional[float]
    genres: Optional[List[str]]
    favorite: bool
