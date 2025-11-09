from typing import List, Optional

from sqlalchemy.orm import Session

from adapters.orm.models import GenreModel, MediaModel
from domain.constants import Status
from domain.entities import Media as DomainMedia
from domain.repositories import MediaRepository


class MediaRepositorySQLAlchemy(MediaRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, m: MediaModel) -> DomainMedia:
        genres = [g.name for g in (m.genres or [])]
        status_enum = Status(m.status) if m.status is not None else None
        return DomainMedia(
            id=m.id,
            title=m.title,
            kind=m.kind,
            year=m.year,
            status=status_enum,
            owner_id=m.owner_id,
            created_at=m.created_at,
            rating=m.rating,
            genres=genres,
            favorite=bool(m.favorite),
        )

    def _get_or_create_genre(self, name: str) -> GenreModel:
        g = self.session.query(GenreModel).filter(GenreModel.name == name).first()
        if g:
            return g
        g = GenreModel(name=name)
        self.session.add(g)
        self.session.flush()
        return g

    def _apply_genres_to_model(self, model: MediaModel, genre_names: Optional[List[str]]):
        model.genres = []
        if not genre_names:
            return
        for name in genre_names:
            gm = self._get_or_create_genre(name)
            model.genres.append(gm)

    def _from_domain(self, dm: DomainMedia, model: Optional[MediaModel] = None) -> MediaModel:
        if model is None:
            model = MediaModel()
        model.title = dm.title
        model.kind = dm.kind
        model.year = dm.year
        model.status = dm.status.value if dm.status is not None else None
        model.owner_id = dm.owner_id
        model.rating = float(dm.rating) if dm.rating is not None else None
        model.favorite = bool(dm.favorite)
        self._apply_genres_to_model(model, dm.genres)
        return model

    def add(self, media: DomainMedia) -> DomainMedia:
        model = self._from_domain(media)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def get(self, media_id: int) -> Optional[DomainMedia]:
        model = self.session.query(MediaModel).filter(MediaModel.id == media_id).first()
        return self._to_domain(model) if model else None

    def list(
        self, kind: Optional[str] = None, status: Optional[str] = None, limit: int = 100
    ) -> List[DomainMedia]:
        q = self.session.query(MediaModel)
        if kind:
            q = q.filter(MediaModel.kind == kind)
        if status:
            q = q.filter(MediaModel.status == status)
        q = q.order_by(MediaModel.id.desc()).limit(limit)
        return [self._to_domain(m) for m in q.all()]

    def update(self, media: DomainMedia) -> DomainMedia:
        model = self.session.query(MediaModel).filter(MediaModel.id == media.id).first()
        if not model:
            raise ValueError("media not found")
        model = self._from_domain(media, model)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def delete(self, media_id: int) -> None:
        model = self.session.query(MediaModel).filter(MediaModel.id == media_id).first()
        if not model:
            raise ValueError("media not found")
        self.session.delete(model)
        self.session.commit()
