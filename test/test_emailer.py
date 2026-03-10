from __future__ import annotations

from pathlib import Path

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


def _cfg(client_secret_file: str | None, secrets_path: str = ".", token_json: str = "tmp-token.json") -> EmailConfig:
    return EmailConfig(
        secrets_path=secrets_path,
        token_json=token_json,
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


def test_gmail_client_refreshes_expired_token(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("locus_quarter_app.emailer.os.path.exists", lambda path: True)
    monkeypatch.setattr(
        "locus_quarter_app.emailer.Credentials.from_authorized_user_file",
        lambda path, scopes: _FakeCreds(valid=False, expired=True, refresh_token="refresh-token"),
    )
    client = GmailClient(_cfg(client_secret_file=None, secrets_path=str(tmp_path), token_json="token.json"))
    creds = client._credentials()
    assert creds.valid is True


def test_gmail_client_oauth_flow_creates_token(monkeypatch, tmp_path: Path) -> None:
    class _FakeFlow:
        @staticmethod
        def run_local_server(port: int):  # noqa: ARG004
            return _FakeCreds(valid=True)

    monkeypatch.setattr("locus_quarter_app.emailer.os.path.exists", lambda path: False)
    monkeypatch.setattr(
        "locus_quarter_app.emailer.InstalledAppFlow.from_client_secrets_file",
        lambda file, scopes: _FakeFlow(),  # noqa: ARG005
    )
    token_path = tmp_path / "oauth-token.json"
    client = GmailClient(
        _cfg(
            client_secret_file="fake-client-secret.json",
            secrets_path=str(tmp_path),
            token_json=token_path.name,
        )
    )
    creds = client._credentials()
    assert creds.valid is True
    assert token_path.exists()
