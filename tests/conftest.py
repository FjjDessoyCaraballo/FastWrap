import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.database.init import init_db, close_db
from main import app
from .MockUser import MockUser
from config import settings


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def setup_database():
    """Initialize database pool once per test session."""
    await init_db()
    yield
    await close_db()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def admin_user(setup_database):
    """Create the first admin via /internal/bootstrap-admin."""
    admin = MockUser()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/internal/bootstrap-admin",
            headers={"x-fastwrap-api-key": settings.FASTWRAP_API_KEY},
            json={"email": admin.email, "password": admin.password},
        )

    if resp.status_code == 201:
        admin.api_key = resp.json()["data"]["api_key"]
        admin.id = str(resp.json()["data"]["id"])
        return admin

    if resp.status_code == 409:
        pool = await init_db()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, email, api_key
                FROM clients
                WHERE is_admin = TRUE
                  AND deleted_at IS NULL
                ORDER BY created_at ASC
                LIMIT 1
                """
            )
        assert row is not None, "Bootstrap returned 409 but DB has no admin"
        admin.id = str(row["id"])
        admin.email = row["email"]
        admin.api_key = row["api_key"]
        return admin

    raise AssertionError(f"Bootstrap admin failed: {resp.status_code} {resp.text}")


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def ensure_admin_exists(admin_user):
    """Force admin creation before any tests run."""
    yield


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def authenticated_user(setup_database):
    """Create a normal (non-admin) client via /auth/signup."""
    user = MockUser()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/auth/signup",
            json={"email": user.email, "password": user.password},
        )

    assert resp.status_code == 201, f"Signup failed: {resp.status_code} {resp.text}"
    data = resp.json()["data"]
    user.api_key = data["api_key"]
    if "id" in data:
        user.id = str(data["id"])

    return user