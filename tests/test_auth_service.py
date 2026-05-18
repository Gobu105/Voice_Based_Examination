import os
from unittest.mock import MagicMock, patch

from app.services import auth_service


def test_get_email_verification_url_uses_app_base_url():
    os.environ["APP_BASE_URL"] = "http://example.com/"
    assert auth_service.get_email_verification_url("token123") == "http://example.com/verify_email/token123"


def test_get_email_verification_url_defaults_to_localhost():
    os.environ.pop("APP_BASE_URL", None)
    assert auth_service.get_email_verification_url("token123") == "http://localhost:5005/verify_email/token123"


def test_send_verification_email_prints_url_when_no_mail_server(monkeypatch, capsys):
    monkeypatch.delenv("MAIL_SERVER", raising=False)
    monkeypatch.setenv("APP_BASE_URL", "http://localhost:5005")

    user = {
        "verification_token": "abc123",
        "email": "user@example.com",
        "full_name": "Test User",
    }

    result = auth_service.send_verification_email(user)
    captured = capsys.readouterr()

    assert "verify_email/abc123" in result
    assert "EMAIL VERIFICATION URL:" in captured.out


def test_send_verification_email_uses_smtp(monkeypatch):
    monkeypatch.setenv("MAIL_SERVER", "smtp.example.com")
    monkeypatch.setenv("MAIL_PORT", "587")
    monkeypatch.setenv("MAIL_USE_TLS", "true")
    monkeypatch.setenv("MAIL_FROM", "from@example.com")

    user = {
        "verification_token": "abc123",
        "email": "user@example.com",
        "full_name": "Test User",
    }

    with patch("app.services.auth_service.smtplib.SMTP") as smtp_mock:
        smtp_instance = smtp_mock.return_value.__enter__.return_value
        smtp_instance.send_message = MagicMock()
        smtp_instance.starttls = MagicMock()

        result = auth_service.send_verification_email(user)

        smtp_mock.assert_called_once_with("smtp.example.com", 587, timeout=15)
        smtp_instance.starttls.assert_called_once()
        smtp_instance.send_message.assert_called_once()
        assert result.endswith("/verify_email/abc123")


def test_verify_session_for_role_returns_true_for_active_verified_user(monkeypatch):
    expected_user = {
        "_id": 7,
        "role": "ADMIN",
        "is_active": True,
        "email_verified": True,
    }

    class FakeUsers:
        def find_one(self, query):
            if query.get("_id") == expected_user["_id"]:
                return expected_user
            return None

    class FakeDB:
        users = FakeUsers()

    monkeypatch.setattr(auth_service, "get_db", lambda: FakeDB())

    assert auth_service.verify_session_for_role("ADMIN", {"user_id": 7}) is True


def test_verify_email_token_updates_user_and_returns_user(monkeypatch):
    stored_user = {
        "_id": 15,
        "verification_token": "token123",
        "email_verified": False,
    }

    class FakeUsers:
        def find_one(self, query):
            if query.get("verification_token") == stored_user["verification_token"]:
                return stored_user
            return None

        def update_one(self, query, update):
            stored_user.update(update["$set"])

    class FakeDB:
        users = FakeUsers()

    monkeypatch.setattr(auth_service, "get_db", lambda: FakeDB())

    user = auth_service.verify_email_token("token123")
    assert user is not None
    assert user["email_verified"] is True
    assert user["verification_token"] is None
    assert "verified_at" in user
