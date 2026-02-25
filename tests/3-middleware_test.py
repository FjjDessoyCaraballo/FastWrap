import pytest
import asyncio
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from config import settings
from main import app
import time

@pytest.mark.asyncio(loop_scope="session")
async def test_middleware_limit():
    time.sleep(settings.API_WINDOW) # wait for the window to refresh
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        for i in range(settings.API_LIMIT):
            response = await ac.get("/")
            assert response.status_code == 200, f"Request {i + 1} supposed to succeed"
        response = await ac.get("/")
        assert response.status_code == 429, f"Expected 429, got {response.status_code}"
        time.sleep(settings.API_WINDOW)
