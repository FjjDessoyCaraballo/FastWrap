import pytest
import asyncio
import pytest_asyncio
import random
import string
# from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from main import app
import logging

# client = TestClient(app)


class MockUser():
    def __init__(self):
        self.email: str = self.generate_random_email()
        self.password: str = self.generate_random_password()
        self.api_key: str = ''

    def generate_random_email(self) -> str:
        random_string: str = ''.join(random.choices(string.ascii_letters, k=10))
        random_email: str = random_string + "@example.com"
        return random_email

    def generate_random_password(self) -> str:
        random_lower_string: str = ''.join(random.choices(string.ascii_lowercase, k=3))
        random_upper_string: str = ''.join(random.choices(string.ascii_uppercase, k=3))
        random_number: str = ''.join(random.choices(string.digits, k=4))
        special_case: str = "!"

        random_password: str = random_lower_string + random_upper_string + random_number + special_case

        return random_password

@pytest_asyncio.fixture(loop_scope="module")
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
    assert "api_key" in response_data["data"], "Missing API key field in response"

    test_user.api_key = response_data["data"]["api_key"]
    return test_user

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
async def test_client_patch_email(authenticated_user):
    authenticated_user.email = authenticated_user.generate_random_email()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.patch(
            "/clients/me",
            headers={ "x-api-key": authenticated_user.api_key },
            json={ "email": authenticated_user.email }
        )

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.json()}"

@pytest.mark.asyncio(loop_scope="module")
async def test_client_patch_password(authenticated_user):
    authenticated_user.password = authenticated_user.generate_random_password()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.patch(
            "/clients/me",
            headers={ "x-api-key": authenticated_user.api_key },
            json={ "password": authenticated_user.password }
        )
    
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.json()}"

@pytest.mark.asyncio(loop_scope="module")
async def test_client_regenerate_key(authenticated_user):
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
async def test_client_delete(authenticated_user):
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
