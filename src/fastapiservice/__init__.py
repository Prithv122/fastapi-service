"""fastapi-service — production FastAPI backend with Neon Postgres and JWT auth."""

import asyncio
import sys

# psycopg's async mode cannot run on Windows' default ProactorEventLoop -- it needs
# a selector-based loop. Must be set before any event loop is created (alembic,
# uvicorn, and pytest-asyncio all create one lazily), so it lives at package import.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

__version__ = "0.1.0"
