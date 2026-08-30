# Build Notes — fastapi-service

Working notes: what broke, what you tried, why you chose X over Y.
Not for recruiters — for you, six months from now, in an interview.

Keep it rough. Rough is the point.

---

## Log

### 2026-08-30 — domain investigation and lock-in
- **Investigated** the user's real Notion "Stock Deep Dive Tracker" (NSE equities: sector/
  sub-sector taxonomy, Call enum Buy/Accumulate/Hold/Wait & Buy/Sell, 1W/1-3M/1-3Y upside
  targets, per-broker brokerage-call tables, technical support/resistance levels) and local
  broker exports (`Fin/Portfolio Combined - Jun 2026.csv`: broker/ticker/sector/qty/avg_price/
  current_price/pnl across both Zerodha and Groww). Used this to replace a generic
  "stock tracker" idea with a domain that matches how the user actually works.
- **Key discovery**: the user's Notion pages archive every research refresh as a dated,
  nested toggle rather than overwriting — they've been manually versioning research this
  whole time. This became the project's central design decision (see below).
- **Domain locked**: Personal Indian Equity Research & Swing-Trade Journal API. Multi-user
  JWT, async SQLAlchemy 2.0 + psycopg 3 + Neon, Alembic. Explicitly not a trading platform —
  no broker integration, no live prices, no execution, no AI recommendations.

### 2026-08-30 — build: layered app, Alembic, tests against real Neon
- **Tried**: connect via async SQLAlchemy + psycopg 3 on Windows.
  **Broke**: `psycopg.InterfaceError: Psycopg cannot use the 'ProactorEventLoop' to run in
  async mode` — hit twice, in two different places, for two different reasons.
  1. Alembic/pytest-asyncio/plain scripts all create their event loop via
     `asyncio.run()`, which honors whatever policy is set. **Fixed by** setting
     `asyncio.WindowsSelectorEventLoopPolicy()` at package import time
     (`fastapiservice/__init__.py`), before anything can create a loop.
  2. That fix did *not* cover the actual running app under `uvicorn.run()` — uvicorn's own
     `loops/asyncio.py` hardcodes `asyncio.ProactorEventLoop` on Windows whenever
     `use_subprocess` is false, overriding the ambient policy entirely rather than reading
     it. Only found this by reading uvicorn's own source after the package-level fix
     provably ran (confirmed via a standalone script) but the live server still failed.
     **Fixed by** passing `loop="none"` to `uvicorn.run()`, which skips uvicorn's loop
     factory and falls back to the policy already set. **Learned**: a fix that works for a
     script/test harness isn't proof it works for the actual server process — different
     entry points can each construct their own event loop.
- **Tried**: assumed a Neon connection string comes pre-formatted for SQLAlchemy.
  **Broke**: Neon's dashboard hands out a bare `postgresql://...` URL, which SQLAlchemy
  resolves to the `psycopg2` dialect by default (not installed here — this project uses
  psycopg 3 only) → `ModuleNotFoundError: No module named 'psycopg2'`.
  **Fixed by** a `field_validator` on `Settings.database_url` that rewrites a bare
  `postgres://`/`postgresql://` prefix to `postgresql+psycopg://`, so a stock Neon URL
  just works without the user needing to know about SQLAlchemy driver suffixes.
- **Caught**: `.env`'s `JWT_SECRET_KEY` ended up at 20 characters after being hand-edited
  (PyJWT's `InsecureKeyLengthWarning` surfaced it in test output) — rotated to a fresh
  64-character `secrets.token_urlsafe(48)` value in place, without ever reading or printing
  the file's `DATABASE_URL` line.
- **Caught during first real test run**: `GET /stocks/{ticker}/history`'s response model
  (`StockHistoryEntry.research_note_id`) didn't match the ORM attribute name (`.id`), so
  FastAPI's automatic attribute-based serialization raised `ResponseValidationError` for
  every row. Fixed by building the response explicitly in the router instead of relying on
  `from_attributes` to bridge a renamed field.
- **Caught my own test bug**: `test_setup_rejects_poor_risk_reward` computed reward wrong
  in a comment (said reward=3, actual reward was 8 given the test's own numbers) and
  asserted the wrong status code for a setup that was, correctly, accepted. Fixed the
  test's numbers, not the validation logic — the API was right, the test was wrong.
- **Verified end-to-end, not just via pytest**: ran the dev server for real, logged in as
  the seeded demo user over HTTP, and confirmed `/stocks`, `/stocks/NEXUSFIN/history`
  (correct BUY → ACCUMULATE → HOLD order), and `/trades` (correct signed P&L for both a
  BUY and a SELL trade, including a losing trade) all serve real, correctly-computed data.

---

## Rejected approaches

| Approach | Why rejected |
|---|---|
| Generic "stocks + notes" CRUD app (original sketch) | Didn't reflect how the user actually researches — no versioning, no multi-broker, no business-logic hooks beyond CRUD |
| Editable `ResearchNote` with an `updated_at` column | Loses the ability to evaluate a past call against what was known at the time; the user's own Notion habit already proves append-only is the right model |
| Importing real portfolio/PnL into the repo as seed data | Public repo — personal holdings and identifiable research don't belong there. Using invented NSE-style tickers (ARVINDTECH, BHARATGREEN, NEXUSFIN, ORBITDEF) instead |
| Classic asyncpg (app) + psycopg2 (Alembic) driver split | Two drivers for one project; psycopg 3 supports both sync and async natively, so Alembic and the app share one driver |
| `float` for prices/P&L | Rounding errors on money; `Decimal` throughout instead |

### 2026-08-30 — CI caught a stale local ruff cache
- **Broke**: first push's CI run failed on `ruff check` (unsorted `__all__` in
  `models/__init__.py`, unsorted imports in `models/setup.py` and `models/stock.py`) even
  though every local `ruff check .` during the build had reported "All checks passed!".
  **Cause**: `.ruff_cache/` (gitignored, machine-local) had cached a clean result for those
  three files from earlier in the session and never re-flagged them, even across a config
  change (adding `ignore = ["B008"]`) that should have invalidated it. **Fixed by** deleting
  `.ruff_cache` and re-running — the real, uncached state had 3 genuine violations. **Learned**:
  a clean local lint run late in a long session isn't proof of a clean *file* — CI's fresh
  environment is the actual source of truth, which is exactly why it's a separate gate and
  not just "trust the last local check."

### 2026-08-30 — Docker: `uv run` at container CMD re-syncs dev deps on every start
- **Tried**: `CMD ["uv", "run", "uvicorn", ...]` in the Dockerfile, after a multi-stage
  `uv sync --frozen --no-dev` build. **Broke** (quietly, not a crash): the container's own
  logs showed `Downloading ruff (9.8MiB)` and package installs on *every* `docker run`,
  even though the image was supposedly already fully built. `uv run` reconciles the
  environment against pyproject's declared dependency-groups by default, regardless of the
  `--no-dev` used at build time — it doesn't know the image was built frozen-without-dev,
  so it "helpfully" installs the dev group back at runtime. Defeats the point of a
  multi-stage build and would fail outright with no network access to PyPI at runtime.
  **Fixed by** putting `/app/.venv/bin` on `PATH` and calling `uvicorn` directly in `CMD`,
  bypassing `uv run` (and any sync check) entirely at container start. Verified clean logs
  after the fix (no downloads, immediate `Uvicorn running`), then re-verified the full
  request path against real Neon data (login, `/stocks`) from inside the running container.

## Open questions

- [x] Confirm real Neon connection string is in `.env` before running the first migration
- [x] Decide whether `TradeSetup` and `ResearchNote` should cross-reference each other —
      done: `TradeSetup.research_note_id` is a nullable FK, used in the seed data
- [ ] Docker Desktop wasn't running during the build session — Dockerfile is written but
      not yet built/run. Confirm before `/ship`.
- [ ] Not deployed yet (Render/Fly.io) — SETUP.md Group 3.
