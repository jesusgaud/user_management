import pytest
from unittest.mock import patch, MagicMock
from app.utils.smtp_connection import SMTPClient

@pytest.fixture
def smtp_client():
    return SMTPClient(
        server="smtp.example.com",
        port=587,
        username="test@example.com",
        password="securepassword"
    )

@patch("smtplib.SMTP")
def test_send_email_success(mock_smtp, smtp_client, caplog):
    # Setup mock SMTP session
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    subject = "Test Email"
    html_content = "<p>Hello World</p>"
    recipient = "recipient@example.com"

    with caplog.at_level("INFO"):
        smtp_client.send_email(subject, html_content, recipient)

    # Assertions
    mock_smtp.assert_called_once_with("smtp.example.com", 587)
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("test@example.com", "securepassword")
    mock_server.sendmail.assert_called_once()
    assert "Email sent to recipient@example.com" in caplog.text

@patch("smtplib.SMTP", side_effect=Exception("SMTP error"))
def test_send_email_failure(mock_smtp, smtp_client, caplog):
    subject = "Failing Email"
    html_content = "<p>Fail</p>"
    recipient = "fail@example.com"

    with caplog.at_level("ERROR"):
        with pytest.raises(Exception, match="SMTP error"):
            smtp_client.send_email(subject, html_content, recipient)

    assert "Failed to send email: SMTP error" in caplog.text
