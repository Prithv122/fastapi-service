"""Shared test fixtures.

Every test runs inside a SAVEPOINT that is rolled back afterwards, so tests can run
against the real (migrated) Neon database without leaving data behind or needing a
throwaway database per run. Schema is created once per session via
`Base.metadata.create_all` -- independent of Alembic, whose migration path is
validated separately in CI.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fastapiservice.config import get_settings
from fastapiservice.database import get_db, make_engine
from fastapiservice.main import create_app
from fastapiservice.models import Base

test_engine = make_engine(get_settings().database_url)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _create_schema():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    async with test_engine.connect() as conn:
        trans = await conn.begin()
        session_factory = async_sessionmaker(
            bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )
        async with session_factory() as session:
            yield session
        await trans.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def register_and_login(
    client: AsyncClient, email: str, password: str = "hunter2pass"
) -> dict[str, str]:
    await client.post("/auth/register", json={"email": email, "password": password})
    resp = await client.post("/auth/login", data={"username": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    return await register_and_login(client, "trader@example.com")


@pytest.fixture
def sample_stock() -> dict:
    return {
        "ticker": "NEXUSFIN",
        "company_name": "Nexus Financial Services Ltd",
        "sector": "Financials",
        "sub_sector": "NBFC - Diversified Lending",
    }
