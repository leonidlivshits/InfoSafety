import pytest

from domain.constants import Status


def test_create_with_rating_and_not_done_raises(media_service):
    svc = media_service

    with pytest.raises(ValueError):
        svc.create(title="Test", kind="movie", status=None, rating=8.0)

    with pytest.raises(ValueError):
        svc.create(title="Test", kind="movie", status=Status.TODO, rating=7.0)


def test_create_with_done_and_rating_ok_and_favorite_and_genres(media_service):
    svc = media_service

    m = svc.create(
        title="Watched",
        kind="movie",
        status=Status.DONE,
        rating=9.0,
        favorite=True,
        genres=["action", "drama"],
    )
    assert m.id is not None
    assert m.title == "Watched"
    assert m.rating == 9.0
    assert m.favorite is True
    assert isinstance(m.genres, list)
    assert "action" in m.genres


def test_update_owner_check_and_rating_rule(media_service, fake_repo):
    svc = media_service

    created = svc.create(title="ToWatch", kind="movie", status=Status.TODO, owner_id=1)
    mid = created.id

    with pytest.raises(PermissionError):
        svc.update(mid, actor_id=2, title="Hacked")

    updated = svc.update(mid, actor_id=1, status=Status.DONE)
    assert (
        hasattr(updated.status, "value") and updated.status.value == Status.DONE.value
    ) or updated.status == Status.DONE

    updated2 = svc.update(mid, actor_id=1, rating=8.5)
    assert updated2.rating == 8.5
