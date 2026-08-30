from httpx import AsyncClient


async def _create_stock_and_get_id(client: AsyncClient, headers: dict, sample_stock: dict) -> str:
    resp = await client.post("/stocks", json=sample_stock, headers=headers)
    return resp.json()["id"]


async def test_create_valid_setup(
    client: AsyncClient, auth_headers: dict[str, str], sample_stock: dict
) -> None:
    stock_id = await _create_stock_and_get_id(client, auth_headers, sample_stock)

    resp = await client.post(
        "/setups",
        json={
            "stock_id": stock_id,
            "scenario": "Dip entry",
            "entry_zone_low": "140.00",
            "entry_zone_high": "145.00",
            "stop_loss": "130.00",
            "target_price": "170.00",
            "timeframe": "SWING",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "OPEN"
    # risk = 140-130 = 10, reward = 170-140 = 30, R:R = 3.0
    assert float(body["risk_reward_ratio"]) == 3.0


async def test_setup_rejects_bad_price_ordering(
    client: AsyncClient, auth_headers: dict[str, str], sample_stock: dict
) -> None:
    stock_id = await _create_stock_and_get_id(client, auth_headers, sample_stock)

    resp = await client.post(
        "/setups",
        json={
            "stock_id": stock_id,
            "scenario": "Bad setup",
            "entry_zone_low": "140.00",
            "entry_zone_high": "145.00",
            "stop_loss": "150.00",  # stop above entry -- invalid
            "target_price": "170.00",
            "timeframe": "SWING",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_setup_rejects_poor_risk_reward(
    client: AsyncClient, auth_headers: dict[str, str], sample_stock: dict
) -> None:
    stock_id = await _create_stock_and_get_id(client, auth_headers, sample_stock)

    resp = await client.post(
        "/setups",
        json={
            "stock_id": stock_id,
            "scenario": "Poor R:R",
            "entry_zone_low": "140.00",
            "entry_zone_high": "145.00",
            "stop_loss": "130.00",  # risk = 10
            "target_price": "145.00",  # reward = 5
            "timeframe": "SWING",
        },
        headers=auth_headers,
    )
    # reward/risk = 5/10 = 0.5, well below the 1.5 minimum
    assert resp.status_code == 422


async def test_update_setup_status(
    client: AsyncClient, auth_headers: dict[str, str], sample_stock: dict
) -> None:
    stock_id = await _create_stock_and_get_id(client, auth_headers, sample_stock)
    create = await client.post(
        "/setups",
        json={
            "stock_id": stock_id,
            "scenario": "Breakout add",
            "entry_zone_low": "140.00",
            "entry_zone_high": "145.00",
            "stop_loss": "130.00",
            "target_price": "170.00",
            "timeframe": "SWING",
        },
        headers=auth_headers,
    )
    setup_id = create.json()["id"]

    resp = await client.patch(
        f"/setups/{setup_id}", json={"status": "TRIGGERED"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "TRIGGERED"


async def test_filter_setups_by_status(
    client: AsyncClient, auth_headers: dict[str, str], sample_stock: dict
) -> None:
    stock_id = await _create_stock_and_get_id(client, auth_headers, sample_stock)
    await client.post(
        "/setups",
        json={
            "stock_id": stock_id,
            "scenario": "Open one",
            "entry_zone_low": "140.00",
            "entry_zone_high": "145.00",
            "stop_loss": "130.00",
            "target_price": "170.00",
            "timeframe": "SWING",
        },
        headers=auth_headers,
    )

    resp = await client.get("/setups", params={"status_filter": "OPEN"}, headers=auth_headers)
    assert resp.status_code == 200
    assert all(s["status"] == "OPEN" for s in resp.json())
