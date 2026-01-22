import pytest
import asyncio
import pytest_asyncio
import string
from httpx import AsyncClient, ASGITransport
from main import app
from .MockUser import MockUser

@pytest.mark.asyncio(loop_scope="module")
async def test_signup_success():
    temp_user = MockUser()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/auth/signup", json={
            "email": temp_user.generate_random_email(), 
            "password": temp_user.generate_random_password() 
            })

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.json()}"

    response_data = response.json()
    assert "data" in response_data, f"'data' key missing in response: {response_data}"
    assert "api_key" in response_data["data"], f"'api_key' missing in data: {response_data}"

@pytest.mark.asyncio(loop_scope="module")
async def test_client_patch_email(authenticated_user: MockUser):
    authenticated_user.email = authenticated_user.generate_random_email()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.patch(
            "/clients/me",
            headers={ "x-api-key": authenticated_user.api_key },
            json={ "email": authenticated_user.email }
        )

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.json()}"

@pytest.mark.asyncio(loop_scope="module")
async def test_client_patch_password(authenticated_user: MockUser):
    authenticated_user.password = authenticated_user.generate_random_password()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.patch(
            "/clients/me",
            headers={ "x-api-key": authenticated_user.api_key },
            json={ "password": authenticated_user.password }
        )
    
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.json()}"

@pytest.mark.asyncio(loop_scope="module")
async def test_client_regenerate_key(authenticated_user: MockUser):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/clients/me/regenerate-key",
            headers={ "x-api-key": authenticated_user.api_key }
        )

    response_data = response.json()
    print(response_data)
    assert response_data["api_key"] != authenticated_user.api_key
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"

@pytest.mark.asyncio(loop_scope="module")
async def test_client_delete(authenticated_user: MockUser):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.delete(
            "/clients/me",
            headers={ "x-api-key": authenticated_user.api_key }
        )
    
    assert response.status_code == 204, f"Expected 204, got {response.status_code}"

    # Test to verify is client together with resources are all deleted
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        test_response = await ac.post(
            "/clients/me/regenerate-key",
            headers={ "x-api-key": authenticated_user.api_key }
        )

    assert test_response.status_code == 401, f"Expected 401, got {test_response.status_code}"
