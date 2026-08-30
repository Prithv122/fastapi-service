# fastapi-service — C2

**Tier:** 2 · **Category:** C — Python web · **Wave:** 2

Root rules in `../CLAUDE.md` apply. This file is project-specific only — keep it under 40 lines.

## What this is

**Personal Indian Equity Research & Swing-Trade Journal API.** Multi-user REST API for
tracking NSE stock research, brokerage calls, trade setups, and trades. Domain modeled on
the user's own real workflow (Notion deep-dive tracker + Zerodha/Groww holdings), with
invented seed data. Not a trading platform: no broker integration, no live prices, no
execution, no AI recommendations.

## Stack

FastAPI · Pydantic v2 / pydantic-settings · SQLAlchemy 2.0 (async, psycopg 3 driver) ·
Alembic · Neon Postgres (serverless) · PyJWT + bcrypt · pytest + pytest-asyncio + httpx ·
Docker · GitHub Actions · uv.

## Acceptance criteria

- [ ] Layered FastAPI service backed by Neon Postgres, JWT auth, tested, containerized,
      deployed (`CATALOG.md` C2)
- [ ] Ship gate passes (`/ship`)

## Key domain decisions

- **ResearchNote is append-only** — a refresh creates a new row, never edits a prior one.
  `GET /stocks/{ticker}/history` surfaces the chronological call history.
- **Multi-user, strictly isolated** — every Stock/ResearchNote/TradeSetup/Trade is owned by
  a user; cross-user access must 404, not 403 (don't confirm the object exists).
- **All money/price fields are `Decimal`**, never `float`.
- Async SQLAlchemy 2.0 on the psycopg 3 driver — one driver for both the async app engine
  and Alembic's sync migration runner.

## Project-specific notes

- Requires a live Neon Postgres connection string in `.env` (`DATABASE_URL`) — see
  `SETUP.md` Group 2. Never commit `.env`.
- Docker Desktop must be running for the containerization/CI-Docker-build stage.
