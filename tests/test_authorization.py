"""Cross-user isolation: user A cannot see, modify, or discover user B's data by ID.

This is the property the user explicitly called out as more valuable than testing that
/login returns a token -- IDOR (insecure direct object reference) is a real OWASP category,
and every resource here is scoped to its owner.
"""

from httpx import AsyncClient

from conftest import register_and_login


async def _headers_for(client: AsyncClient, email: str) -> dict[str, str]:
    return await register_and_login(client, email)


async def test_user_cannot_see_another_users_stock(client: AsyncClient, sample_stock: dict) -> None:
    a_headers = await _headers_for(client, "alice@example.com")
    b_headers = await _headers_for(client, "bob@example.com")

    await client.post("/stocks", json=sample_stock, headers=a_headers)

    # Bob's own stock list must not include Alice's stock.
    resp = await client.get("/stocks", headers=b_headers)
    assert resp.json() == []

    # Bob looking up Alice's ticker directly gets 404, not Alice's data.
    resp = await client.get("/stocks/NEXUSFIN", headers=b_headers)
    assert resp.status_code == 404


async def test_user_cannot_read_another_users_research_note_by_id(
    client: AsyncClient, sample_stock: dict
) -> None:
    a_headers = await _headers_for(client, "alice2@example.com")
    b_headers = await _headers_for(client, "bob2@example.com")

    await client.post("/stocks", json=sample_stock, headers=a_headers)
    note_resp = await client.post(
        "/stocks/NEXUSFIN/research",
        json={
            "refresh_date": "2026-06-10",
            "call": "BUY",
            "thesis": "Alice's private thesis.",
            "catalysts": [],
            "risks": [],
        },
        headers=a_headers,
    )
    note_id = note_resp.json()["id"]

    # Bob knows the UUID but must not be able to fetch it -- a 404, not a 403 that would
    # confirm the object exists.
    resp = await client.get(f"/research/{note_id}", headers=b_headers)
    assert resp.status_code == 404


async def test_user_cannot_modify_another_users_trade_setup(
    client: AsyncClient, sample_stock: dict
) -> None:
    a_headers = await _headers_for(client, "alice3@example.com")
    b_headers = await _headers_for(client, "bob3@example.com")

    stock_resp = await client.post("/stocks", json=sample_stock, headers=a_headers)
    setup_resp = await client.post(
        "/setups",
        json={
            "stock_id": stock_resp.json()["id"],
            "scenario": "Alice's setup",
            "entry_zone_low": "140.00",
            "entry_zone_high": "145.00",
            "stop_loss": "130.00",
            "target_price": "170.00",
            "timeframe": "SWING",
        },
        headers=a_headers,
    )
    setup_id = setup_resp.json()["id"]

    resp = await client.patch(
        f"/setups/{setup_id}", json={"status": "INVALIDATED"}, headers=b_headers
    )
    assert resp.status_code == 404

    # Confirm Alice's setup was untouched.
    resp = await client.get("/setups", headers=a_headers)
    assert resp.json()[0]["status"] == "OPEN"


async def test_user_cannot_close_another_users_trade(
    client: AsyncClient, sample_stock: dict
) -> None:
    a_headers = await _headers_for(client, "alice4@example.com")
    b_headers = await _headers_for(client, "bob4@example.com")

    stock_resp = await client.post("/stocks", json=sample_stock, headers=a_headers)
    trade_resp = await client.post(
        "/trades",
        json={
            "stock_id": stock_resp.json()["id"],
            "broker": "ZERODHA",
            "side": "BUY",
            "quantity": 10,
            "entry_price": "140.00",
            "entry_date": "2026-06-10",
        },
        headers=a_headers,
    )
    trade_id = trade_resp.json()["id"]

    resp = await client.patch(
        f"/trades/{trade_id}/exit",
        json={"exit_price": "999.00", "exit_date": "2026-07-01"},
        headers=b_headers,
    )
    assert resp.status_code == 404

    resp = await client.get(f"/trades/{trade_id}", headers=a_headers)
    assert resp.json()["exit_price"] is None
