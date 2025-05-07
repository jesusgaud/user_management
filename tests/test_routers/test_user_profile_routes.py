import pytest
from httpx import AsyncClient
from uuid import uuid4
from app.main import app
from app.services.user_service import UserService
from app.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.anyio
@pytest.fixture
async def setup_users():
    admin_email = f"admin_{uuid4().hex[:6]}@example.com"
    user_email = f"user_{uuid4().hex[:6]}@example.com"
    password = "TestPass123!"

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        admin_payload = {"email": admin_email, "password": password}
        res1 = await ac.post("/register/", json=admin_payload)
        assert res1.status_code == 201, "Admin registration failed"
        admin_data = res1.json()
        assert admin_data["role"] == "ADMIN"

        user_payload = {"email": user_email, "password": password}
        res2 = await ac.post("/register/", json=user_payload)
        assert res2.status_code == 201, "User registration failed"
        user_data = res2.json()

        user_uuid = user_data["id"]
        async with get_db() as session:
            test_user = await UserService.get_by_id(session, user_uuid)
            token = test_user.verification_token
        verify_res = await ac.get(f"/verify-email/{user_data['id']}/{token}")
        assert verify_res.status_code == 200

        login_data = {"username": admin_email, "password": password}
        res3 = await ac.post("/login/", data=login_data)
        assert res3.status_code == 200, "Admin login failed"
        admin_token = res3.json()["access_token"]

        login_data = {"username": user_email, "password": password}
        res4 = await ac.post("/login/", data=login_data)
        assert res4.status_code == 200, "User login failed"
        user_token = res4.json()["access_token"]

    return {
        "admin_token": admin_token,
        "admin_email": admin_email,
        "admin_id": admin_data["id"],
        "user_token": user_token,
        "user_email": user_email,
        "user_id": user_data["id"]
    }

@pytest.mark.anyio
async def test_get_profile_me_success(setup_users):
    user_token = setup_users["user_token"]
    user_email = setup_users["user_email"]
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get("/users/me", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    profile = response.json()
    assert profile["email"] == user_email

@pytest.mark.anyio
async def test_update_profile_me_success(setup_users):
    user_token = setup_users["user_token"]
    update_payload = {"first_name": "Updated", "bio": "Updated Bio"}
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.patch("/users/me", json=update_payload,
                                  headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["bio"] == "Updated Bio"

@pytest.mark.anyio
async def test_update_profile_me_no_fields(setup_users):
    user_token = setup_users["user_token"]
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.patch("/users/me", json={}, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 422

@pytest.mark.anyio
async def test_get_profile_me_unauthorized():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get("/users/me")
    assert response.status_code == 401

@pytest.mark.anyio
async def test_update_profile_invalid_data(setup_users):
    user_token = setup_users["user_token"]
    bad_data = {"linkedin_profile_url": "not-a-url"}
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.patch("/users/me", json=bad_data, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 422

@pytest.mark.anyio
async def test_user_cannot_change_role(setup_users):
    user_token = setup_users["user_token"]
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.patch("/users/me", json={"role": "ADMIN"},
                                  headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403

@pytest.mark.anyio
async def test_user_cannot_access_others_profile(setup_users):
    user_token = setup_users["user_token"]
    admin_id = setup_users["admin_id"]
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        res1 = await ac.get(f"/users/{admin_id}", headers={"Authorization": f"Bearer {user_token}"})
        assert res1.status_code == 403

@pytest.mark.anyio
async def test_admin_can_get_and_update_others_profile(setup_users):
    admin_token = setup_users["admin_token"]
    user_id = setup_users["user_id"]
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        res1 = await ac.get(f"/users/{user_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert res1.status_code == 200
        res2 = await ac.put(f"/users/{user_id}", json={"first_name": "AdminEdit"},
                            headers={"Authorization": f"Bearer {admin_token}"})
        assert res2.status_code == 200
