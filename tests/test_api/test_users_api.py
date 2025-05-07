from builtins import str
import pytest
from httpx import AsyncClient
from app.main import app
from app.models.user_model import User, UserRole
from app.utils.nickname_gen import generate_nickname
from app.utils.security import hash_password
from app.services.jwt_service import decode_token  # Import your FastAPI app

# Example of a test function using the async_client fixture
@pytest.mark.asyncio
async def test_create_user_access_denied(async_client, user_token, email_service):
    headers = {"Authorization": f"Bearer {user_token}"}
    # Define user data for the test
    user_data = {
        "nickname": generate_nickname(),
        "email": "test@example.com",
        "password": "sS#fdasrongPassword123!",
    }
    # Send a POST request to create a user
    response = await async_client.post("/users/", json=user_data, headers=headers)
    # Asserts
    assert response.status_code == 403

# You can similarly refactor other test functions to use the async_client fixture
@pytest.mark.asyncio
async def test_retrieve_user_access_denied(async_client, verified_user, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await async_client.get(f"/users/{verified_user.id}", headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_retrieve_user_access_allowed(async_client, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.get(f"/users/{admin_user.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == str(admin_user.id)

@pytest.mark.asyncio
async def test_update_user_email_access_denied(async_client, verified_user, user_token):
    updated_data = {"email": f"updated_{verified_user.id}@example.com"}
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await async_client.put(f"/users/{verified_user.id}", json=updated_data, headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_update_user_email_access_allowed(async_client, admin_user, admin_token):
    updated_data = {"email": f"updated_{admin_user.id}@example.com"}
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.put(f"/users/{admin_user.id}", json=updated_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == updated_data["email"]

@pytest.mark.asyncio
async def test_delete_user(async_client, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    delete_response = await async_client.delete(f"/users/{admin_user.id}", headers=headers)
    assert delete_response.status_code == 204
    # Verify the user is deleted
    fetch_response = await async_client.get(f"/users/{admin_user.id}", headers=headers)
    assert fetch_response.status_code == 404

@pytest.mark.asyncio
async def test_create_user_duplicate_email(async_client, verified_user):
    user_data = {
        "email": verified_user.email,
        "password": "AnotherPassword123!",
        "role": UserRole.ADMIN.name
    }
    response = await async_client.post("/register/", json=user_data)
    assert response.status_code == 400
    assert "Email already exists" in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_create_user_invalid_email(async_client):
    user_data = {
        "email": "notanemail",
        "password": "ValidPassword123!",
    }
    response = await async_client.post("/register/", json=user_data)
    assert response.status_code == 422

import pytest
from app.services.jwt_service import decode_token
from urllib.parse import urlencode

@pytest.mark.asyncio
async def test_login_success(async_client, verified_user):
    # Attempt to login with the test user
    form_data = {
        "username": verified_user.email,
        "password": "MySuperPassword$1234"
    }
    response = await async_client.post("/login/", data=urlencode(form_data), headers={"Content-Type": "application/x-www-form-urlencoded"})

    # Check for successful login response
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Use the decode_token method from jwt_service to decode the JWT
    decoded_token = decode_token(data["access_token"])
    assert decoded_token is not None, "Failed to decode token"
    assert decoded_token["role"] == "AUTHENTICATED", "The user role should be AUTHENTICATED"

@pytest.mark.asyncio
async def test_login_user_not_found(async_client):
    form_data = {
        "username": "nonexistentuser@here.edu",
        "password": "DoesNotMatter123!"
    }
    response = await async_client.post("/login/", data=urlencode(form_data), headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert response.status_code == 401
    assert "Incorrect email or password." in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_login_incorrect_password(async_client, verified_user):
    form_data = {
        "username": verified_user.email,
        "password": "IncorrectPassword123!"
    }
    response = await async_client.post("/login/", data=urlencode(form_data), headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert response.status_code == 401
    assert "Incorrect email or password." in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_login_unverified_user(async_client, unverified_user):
    form_data = {
        "username": unverified_user.email,
        "password": "MySuperPassword$1234"
    }
    response = await async_client.post("/login/", data=urlencode(form_data), headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_login_locked_user(async_client, locked_user):
    form_data = {
        "username": locked_user.email,
        "password": "MySuperPassword$1234"
    }
    response = await async_client.post("/login/", data=urlencode(form_data), headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert response.status_code == 400
    assert "Account locked due to too many failed login attempts." in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_delete_user_does_not_exist(async_client, admin_token):
    non_existent_user_id = "00000000-0000-0000-0000-000000000000"  # Valid UUID format
    headers = {"Authorization": f"Bearer {admin_token}"}
    delete_response = await async_client.delete(f"/users/{non_existent_user_id}", headers=headers)
    assert delete_response.status_code == 404

@pytest.mark.asyncio
async def test_update_user_github(async_client, admin_user, admin_token):
    updated_data = {"github_profile_url": "http://www.github.com/kaw393939"}
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.put(f"/users/{admin_user.id}", json=updated_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["github_profile_url"] == updated_data["github_profile_url"]

@pytest.mark.asyncio
async def test_update_user_linkedin(async_client, admin_user, admin_token):
    updated_data = {"linkedin_profile_url": "http://www.linkedin.com/kaw393939"}
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.put(f"/users/{admin_user.id}", json=updated_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["linkedin_profile_url"] == updated_data["linkedin_profile_url"]

@pytest.mark.asyncio
async def test_list_users_as_admin(async_client, admin_token):
    response = await async_client.get(
        "/users/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert 'items' in response.json()

@pytest.mark.asyncio
async def test_list_users_as_manager(async_client, manager_token):
    response = await async_client.get(
        "/users/",
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_list_users_unauthorized(async_client, user_token):
    response = await async_client.get(
        "/users/",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403  # Forbidden, as expected for regular user

# New tests for Phase 5: /users/me endpoints

@pytest.mark.asyncio
async def test_get_current_user_profile_success(async_client, user, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await async_client.get("/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    # The token corresponds to 'user' fixture, ensure data matches
    assert data["id"] == str(user.id)
    assert data["email"] == user.email
    assert data["role"] == user.role.name

@pytest.mark.asyncio
async def test_get_current_user_profile_unauthorized(async_client):
    # No token
    response = await async_client.get("/users/me")
    assert response.status_code == 401
    # Invalid token
    headers = {"Authorization": "Bearer invalidtoken"}
    response = await async_client.get("/users/me", headers=headers)
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_update_current_user_profile_success(async_client, user, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    new_data = {"first_name": "NewName", "last_name": "NewLast"}
    response = await async_client.put("/users/me", json=new_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "NewName"
    assert data["last_name"] == "NewLast"
    # Role remains unchanged
    assert data["role"] == user.role.name

@pytest.mark.asyncio
async def test_update_current_user_profile_no_fields(async_client, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    # No fields provided – should fail validation (422)
    response = await async_client.put("/users/me", json={}, headers=headers)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_update_current_user_profile_conflict_email(async_client, user, verified_user, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    # Attempt to change email to one already used by verified_user
    conflict_email = verified_user.email
    response = await async_client.put("/users/me", json={"email": conflict_email}, headers=headers)
    # The service returns None on conflict, our route returns 404
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

@pytest.mark.asyncio
async def test_update_current_user_profile_ignore_role(async_client, user, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    # Attempt to change role (should be ignored)
    response = await async_client.put("/users/me", json={"role": "ADMIN"}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == user.role.name  # still original role

@pytest.mark.asyncio
async def test_update_profile_picture_success(async_client, user, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    image_content = b"fakeimagecontent"
    files = {"profile_picture": ("test.png", image_content, "image/png")}
    response = await async_client.patch("/users/me/profile-picture", files=files, headers=headers)
    assert response.status_code == 200
    data = response.json()
    # profile_picture_url should be set to our static path
    assert "profile_picture_url" in data and data["profile_picture_url"]
    assert "/profile_pictures/" in data["profile_picture_url"]
    # Verify file saved
    filename = data["profile_picture_url"].split("/profile_pictures/")[-1]
    import os
    assert os.path.exists(os.path.join("profile_pictures", filename))

@pytest.mark.asyncio
async def test_update_profile_picture_invalid_type(async_client, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    # Upload a text file as profile picture (invalid)
    files = {"profile_picture": ("test.txt", b"notanimage", "text/plain")}
    response = await async_client.patch("/users/me/profile-picture", files=files, headers=headers)
    assert response.status_code == 400
    assert "Unsupported file type" in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_update_profile_picture_replace(async_client, user, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    # First upload a PNG
    files1 = {"profile_picture": ("pic.png", b"img1", "image/png")}
    response1 = await async_client.patch("/users/me/profile-picture", files=files1, headers=headers)
    assert response1.status_code == 200
    url1 = response1.json()["profile_picture_url"]
    filename1 = url1.split("/profile_pictures/")[-1]
    # Then upload a JPEG, which should replace the previous image file
    files2 = {"profile_picture": ("pic.jpg", b"img2", "image/jpeg")}
    response2 = await async_client.patch("/users/me/profile-picture", files=files2, headers=headers)
    assert response2.status_code == 200
    url2 = response2.json()["profile_picture_url"]
    filename2 = url2.split("/profile_pictures/")[-1]
    assert filename2 != filename1  # extension changed, so different filename
    import os
    # New file exists...
    assert os.path.exists(os.path.join("profile_pictures", filename2))
    # ...old file removed
    assert not os.path.exists(os.path.join("profile_pictures", filename1))
