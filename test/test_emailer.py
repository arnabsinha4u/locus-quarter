from __future__ import annotations

from locus_quarter_app.emailer import GmailClient
from locus_quarter_app.models import EmailConfig


class _FakeCreds:
    def __init__(self, valid: bool = True, expired: bool = False, refresh_token: str | None = "x"):
        self.valid = valid
        self.expired = expired
        self.refresh_token = refresh_token

    def refresh(self, request) -> None:  # noqa: ARG002
        self.valid = True

    def to_json(self) -> str:
        return '{"token": "x"}'


def _cfg(client_secret_file: str | None) -> EmailConfig:
    return EmailConfig(
        secrets_path=".",
        token_json="tmp-token.json",
        action_scope="https://www.googleapis.com/auth/gmail.send",
        client_secret_file=client_secret_file,
        application_name="lq",
        receiver_mail_address="to@example.com",
        sender_mail_address="from@example.com",
        email_subject="subject",
    )


def test_gmail_client_send_uses_existing_token(monkeypatch) -> None:
    class _FakeSendCall:
        @staticmethod
        def execute() -> dict:
            return {"id": "ok"}

    class _FakeMessages:
        @staticmethod
        def send(userId, body):  # noqa: N803, ARG004
            return _FakeSendCall()

    class _FakeUsers:
        @staticmethod
        def messages():
            return _FakeMessages()

    class _FakeService:
        @staticmethod
        def users():
            return _FakeUsers()

    monkeypatch.setattr("locus_quarter_app.emailer.os.path.exists", lambda path: True)
    monkeypatch.setattr(
        "locus_quarter_app.emailer.Credentials.from_authorized_user_file",
        lambda path, scopes: _FakeCreds(valid=True),
    )
    monkeypatch.setattr("locus_quarter_app.emailer.build", lambda *args, **kwargs: _FakeService())

    client = GmailClient(_cfg(client_secret_file=None))
    client.send("from@example.com", "to@example.com", "subject", "body")


def test_gmail_client_requires_secret_when_token_missing(monkeypatch) -> None:
    monkeypatch.setattr("locus_quarter_app.emailer.os.path.exists", lambda path: False)
    client = GmailClient(_cfg(client_secret_file=None))
    try:
        client._credentials()
    except ValueError as exc:
        assert "client secret file is required" in str(exc).lower()
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected ValueError when no token and no secret file")
