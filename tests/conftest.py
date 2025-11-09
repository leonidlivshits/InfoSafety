import sys
from pathlib import Path
from typing import Dict, Generator, List, Optional

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from adapters.persistence import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from domain.entities import Media  # noqa: E402
from usecases.media_service import MediaService  # noqa: E402


class FakeRepo:
    def __init__(self):
        self._store: Dict[int, Media] = {}
        self._next = 1

    def add(self, media: Media) -> Media:
        media.id = self._next
        self._next += 1
        self._store[media.id] = media
        return media

    def get(self, media_id: int) -> Optional[Media]:
        return self._store.get(media_id)

    def list(
        self, kind: Optional[str] = None, status: Optional[str] = None, limit: int = 100
    ) -> List[Media]:
        res = list(self._store.values())
        if kind:
            res = [m for m in res if m.kind == kind]
        if status:
            res = [
                m
                for m in res
                if (m.status.value if hasattr(m.status, "value") else m.status) == status
            ]
        return res[:limit]

    def update(self, media: Media) -> Media:
        if media.id not in self._store:
            raise ValueError("media not found")
        self._store[media.id] = media
        return media

    def delete(self, media_id: int) -> None:
        if media_id not in self._store:
            raise ValueError("media not found")
        del self._store[media_id]


@pytest.fixture
def fake_repo() -> FakeRepo:
    return FakeRepo()


@pytest.fixture
def media_service(fake_repo: FakeRepo) -> MediaService:
    return MediaService(fake_repo)


@pytest.fixture(scope="module")
def testing_session_factory():
    engine = create_engine(
        "sqlite:///file::memory:?cache=shared",
        connect_args={"check_same_thread": False, "uri": True},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(testing_session_factory) -> Generator[TestClient, None, None]:
    TestingSessionLocal = testing_session_factory

    def override_get_db():
        db: Session = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)
