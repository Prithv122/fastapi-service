# fastapi-service — C2

**Tier:** 2 · **Category:** C — Python web · **Wave:** 2

Root rules in `../CLAUDE.md` apply. This file is project-specific only — keep it under 40 lines.

## What this is

Production FastAPI service — layered architecture, Pydantic v2, SQLAlchemy 2.0 + Alembic,
Neon Postgres, JWT auth, pytest + httpx, Docker, CI, deployed. The most reusable backend
project in the catalogue.

## Stack

FastAPI · Pydantic v2 / pydantic-settings · SQLAlchemy 2.0 (async, psycopg 3 driver) ·
Alembic · Neon Postgres (serverless) · PyJWT + bcrypt · pytest + pytest-asyncio + httpx ·
Docker · GitHub Actions · uv.

## Acceptance criteria

- [ ] Layered FastAPI service backed by Neon Postgres, JWT auth, tested, containerized,
      deployed (`CATALOG.md` C2)
- [ ] Ship gate passes (`/ship`)

## Project-specific notes

- Requires a live Neon Postgres connection string in `.env` (`DATABASE_URL`) — see
  `SETUP.md` Group 2. Never commit `.env`.
- Docker Desktop must be running for the containerization/CI-Docker-build stage.
