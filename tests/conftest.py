
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.dependencies import get_db
from app.services.user_service import UserService
from app.schemas.user_schemas import UserCreate
from app.models.user_model import UserRole
from uuid import uuid4


@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
async def create_test_user(async_client: AsyncClient):
    email = f"user_{uuid4().hex[:6]}@example.com"
    password = "TestPass123!"
    payload = {
        "email": email,
        "password": password
    }
    response = await async_client.post("/register/", json=payload)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
async def authenticated_user(async_client: AsyncClient, create_test_user):
    login_data = {
        "username": create_test_user["email"],
        "password": "TestPass123!"
    }
    response = await async_client.post("/login/", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {
        "token": token,
        "user": create_test_user
    }
