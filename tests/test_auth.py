from httpx import AsyncClient


async def test_register_and_login(client: AsyncClient) -> None:
    resp = await client.post(
        "/auth/register", json={"email": "new@example.com", "password": "hunter2pass"}
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == "new@example.com"

    resp = await client.post(
        "/auth/login", data={"username": "new@example.com", "password": "hunter2pass"}
    )
    assert resp.status_code == 200
    assert resp.json()["token_type"] == "bearer"
    assert resp.json()["access_token"]


async def test_register_duplicate_email_conflicts(client: AsyncClient) -> None:
    payload = {"email": "dup@example.com", "password": "hunter2pass"}
    first = await client.post("/auth/register", json=payload)
    second = await client.post("/auth/register", json=payload)
    assert first.status_code == 201
    assert second.status_code == 409


async def test_login_wrong_password_is_rejected(client: AsyncClient) -> None:
    await client.post(
        "/auth/register", json={"email": "u@example.com", "password": "correct-password"}
    )
    resp = await client.post(
        "/auth/login", data={"username": "u@example.com", "password": "wrong-password"}
    )
    assert resp.status_code == 401


async def test_protected_route_requires_token(client: AsyncClient) -> None:
    resp = await client.get("/stocks")
    assert resp.status_code == 401


async def test_protected_route_rejects_garbage_token(client: AsyncClient) -> None:
    resp = await client.get("/stocks", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401
