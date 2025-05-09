import pytest
from app.utils.validators import validate_email_address

def test_validate_email_address_valid():
    valid_email = "example@test.com"
    assert validate_email_address(valid_email) is True

def test_validate_email_address_invalid():
    invalid_email = "not-an-email"
    assert validate_email_address(invalid_email) is False

def test_validate_email_address_empty_string():
    assert validate_email_address("") is False
