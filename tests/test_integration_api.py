def test_post_and_get_media_basic(client):
    payload = {"title": "Integration Movie", "kind": "movie", "year": 2021}
    r = client.post("/media", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == "Integration Movie"
    mid = data["id"]
    r2 = client.get(f"/media/{mid}")
    assert r2.status_code == 200
    assert r2.json()["id"] == mid


def test_rating_rejected_if_not_done(client):
    payload = {"title": "Bad Rating", "kind": "movie", "rating": 7.5}
    r = client.post("/media", json=payload)
    assert r.status_code in (400, 422)


def test_create_with_done_and_genres_and_favorite(client):
    payload = {
        "title": "Genre Movie",
        "kind": "movie",
        "status": "done",
        "rating": 8.0,
        "genres": ["action", "drama"],
        "favorite": True,
    }
    r = client.post("/media", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["rating"] == 8.0
    assert data["favorite"] is True
    assert "action" in (data.get("genres") or [])


def test_owner_header_and_permissions(client):
    payload = {"title": "Owned", "kind": "movie", "owner_id": 10}
    r = client.post("/media", json=payload)
    assert r.status_code == 201
    mid = r.json()["id"]
    r2 = client.put(f"/media/{mid}", json={"title": "TryHack"}, headers={"X-Actor-Id": "11"})
    assert r2.status_code in (
        403,
        422,
    ), f"unexpected response: {r2.status_code} {r2.text}"
    r3 = client.put(f"/media/{mid}", json={"title": "OwnerUpdate"}, headers={"X-Actor-Id": "10"})
    assert r3.status_code == 200
    assert r3.json()["title"] == "OwnerUpdate"
    r4 = client.delete(f"/media/{mid}", headers={"X-Actor-Id": "11"})
    assert r4.status_code in (403, 422)
    r5 = client.delete(f"/media/{mid}", headers={"X-Actor-Id": "10"})
    assert r5.status_code == 200
    assert r5.json()["ok"] is True
