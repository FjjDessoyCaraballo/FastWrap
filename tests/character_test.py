import pytest
import asyncio
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from main import app
from .MockUser import MockUser

@pytest.mark.asyncio(loop_scope="module")
async def test_character_creation_with_ttl(authenticated_user: MockUser):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/characters",
            headers={ "x-api-key": authenticated_user.api_key },
            json={
                "agent_role": "You are a standup comedian.",
                "ttl": 1000
            }
        )

    response_data = response.json()

    assert response.status_code == 201
    assert "data" in response_data, f"'data' field is missing from payload: {response_data}"
    assert "agent_role" in response_data["data"], f"'agent_role' field is missing from payload: {response_data}"
    assert "id" in response_data["data"], f"'id' field is missing from payload: {response_data}"
    assert "ttl" in response_data["data"], f"'TTL' field is missing from payload: {response_data}"

@pytest.mark.asyncio(loop_scope="module")
async def test_character_creation_no_ttl(authenticated_user: MockUser):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/characters",
            headers={ "x-api-key": authenticated_user.api_key },
            json={ "agent_role": authenticated_user.character }
        )

    response_data = response.json()
    print(response_data)
    authenticated_user.character_id = response_data["data"]["id"]

    assert response.status_code == 201
    assert "data" in response_data, f"'data' field is missing from payload: {response_data}"
    assert "agent_role" in response_data["data"], f"'agent_role' field is missing from payload: {response_data}"
    assert response_data["data"]["agent_role"] == authenticated_user.character
    assert "id" in response_data["data"], f"'id' field is missing from payload: {response_data}"

@pytest.mark.asyncio(loop_scope="module")
async def test_character_get(authenticated_user: MockUser):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(
            f"/api/characters/{authenticated_user.character_id}",
            headers={ "x-api-key": authenticated_user.api_key }
        )

    response_data = response.json()

    assert response.status_code == 200, f"Expected HTTP code 200, got {response.status_code} instead."
    assert "data" in response_data, f"'data' is missing from payload: {response_data}"
    assert response_data["data"] == authenticated_user.character

@pytest.mark.asyncio(loop_scope="module")
async def test_character_get_all(authenticated_user: MockUser):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(
            "/api/characters",
            headers={ "x-api-key": authenticated_user.api_key }
        )

    response_data = response.json()

    assert response.status_code == 200, f"Expected HTTP code 200, got {response.status_code} instead."
    assert "data" in response_data, f"'data' missing from payload: {response_data}"

@pytest.mark.asyncio(loop_scope="module")
async def test_character_patch(authenticated_user: MockUser):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.patch(
            f"/api/characters/{authenticated_user.character_id}",
            headers={ "x-api-key": authenticated_user.api_key },
            json={ "agent_role": "You are a salesperson from a hardware store called Hard R' Us." }
        )

        assert response.status_code == 201
        response_data = response.json()
        assert "data" in response_data, f"'data' field missing in payload."
        print(response_data["data"])
        assert response_data["data"] != authenticated_user.character, f"Payload in wrong format: {response_data}"
        authenticated_user.character = response_data["data"]

@pytest.mark.asyncio(loop_scope="module")
async def test_character_deletion(authenticated_user: MockUser):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.delete(
            f"/api/characters/{authenticated_user.character_id}",
            headers={ "x-api-key": authenticated_user.api_key }
        )

    assert response.status_code == 204
    