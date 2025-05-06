import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4
from app.main import app  # assuming the FastAPI app is created in app.main
from app.services.user_service import UserService

@pytest.mark.anyio
@pytest.fixture
async def setup_users():
    """Fixture to create a test admin and a normal user, and return their tokens and info."""
    # Use unique emails for test isolation
    admin_email = f"admin_{uuid4().hex[:6]}@example.com"
    user_email  = f"user_{uuid4().hex[:6]}@example.com"
    password = "TestPass123!"  # sample password for both

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        # 1. Register admin (first registered user becomes ADMIN by service logic)
        admin_payload = {"email": admin_email, "password": password}
        res1 = await ac.post("/register/", json=admin_payload)
        assert res1.status_code == 201, "Admin registration failed"
        admin_data = res1.json()
        assert admin_data["role"] == "ADMIN"
        # 2. Register normal user (will initially have role ANONYMOUS until verified)
        user_payload = {"email": user_email, "password": password}
        res2 = await ac.post("/register/", json=user_payload)
        assert res2.status_code == 201, "User registration failed"
        user_data = res2.json()
        # Ensure the normal user is created with ANONYMOUS role (unverified)
        assert user_data["role"] == "ANONYMOUS"

        # 3. Verify the normal user's email (simulate clicking verification link)
        # Fetch the verification token from the database (since email sending is disabled in tests)
        user_uuid = UUID(user_data["id"])
        # Use the service or direct DB query to get the token
        async with app.dependency_overrides[get_db]() as session:
            test_user = await UserService.get_by_id(session, user_uuid)
            token = test_user.verification_token
        verify_res = await ac.get(f"/verify-email/{user_data['id']}/{token}")
        assert verify_res.status_code == 200
        # After verification, the user's role should now be 'AUTHENTICATED'
        async with app.dependency_overrides[get_db]() as session:
            verified_user = await UserService.get_by_id(session, user_uuid)
            assert verified_user.email_verified is True
            assert str(verified_user.role.name) == "AUTHENTICATED"

        # 4. Log in both users to get tokens
        login_data = {"username": admin_email, "password": password}
        res3 = await ac.post("/login/", data=login_data)
        assert res3.status_code == 200, "Admin login failed"
        admin_token = res3.json()["access_token"]
        login_data = {"username": user_email, "password": password}
        res4 = await ac.post("/login/", data=login_data)
        assert res4.status_code == 200, "User login failed (possibly not verified)"
        user_token = res4.json()["access_token"]

    # Yield tokens and user info for use in tests
    return {
        "admin_token": admin_token,
        "admin_email": admin_email,
        "admin_id": admin_data["id"],
        "user_token": user_token,
        "user_email": user_email,
        "user_id": user_data["id"]  # user_data from before verification, ID remains same
    }

@pytest.mark.anyio
async def test_get_profile_me_success(setup_users):
    """Authenticated user should retrieve their own profile successfully."""
    tokens = setup_users
    user_token = tokens["user_token"]
    user_email = tokens["user_email"]

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        # Call GET /users/me with user's token
        response = await ac.get("/users/me", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    profile = response.json()
    # Check that the profile data matches the logged-in user
    assert profile["email"] == user_email
    assert profile["nickname"] is not None  # Nickname is generated on registration
    assert profile["role"] in ["AUTHENTICATED", "ADMIN"]  # the user should now be AUTHENTICATED
    # The response should include HATEOAS links
    assert "links" in profile and "self" in profile["links"]

@pytest.mark.anyio
async def test_get_profile_me_unauthorized():
    """Without a token, accessing /users/me should return 401 Unauthorized."""
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get("/users/me")  # no Authorization header
    assert response.status_code == 401
    detail = response.json().get("detail", "")
    assert "credentials" in detail or "Not authenticated" in detail

@pytest.mark.anyio
async def test_update_profile_me_success(setup_users):
    """User can update their own profile fields."""
    tokens = setup_users
    user_token = tokens["user_token"]
    user_id = tokens["user_id"]

    # Prepare an update payload (e.g., first_name and bio)
    update_payload = {
        "first_name": "UpdatedName",
        "bio": "Updated bio text"
    }
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.patch("/users/me", json=update_payload,
                                  headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    data = response.json()
    # The response should reflect the changes
    assert data["first_name"] == "UpdatedName"
    assert data["bio"] == "Updated bio text"
    # Unchanged fields (e.g., email) should remain the same and present
    assert data["email"] == tokens["user_email"]
    # Verify that the change is persisted by retrieving profile again
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        res2 = await ac.get("/users/me", headers={"Authorization": f"Bearer {user_token}"})
    profile = res2.json()
    assert profile["first_name"] == "UpdatedName" and profile["bio"] == "Updated bio text"

@pytest.mark.anyio
async def test_update_profile_me_no_fields(setup_users):
    """PATCH /users/me with no fields should be rejected (422) by validation."""
    user_token = setup_users["user_token"]
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        # Send an empty JSON object
        response = await ac.patch("/users/me", json={}, headers={"Authorization": f"Bearer {user_token}"})
    # Expect a 422 Unprocessable Entity due to root_validator enforcing at least one field
    assert response.status_code == 422
    detail = response.json()["detail"]
    # The validation error should mention that at least one field is required
    assert any("At least one field must be provided" in err["msg"] for err in detail)

@pytest.mark.anyio
async def test_update_profile_invalid_data(setup_users):
    """Invalid profile data (e.g., bad format URL) should result in 422 validation error."""
    user_token = setup_users["user_token"]
    # Provide an improperly formatted URL for linkedin_profile_url
    bad_data = {"linkedin_profile_url": "not-a-valid-url"}
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.patch("/users/me", json=bad_data, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 422
    errors = response.json()["detail"]
    # We expect a validation error for the URL format
    assert any(err["loc"][-1] == "linkedin_profile_url" for err in errors)
    assert any("Invalid URL format" in err.get("msg", "") for err in errors)

@pytest.mark.anyio
async def test_user_cannot_change_role(setup_users):
    """A normal user should not be allowed to change their role via profile update."""
    user_token = setup_users["user_token"]
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        # Attempt to upgrade role to ADMIN via profile patch
        response = await ac.patch("/users/me", json={"role": "ADMIN"},
                                  headers={"Authorization": f"Bearer {user_token}"})
    # The dependency/route logic should forbid this
    assert response.status_code == 403
    detail = response.json()["detail"]
    assert "not permitted" in detail or "forbidden" in detail.lower()

@pytest.mark.anyio
async def test_user_cannot_access_others_profile(setup_users):
    """A normal user token cannot use admin-only endpoints to access or modify others' profiles."""
    tokens = setup_users
    user_token = tokens["user_token"]
    admin_id = tokens["admin_id"]

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        # Normal user tries to GET another user's data by ID (admin's profile)
        res1 = await ac.get(f"/users/{admin_id}", headers={"Authorization": f"Bearer {user_token}"})
        # Normal user tries to PUT update another user's data
        res2 = await ac.put(f"/users/{admin_id}", json={"first_name": "Hacker"},
                             headers={"Authorization": f"Bearer {user_token}"})
    # Both should be forbidden because require_role on those endpoints only allows ADMIN/MANAGER
    assert res1.status_code == 403
    assert res2.status_code == 403

@pytest.mark.anyio
async def test_admin_can_get_and_update_others_profile(setup_users):
    """Admin user should be able to retrieve and update another user's profile via admin endpoints."""
    tokens = setup_users
    admin_token = tokens["admin_token"]
    normal_user_id = tokens["user_id"]

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        # Admin fetching another user's profile
        res1 = await ac.get(f"/users/{normal_user_id}", headers={"Authorization": f"Bearer {admin_token}"})
        # Admin updating another user's profile (e.g., changing first_name)
        update_data = {"first_name": "AdminEdit"}
        res2 = await ac.put(f"/users/{normal_user_id}", json=update_data,
                             headers={"Authorization": f"Bearer {admin_token}"})
    assert res1.status_code == 200
    user_info = res1.json()
    assert user_info["id"] == normal_user_id
    # The user fetched by admin should have role AUTHENTICATED (since we verified them in setup)
    assert user_info["role"] == "AUTHENTICATED"
    assert res2.status_code == 200
    updated = res2.json()
    # The first_name should be updated to "AdminEdit"
    assert updated["first_name"] == "AdminEdit"
    # Ensure that the change is reflected if the user fetches their profile
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        res3 = await ac.get("/users/me", headers={"Authorization": f"Bearer {tokens['user_token']}"})
    profile = res3.json()
    assert profile["first_name"] == "AdminEdit"
