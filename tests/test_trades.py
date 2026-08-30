from httpx import AsyncClient


async def _create_stock_and_get_id(client: AsyncClient, headers: dict, sample_stock: dict) -> str:
    resp = await client.post("/stocks", json=sample_stock, headers=headers)
    return resp.json()["id"]


async def test_create_open_trade_has_no_pnl(
    client: AsyncClient, auth_headers: dict[str, str], sample_stock: dict
) -> None:
    stock_id = await _create_stock_and_get_id(client, auth_headers, sample_stock)

    resp = await client.post(
        "/trades",
        json={
            "stock_id": stock_id,
            "broker": "ZERODHA",
            "side": "BUY",
            "quantity": 10,
            "entry_price": "140.00",
            "entry_date": "2026-06-10",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["realized_pnl"] is None
    assert body["exit_price"] is None


async def test_closing_a_buy_trade_computes_pnl(
    client: AsyncClient, auth_headers: dict[str, str], sample_stock: dict
) -> None:
    stock_id = await _create_stock_and_get_id(client, auth_headers, sample_stock)
    create = await client.post(
        "/trades",
        json={
            "stock_id": stock_id,
            "broker": "GROWW",
            "side": "BUY",
            "quantity": 10,
            "entry_price": "140.00",
            "entry_date": "2026-06-10",
        },
        headers=auth_headers,
    )
    trade_id = create.json()["id"]

    resp = await client.patch(
        f"/trades/{trade_id}/exit",
        json={"exit_price": "155.00", "exit_date": "2026-07-01"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    # (155 - 140) * 10 = 150
    assert float(body["realized_pnl"]) == 150.0
    assert round(float(body["realized_pnl_pct"]), 2) == round(150 / 1400 * 100, 2)


async def test_closing_a_sell_trade_flips_pnl_sign(
    client: AsyncClient, auth_headers: dict[str, str], sample_stock: dict
) -> None:
    stock_id = await _create_stock_and_get_id(client, auth_headers, sample_stock)
    create = await client.post(
        "/trades",
        json={
            "stock_id": stock_id,
            "broker": "ZERODHA",
            "side": "SELL",
            "quantity": 5,
            "entry_price": "200.00",
            "entry_date": "2026-06-10",
        },
        headers=auth_headers,
    )
    trade_id = create.json()["id"]

    resp = await client.patch(
        f"/trades/{trade_id}/exit",
        json={"exit_price": "180.00", "exit_date": "2026-07-01"},
        headers=auth_headers,
    )
    body = resp.json()
    # SELL: (180 - 200) * 5 * -1 = 100 (profit on a short)
    assert float(body["realized_pnl"]) == 100.0


async def test_filter_trades_by_date_range(
    client: AsyncClient, auth_headers: dict[str, str], sample_stock: dict
) -> None:
    stock_id = await _create_stock_and_get_id(client, auth_headers, sample_stock)
    for entry_date in ["2026-01-10", "2026-06-10"]:
        await client.post(
            "/trades",
            json={
                "stock_id": stock_id,
                "broker": "ZERODHA",
                "side": "BUY",
                "quantity": 1,
                "entry_price": "100.00",
                "entry_date": entry_date,
            },
            headers=auth_headers,
        )

    resp = await client.get(
        "/trades",
        params={"date_from": "2026-05-01", "date_to": "2026-12-31"},
        headers=auth_headers,
    )
    dates = [t["entry_date"] for t in resp.json()]
    assert dates == ["2026-06-10"]
