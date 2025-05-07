# tests/test_additional_coverage.py
import os, json, types, asyncio
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

def test_email_service_send_user_email(monkeypatch):
    from app.services import email_service
    # Setup EmailService with dummy TemplateManager and SMTP client
    dummy_tmpl = types.SimpleNamespace(render_template=lambda t, **k: "<p>Email</p>")
    es = email_service.EmailService(template_manager=dummy_tmpl)
    es.smtp_client.send_email = lambda subject, html, email: None  # no-op
    # Valid email_type -> should not raise
    es.send_user_email({"email": "user@example.com"}, "email_verification")
    # Invalid email_type -> should raise ValueError
    with pytest.raises(ValueError):
        es.send_user_email({"email": "user@example.com"}, "invalid_type")

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
        init_args = None; create_called = False
        @classmethod
        def initialize(cls, url, debug):
            DummyDB.init_args = (url, debug)
        @classmethod
        async def create_tables(cls):
            DummyDB.create_called = True
    monkeypatch.setattr(main, "Database", DummyDB)

    # Monkeypatch get_settings to provide dummy DB URL
    class DummySettings:
        database_url = "sqlite+aiosqlite:///:memory:"; debug = False
    monkeypatch.setattr(main, "get_settings", lambda: DummySettings())

    # Remove profile_pictures dir if exists to test creation
    if os.path.isdir("profile_pictures"):
        try: os.rmdir("profile_pictures")
        except OSError: pass

    # Call the startup event function
    await main.startup_event()
    # Verify Database.initialize called with correct parameters
    assert DummyDB.init_args == (DummySettings.database_url, DummySettings.debug)
    # Verify that create_tables() was called
    assert DummyDB.create_called is True
    # Verify profile_pictures directory is created
    assert os.path.isdir("profile_pictures")
