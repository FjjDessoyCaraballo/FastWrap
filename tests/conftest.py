import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.database.init import init_db, close_db
import pytest
import asyncio
from main import app
from .MockUser import MockUser

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Initialization of database pool once for all tests, closes on teardown"""
    await init_db()
    yield
    await close_db()

@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def authenticated_user():
    test_user = MockUser()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/auth/signup",
            json={
                "email": test_user.email, 
                "password": test_user.password
                }
            )

    assert response.status_code == 201, f"Signup failed: {response.status_code}"

    response_data = response.json()

    assert "data" in response_data, "Missing data field in response"
    assert "api_key" in response_data["data"], "Missing api_key field in response"

    test_user.api_key = response_data["data"]["api_key"]
    return test_user