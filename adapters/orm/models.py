from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from adapters.persistence import Base

media_genres = Table(
    "media_genres",
    Base.metadata,
    Column(
        "media_id",
        Integer,
        ForeignKey("media.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "genre_id",
        Integer,
        ForeignKey("genres.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class MediaModel(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    kind = Column(String, nullable=False)
    year = Column(Integer, nullable=True)
    status = Column(String, nullable=True)
    owner_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    rating = Column(Float, nullable=True)

    favorite = Column(Boolean, nullable=False, default=False)

    genres = relationship("GenreModel", secondary=media_genres, back_populates="media")


class GenreModel(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)

    media = relationship("MediaModel", secondary=media_genres, back_populates="genres")


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
