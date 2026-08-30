from httpx import AsyncClient


async def test_create_and_list_stock(
    client: AsyncClient, auth_headers: dict[str, str], sample_stock: dict
) -> None:
    resp = await client.post("/stocks", json=sample_stock, headers=auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["ticker"] == "NEXUSFIN"
    assert body["sector"] == "Financials"

    resp = await client.get("/stocks", headers=auth_headers)
    assert resp.status_code == 200
    tickers = [s["ticker"] for s in resp.json()]
    assert "NEXUSFIN" in tickers


async def test_ticker_is_uppercased(
    client: AsyncClient, auth_headers: dict[str, str], sample_stock: dict
) -> None:
    payload = sample_stock | {"ticker": "nexusfin"}
    resp = await client.post("/stocks", json=payload, headers=auth_headers)
    assert resp.json()["ticker"] == "NEXUSFIN"


async def test_get_stock_by_ticker(
    client: AsyncClient, auth_headers: dict[str, str], sample_stock: dict
) -> None:
    await client.post("/stocks", json=sample_stock, headers=auth_headers)
    resp = await client.get("/stocks/NEXUSFIN", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["company_name"] == sample_stock["company_name"]


async def test_get_unknown_stock_is_404(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    resp = await client.get("/stocks/NOSUCHTICKER", headers=auth_headers)
    assert resp.status_code == 404


async def test_filter_stocks_by_sector(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    await client.post(
        "/stocks",
        json={
            "ticker": "ARVINDTECH",
            "company_name": "Arvind Technologies Ltd",
            "sector": "IT",
            "sub_sector": "IT Services",
        },
        headers=auth_headers,
    )
    await client.post(
        "/stocks",
        json={
            "ticker": "BHARATGREEN",
            "company_name": "Bharat Green Energy Ltd",
            "sector": "Renewables",
            "sub_sector": "Solar EPC",
        },
        headers=auth_headers,
    )

    resp = await client.get("/stocks", params={"sector": "IT"}, headers=auth_headers)
    tickers = [s["ticker"] for s in resp.json()]
    assert tickers == ["ARVINDTECH"]
