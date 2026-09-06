import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chats_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/chats")).status_code == 401
    assert (await client.post("/api/v1/chats")).status_code == 401
    assert (await client.get("/api/v1/chats/abc")).status_code == 401
    assert (await client.patch("/api/v1/chats/abc", json={"title": "x"})).status_code == 401
    assert (await client.delete("/api/v1/chats/abc")).status_code == 401


@pytest.mark.asyncio
async def test_create_and_list_chat(client: AsyncClient, auth_headers: dict) -> None:
    created = await client.post("/api/v1/chats", headers=auth_headers)
    assert created.status_code == 201
    chat_id = created.json()["id"]

    listed = await client.get("/api/v1/chats", headers=auth_headers)
    assert listed.status_code == 200
    data = listed.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert item["id"] == chat_id
    assert item["title"] == "New chat"
    assert item["message_count"] == 0


@pytest.mark.asyncio
async def test_chat_detail_empty(client: AsyncClient, auth_headers: dict) -> None:
    created = await client.post("/api/v1/chats", headers=auth_headers)
    chat_id = created.json()["id"]
    detail = await client.get(f"/api/v1/chats/{chat_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["messages"] == []


@pytest.mark.asyncio
async def test_rename_chat(client: AsyncClient, auth_headers: dict) -> None:
    created = await client.post("/api/v1/chats", headers=auth_headers)
    chat_id = created.json()["id"]
    renamed = await client.patch(
        f"/api/v1/chats/{chat_id}", json={"title": "BTC outlook"}, headers=auth_headers
    )
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "BTC outlook"


@pytest.mark.asyncio
async def test_rename_validation(client: AsyncClient, auth_headers: dict) -> None:
    created = await client.post("/api/v1/chats", headers=auth_headers)
    chat_id = created.json()["id"]
    resp = await client.patch(
        f"/api/v1/chats/{chat_id}", json={"title": ""}, headers=auth_headers
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_delete_chat(client: AsyncClient, auth_headers: dict) -> None:
    created = await client.post("/api/v1/chats", headers=auth_headers)
    chat_id = created.json()["id"]
    deleted = await client.delete(f"/api/v1/chats/{chat_id}", headers=auth_headers)
    assert deleted.status_code == 204
    assert (await client.get(f"/api/v1/chats/{chat_id}", headers=auth_headers)).status_code == 404


@pytest.mark.asyncio
async def test_chats_isolated_between_users(client: AsyncClient, auth_headers: dict) -> None:
    created = await client.post("/api/v1/chats", headers=auth_headers)
    chat_id = created.json()["id"]

    other = await client.post(
        "/api/v1/auth/register",
        json={"username": "other_user_xyz", "password": "password123"},
    )
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}

    assert (await client.get(f"/api/v1/chats/{chat_id}", headers=other_headers)).status_code == 404
    assert (await client.delete(f"/api/v1/chats/{chat_id}", headers=other_headers)).status_code == 404
    other_list = await client.get("/api/v1/chats", headers=other_headers)
    assert other_list.json()["total"] == 0


@pytest.mark.asyncio
async def test_share_chat_roundtrip(client: AsyncClient, auth_headers: dict) -> None:
    created = await client.post("/api/v1/chats", headers=auth_headers)
    chat_id = created.json()["id"]

    shared = await client.post(f"/api/v1/chats/{chat_id}/share", headers=auth_headers)
    assert shared.status_code == 200
    token = shared.json()["token"]
    assert token

    # public read with a valid token works without auth
    public = await client.get(f"/api/v1/chats/{chat_id}/shared?token={token}")
    assert public.status_code == 200
    assert public.json()["id"] == chat_id

    # wrong token is rejected
    bad = await client.get(f"/api/v1/chats/{chat_id}/shared?token=deadbeef")
    assert bad.status_code == 403

    # missing token is rejected
    missing = await client.get(f"/api/v1/chats/{chat_id}/shared")
    assert missing.status_code == 422

    # sharing someone else's chat is forbidden
    other = await client.post(
        "/api/v1/auth/register",
        json={"username": "share_other_user", "password": "password123"},
    )
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    forbidden = await client.post(f"/api/v1/chats/{chat_id}/share", headers=other_headers)
    assert forbidden.status_code == 404


@pytest.mark.asyncio
async def test_search_and_pagination(client: AsyncClient, auth_headers: dict) -> None:
    for title in ["BTC outlook", "ETH momentum", "BTC vs ETH"]:
        created = await client.post("/api/v1/chats", headers=auth_headers)
        await client.patch(
            f"/api/v1/chats/{created.json()['id']}",
            json={"title": title},
            headers=auth_headers,
        )

    searched = await client.get("/api/v1/chats?search=btc", headers=auth_headers)
    assert searched.json()["total"] == 2

    page = await client.get("/api/v1/chats?limit=2&offset=0", headers=auth_headers)
    assert len(page.json()["items"]) == 2
    assert page.json()["total"] == 3

    page2 = await client.get("/api/v1/chats?limit=2&offset=2", headers=auth_headers)
    assert len(page2.json()["items"]) == 1
