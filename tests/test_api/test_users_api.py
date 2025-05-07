import pytest
from httpx import AsyncClient
from uuid import uuid4
from app.main import app
from app.services.user_service import UserService
from app.models.user_model import UserRole

@pytest.mark.anyio
async def test_list_users_admin_only(admin_token):
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        res = await ac.get("/users/", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert isinstance(data["items"], list)

@pytest.mark.anyio
async def test_admin_can_delete_user(admin_token, setup_users):
    user_id = setup_users["user_id"]
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        res = await ac.delete(f"/users/{user_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 204

@pytest.mark.anyio
async def test_non_admin_cannot_delete_user(user_token, setup_users):
    admin_id = setup_users["admin_id"]
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        res = await ac.delete(f"/users/{admin_id}", headers={"Authorization": f"Bearer {user_token}"})
    assert res.status_code == 403

@pytest.mark.anyio
async def test_user_gets_404_on_nonexistent_user(admin_token):
    bad_uuid = str(uuid4())
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        res = await ac.get(f"/users/{bad_uuid}", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 404

@pytest.mark.anyio
async def test_update_user_by_admin(admin_token, setup_users):
    user_id = setup_users["user_id"]
    update_data = {"bio": "Bio changed by admin", "first_name": "UpdatedName"}
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        res = await ac.put(f"/users/{user_id}", json=update_data,
                           headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["first_name"] == "UpdatedName"
    assert data["bio"] == "Bio changed by admin"
