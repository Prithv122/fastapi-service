# Resume Bullets — fastapi-service

Form: **action → technical specifics → measured outcome.** Numbers or it doesn't go on the resume.

---

## Bullets

- Built a multi-user REST API (FastAPI, async SQLAlchemy 2.0 on psycopg 3, Neon Postgres,
  Alembic, JWT) for tracking equity research, trade setups, and trades, with research
  modeled as an append-only history so past calls can be judged against what was known at
  the time — verified by 27 tests (86% coverage) run against the live database.
- Enforced per-user data isolation at the query layer across every resource, closing an
  IDOR (insecure direct object reference) class of bug by returning 404 rather than 403 on
  cross-user access — proven with 4 dedicated authorization tests that a second user
  holding a real object UUID cannot read, modify, or discover another user's data.
- Implemented server-side financial business logic (trade-setup price ordering, minimum
  risk/reward ratio, signed realized P&L for both long and short trades) using `Decimal`
  throughout to avoid float rounding error, rather than trusting client-supplied values.

## Which roles this supports

- [ ] Data Scientist / ML
- [x] AI Engineer (LLM/NLP/CV) — reusable backend pattern for future LLM-facing services
- [x] Data Engineer — Alembic-managed schema, layered persistence
- [x] Data Analyst / Python Developer — the primary fit: production API design

## Keywords this project earns

FastAPI · Pydantic v2 · SQLAlchemy 2.0 (async) · psycopg 3 · PostgreSQL · Alembic
migrations · JWT authentication · bcrypt · pytest / pytest-asyncio · httpx · REST API
design · authorization / IDOR prevention · Docker · GitHub Actions CI.

---

### Bad vs good

❌ "Built a machine learning model to predict customer churn using Python."
✅ "Built a churn classifier on 240k accounts (LightGBM, 1:40 class imbalance) with isotonic calibration and cost-sensitive thresholding, lifting precision@10% from 0.31 to 0.58 over the business's existing rules baseline."

The second one is answerable in an interview. The first invites the question you can't answer.
