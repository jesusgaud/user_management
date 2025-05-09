import os, json, types, asyncio, uuid
import pytest
from fastapi import HTTPException

def test_get_current_user_invalid_token(monkeypatch):
    import app.dependencies as deps
    # Token decoding returns None -> should raise 401
    monkeypatch.setattr(deps, "decode_token", lambda token: None)
    with pytest.raises(HTTPException) as exc:
        deps.get_current_user(token="fake")
    assert exc.value.status_code == 401

    # Token decoded but missing fields -> should raise 401
    monkeypatch.setattr(deps, "decode_token", lambda token: {})
    with pytest.raises(HTTPException) as exc:
        deps.get_current_user(token="fake")
    assert exc.value.status_code == 401

    # Valid token payload -> should return user dict
    monkeypatch.setattr(deps, "decode_token", lambda token: {"sub": "user123", "role": "AUTHENTICATED"})
    current_user = deps.get_current_user(token="fake")
    assert current_user == {"user_id": "user123", "role": "AUTHENTICATED"}

def test_require_role_enforcement():
    from app.dependencies import require_role
    role_checker = require_role(["ADMIN", "MANAGER"])
    # Role not allowed -> raises 403
    with pytest.raises(HTTPException) as exc:
        role_checker(current_user={"role": "AUTHENTICATED"})
    assert exc.value.status_code == 403
    # Allowed role -> returns current_user dict
    result = role_checker(current_user={"role": "ADMIN"})
    assert result == {"role": "ADMIN"}

def test_enhanced_pagination_add_link():
    from app.schemas.pagination_schema import EnhancedPagination
    pag = EnhancedPagination(page=1, per_page=10, total_items=50, total_pages=5)
    # Add a pagination link and verify it is added correctly
    pag.add_link("next", "http://example.com/page/2")
    assert pag.links and pag.links[-1].rel == "next" and str(pag.links[-1].href) == "http://example.com/page/2"

@pytest.mark.asyncio
async def test_user_service_update_no_fields():
    from app.services.user_service import UserService
    # Update data with no actual updatable fields (only 'role' which is protected)
    result = await UserService.update(session=types.SimpleNamespace(), user_id=uuid.uuid4(), update_data={"role": "ADMIN"})
    assert result is None

@pytest.mark.asyncio
async def test_user_service_create_duplicate(monkeypatch):
    from app.services.user_service import UserService
    # Simulate duplicate email scenario for user creation
    async def dummy_get_by_email(session, email):
        return object()  # return a non-None value to indicate user exists
    monkeypatch.setattr(UserService, "get_by_email", dummy_get_by_email)
    # Prepare minimal valid user data
    user_data = {"email": "duplicate@example.com", "password": "ValidPass123!", "nickname": "dupUser"}
    # Use a dummy EmailService to avoid actual email sending
    class DummyEmailService:
        async def send_verification_email(self, user):
            return None
    dummy_email_service = DummyEmailService()
    result = await UserService.create(session=types.SimpleNamespace(), user_data=user_data, email_service=dummy_email_service)
    assert result is None

@pytest.mark.asyncio
async def test_exception_handler():
    from app.main import exception_handler
    # Simulate a generic server exception
    response = await exception_handler(None, Exception("Boom"))
    assert response.status_code == 500
    data = json.loads(response.body.decode())
    assert data["message"] == "An unexpected error occurred."

@pytest.mark.asyncio
async def test_startup_event(monkeypatch):
    import app.main as main
    # Monkeypatch Database to avoid real DB calls
    class DummyDB:
        init_args = None
        create_called = False
        @classmethod
        def initialize(cls, url, debug):
            DummyDB.init_args = (url, debug)
        @classmethod
        async def create_tables(cls):
            DummyDB.create_called = True
    monkeypatch.setattr(main, "Database", DummyDB)

    # Monkeypatch get_settings to provide dummy settings
    class DummySettings:
        database_url = "sqlite+aiosqlite:///:memory:"
        debug = False
    monkeypatch.setattr(main, "get_settings", lambda: DummySettings())

    # Remove profile_pictures dir if exists to test creation
    if os.path.isdir("profile_pictures"):
        try:
            os.rmdir("profile_pictures")
        except OSError:
            pass

    # Call the startup event function
    await main.startup_event()
    # Verify Database.initialize called with correct parameters
    assert DummyDB.init_args == (DummySettings.database_url, DummySettings.debug)
    # Verify that create_tables() was called
    assert DummyDB.create_called is True
    # Verify profile_pictures directory is created
    assert os.path.isdir("profile_pictures")

@pytest.mark.asyncio
async def test_verify_email_route():
    from app.routers import user_routes
    # Directly call the verify_email route function with dummy dependencies
    dummy_session = types.SimpleNamespace()
    dummy_email_service = types.SimpleNamespace()
    response = await user_routes.verify_email(user_id=uuid.uuid4(), token="dummy-token", db=dummy_session, email_service=dummy_email_service)
    assert response == {"message": "Email verified successfully."}
