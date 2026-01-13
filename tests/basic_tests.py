import pytest
import random
import string
from fastapi.testclient import TestClient
from main import app
import logging

client = TestClient(app)

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

test_user = MockUser()

def test_signup_success():
    response = client.post(
        "/auth/signup",
        json={
            "email": test_user.email,
            "password": test_user.password
        }
    )

    # Add debug info if request fails
    if response.status_code != 201:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.json()}")

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.json()}"

    response_data = response.json()
    assert "data" in response_data, f"'data' key missing in response: {response_data}"
    assert "api_key" in response_data["data"], f"'api_key' missing in data: {response_data}"

    test_user.api_key = response_data["data"]["api_key"]
    assert test_user.api_key is not None