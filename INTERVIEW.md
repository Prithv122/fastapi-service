# Interview Prep — fastapi-service

**Five questions, five answers.** An unanswered question means this project is not shipped.

If you can't answer one, you don't understand that part of your own project yet — go back and understand it. This file is the difference between a portfolio that survives a technical screen and one that collapses in it.

---

### Q1. Walk me through the architecture in 90 seconds.

_A:_ It's a layered FastAPI service: routers handle HTTP concerns and pull the
authenticated user off a JWT; Pydantic v2 schemas validate the request body and enforce
business rules that don't belong in the database (like a trade setup's price ordering and
minimum risk/reward); SQLAlchemy 2.0 async models handle persistence and expose computed
properties like realized P&L; Neon Postgres is the actual store, reached through the
psycopg 3 driver in async mode. Alembic owns schema migrations independently — it runs the
same models but through its own sync-style runner, so the migration path is a first-class,
version-controlled artifact, not something inferred from `create_all` in production. Every
domain resource (Stock, ResearchNote, TradeSetup, Trade) carries a `user_id` and every
query filters on it, so multi-tenancy is enforced at the query layer, not just at the door.

### Q2. Why did you choose an append-only research history over an editable note?

_A:_ Because the whole point of a trading journal is being able to judge a past decision
against what was actually known at the time — an editable note lets you unconsciously
rewrite history every time you're wrong. I noticed I was already doing this by hand in my
own Notion research tracker, archiving every refresh as a dated snapshot instead of
overwriting the page. So `ResearchNote` rows are never updated or deleted after creation;
a "refresh" is just a new row with the same `stock_id`, and `GET /stocks/{ticker}/history`
returns them in order. It cost me nothing extra at the schema level — no version numbers,
no `superseded_by` pointers — and it's the one design decision in this project that maps
directly onto a real habit rather than a textbook pattern.

### Q3. What's the weakest part of this, and what would break first under load?

_A:_ Two things. First, JWTs here have no revocation path — if a token leaks, it's valid
until it expires, full stop; a real deployment needs short-lived access tokens plus a
refresh-token flow with a server-side denylist. Second, `research_notes` grows unboundedly
per stock with no pruning or "latest call" materialized view — fine at personal-journal
volume (a handful of refreshes per stock per year), but a power user refreshing hundreds of
tickers weekly would start paying for a full history scan on every list/history call. I'd
add a `is_latest` flag maintained on insert, or a covering index, before that became a
real cost.

### Q4. How do you know it works? What did you measure, and against what baseline?

_A:_ 27 tests, 86% coverage, run against the real (migrated) Neon database inside a
per-test SAVEPOINT that's rolled back afterward — not mocks, and not a separate SQLite
substitute that could silently diverge from Postgres behavior (array columns and native
enums, in particular, don't exist in SQLite). Four of those tests exist specifically to
prove cross-user isolation: a second user holding a real UUID for another user's stock,
research note, trade setup, or trade gets a 404 on every route, never a 403 (which would
leak that the object exists) and never the actual data. Beyond pytest, I ran the dev server
for real, logged in as the seeded demo user over HTTP, and manually verified the append-
only history returns calls in the right order and that P&L signs correctly for both a BUY
and a SELL trade.

### Q5. Your risk/reward validation runs once, at setup creation. What happens if the
underlying research note's call changes after that?

_A:_ Nothing, currently — `TradeSetup` optionally references the `ResearchNote` that
justified it via a nullable FK, but that link isn't re-checked once the setup exists. If
the stock gets a new research refresh a week later with a downgraded call, the setup just
sits there looking validated even though its premise has moved. That's a real gap I've
written down as a "what I'd add" item rather than papered over: the honest fix is either a
scheduled re-validation job or a response-time warning ("this setup's research note is no
longer the latest") rather than blocking new setups retroactively, since the setup itself
was valid at the time it was made — which is the same append-only philosophy driving the
research model in the first place.

---

## 30-second pitch

Swing-trading Indian equities means running the same loop over and over: research a stock,
form a thesis with real entry/stop/target levels, size the position against that risk, and
— months later — check whether the call held up. I built a multi-user REST API for that
loop: FastAPI, async SQLAlchemy 2.0 on psycopg 3, Neon Postgres, JWT auth, with research
modeled append-only so a thesis can always be judged against what was known when it was
made. Business rules like minimum risk/reward and signed P&L run server-side, not trusted
to whatever wrote the last edit — and every resource is authorization-scoped, verified by
tests that a second user can't reach another user's data even holding the real ID.
