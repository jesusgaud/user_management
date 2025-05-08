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
    monkeypatch.setattr(deps, "decode_token", lambda token: {"user_id": "user123", "role": "AUTHENTICATED"})
    current_user = deps.get_current_user(token="fake")
    assert current_user == {"user_id": "user123", "role": "AUTHENTICATED"}

def test_require_role_enforcement():
    from app.dependencies import require_role
    role_checker = require_role(["ADMIN", "MANAGER"])
    with pytest.raises(HTTPException) as exc:
        role_checker(current_user={"role": "AUTHENTICATED"})
    assert exc.value.status_code == 403
    result = role_checker(current_user={"role": "ADMIN"})
    assert result == {"role": "ADMIN"}

def test_email_service_send_user_email(monkeypatch):
    from app.services import email_service
    dummy_tmpl = types.SimpleNamespace(render_template=lambda t, **k: "<p>Email</p>")
    es = email_service.EmailService(template_manager=dummy_tmpl)
    es.smtp_client.send_email = lambda subject, html, email: None

    # Test valid email type (should pass silently)
    es.send_user_email({"email": "user@example.com"}, "email_verification")

    # Monkeypatch class-level TEMPLATE_MAP for invalid test
    monkeypatch.setitem(email_service.EmailService.TEMPLATE_MAP, "invalid_type", None)
    with pytest.raises(ValueError):
        es.send_user_email({"email": "user@example.com"}, "invalid_type")

@pytest.mark.asyncio
async def test_exception_handler():
    from app.main import exception_handler
    response = await exception_handler(None, Exception("Boom"))
    assert response.status_code == 500
    data = json.loads(response.body.decode())
    assert data["message"] == "An unexpected error occurred."
