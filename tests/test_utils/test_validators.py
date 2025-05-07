import pytest
from app.utils.validators import validate_email_address

@pytest.mark.parametrize("email", [
    "valid@example.com",
    "first.last@domain.co",
    "email@sub.domain.com"
])
def test_validate_email_address_valid(email):
    assert validate_email_address(email) is None

@pytest.mark.parametrize("email", [
    "invalid-email",
    "missing@domain",
    "@missinguser.com",
    "user@.com",
    ""
])
def test_validate_email_address_invalid(email):
    with pytest.raises(ValueError, match="Invalid email format"):
        validate_email_address(email)
