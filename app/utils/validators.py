import re

def validate_email_address(email: str) -> None:
    """Validate email address format. Raise ValueError if invalid."""
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(email_regex, email):
        raise ValueError("Invalid email format")

