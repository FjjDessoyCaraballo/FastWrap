import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_signup_success():
    response = client.post(
        "/auth/signup",
        json={
            "email": "test@example.com",
            "password": "ValidPass123!"
        }
    )
    assert response.status_code == 201
    assert "api_key" in response.json()["data"]