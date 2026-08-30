from httpx import AsyncClient


async def _create_stock(client: AsyncClient, headers: dict, sample_stock: dict) -> None:
    resp = await client.post("/stocks", json=sample_stock, headers=headers)
    assert resp.status_code == 201


def _note_payload(refresh_date: str, call: str) -> dict:
    return {
        "refresh_date": refresh_date,
        "call": call,
        "thesis": "Diversified NBFC gaining share in underserved retail lending.",
        "catalysts": ["Q2 results", "rate cut transmission"],
        "risks": ["asset quality softening", "valuation re-rating already priced in"],
        "target_1w": "150.00",
        "target_1w_note": "Consolidating 142-148",
        "target_1_3m": "165.00",
        "target_1_3m_note": "Breakout above 148 opens 165",
        "target_1_3y": "210.00",
        "target_1_3y_note": "FY28 earnings-driven re-rating",
        "technical_notes": "Support 142, resistance 148",
        "brokerage_calls": [
            {
                "broker": "Nomura",
                "rating": "Buy",
                "target_price": "160.00",
                "note": "AUM growth ahead of guidance",
                "call_date": refresh_date,
            }
        ],
    }


async def test_create_research_note(
    client: AsyncClient, auth_headers: dict[str, str], sample_stock: dict
) -> None:
    await _create_stock(client, auth_headers, sample_stock)

    resp = await client.post(
        "/stocks/NEXUSFIN/research", json=_note_payload("2026-06-10", "BUY"), headers=auth_headers
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["call"] == "BUY"
    assert len(body["brokerage_calls"]) == 1
    assert body["brokerage_calls"][0]["broker"] == "Nomura"


async def test_research_history_is_append_only_and_chronological(
    client: AsyncClient, auth_headers: dict[str, str], sample_stock: dict
) -> None:
    await _create_stock(client, auth_headers, sample_stock)

    for refresh_date, call in [
        ("2026-06-10", "BUY"),
        ("2026-06-15", "ACCUMULATE"),
        ("2026-08-25", "HOLD"),
    ]:
        resp = await client.post(
            "/stocks/NEXUSFIN/research",
            json=_note_payload(refresh_date, call),
            headers=auth_headers,
        )
        assert resp.status_code == 201

    resp = await client.get("/stocks/NEXUSFIN/history", headers=auth_headers)
    assert resp.status_code == 200
    history = resp.json()
    assert [h["call"] for h in history] == ["BUY", "ACCUMULATE", "HOLD"]
    assert len({h["research_note_id"] for h in history}) == 3


async def test_research_note_has_no_update_or_delete_route(
    client: AsyncClient, auth_headers: dict[str, str], sample_stock: dict
) -> None:
    await _create_stock(client, auth_headers, sample_stock)
    create_resp = await client.post(
        "/stocks/NEXUSFIN/research", json=_note_payload("2026-06-10", "BUY"), headers=auth_headers
    )
    note_id = create_resp.json()["id"]

    assert (
        await client.patch(f"/research/{note_id}", json={}, headers=auth_headers)
    ).status_code == 405
    assert (await client.delete(f"/research/{note_id}", headers=auth_headers)).status_code == 405
