import os

import pytest

from adapters.backup import safe_export_sqlite


def test_rfc7807_problem_fields_present(client):
    r = client.get("/nonexistent-path")
    assert r.status_code == 404
    body = r.json()
    assert (
        "type" in body
        and "title" in body
        and "status" in body
        and "detail" in body
        and "correlation_id" in body
    )
    assert isinstance(body["correlation_id"], str)


def test_validation_rejects_rating_if_not_done_via_api(client):
    payload = {"title": "Bad Rating", "kind": "movie", "rating": 7.5}
    r = client.post("/media", json=payload)
    assert r.status_code in (400, 422)
    body = r.json()
    assert "Validation" in body.get("detail", "") or ("rating" in body.get("detail", ""))


def test_sql_injection_like_title_does_not_crash(client):
    title = "'; DROP TABLE users; --"
    payload = {"title": title, "kind": "movie", "year": 2020}
    r = client.post("/media", json=payload)
    assert r.status_code in (201, 400, 422)


def test_long_title_rejected_or_handled(client):
    title = "A" * 2001
    payload = {"title": title, "kind": "movie", "year": 2020}
    r = client.post("/media", json=payload)
    assert r.status_code in (400, 422, 201)


def test_rate_limit_behavior(client):
    saw_500 = False
    for _ in range(250):
        r = client.get("/media")
        if r.status_code == 500:
            saw_500 = True
            break
        if r.status_code == 429:
            body = r.json()
            assert body.get("title") == "TooManyRequests"
            break
    assert not saw_500


def test_safe_export_sqlite_rejects_traversal(tmp_path):
    src = tmp_path / "media.db"
    src.write_text("dummy")
    dest_dir = tmp_path / "out"
    dest_dir.mkdir()

    out = safe_export_sqlite(str(src), str(dest_dir), filename="ok_backup")
    assert os.path.isfile(out)

    with pytest.raises(ValueError):
        safe_export_sqlite(str(src), str(dest_dir), filename="../../evil")
