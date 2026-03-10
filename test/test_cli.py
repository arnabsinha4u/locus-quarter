from __future__ import annotations

from click.testing import CliRunner

from locus_quarter_app.cli import main
from locus_quarter_app.interfaces import FeedEntry
from locus_quarter_app.models import AppConfig, EmailConfig, QueryConfig
from test.fakes import FakeFeedClient, FakeMailClient, FakeMapsClient


def _config() -> AppConfig:
    return AppConfig(
        query=QueryConfig(
            regions_urls=["https://example.test/feed"],
            nearby_place_types=["school"],
            travel_modes=["walking"],
            limit_houses=1,
            limit_search_places_nearby=1,
            office_addresses=[],
            office_travel_modes=[],
        ),
        maps_api_key="fake",
        email=EmailConfig(
            secrets_path=".",
            token_json="token.json",
            action_scope="https://www.googleapis.com/auth/gmail.send",
            client_secret_file=None,
            application_name="lq",
            receiver_mail_address="to@example.com",
            sender_mail_address="from@example.com",
            email_subject="LQ",
        ),
        raw_config_path="config-mini-locus-quarter.ini",
    )


def test_cli_json_output(monkeypatch) -> None:
    runner = CliRunner()

    monkeypatch.setattr("locus_quarter_app.cli.ConfigLoader.load", lambda self: _config())
    monkeypatch.setattr(
        "locus_quarter_app.cli.FeedParserClient", lambda: FakeFeedClient(entries=[])
    )
    monkeypatch.setattr("locus_quarter_app.cli.GoogleMapsClient", lambda api_key: FakeMapsClient())

    result = runner.invoke(main, ["--format", "json", "--no-save-artifacts"])
    assert result.exit_code == 0
    assert '"mode": "feed"' in result.output


def test_cli_sends_email_when_requested(monkeypatch) -> None:
    runner = CliRunner()
    fake_mail = FakeMailClient()

    monkeypatch.setattr("locus_quarter_app.cli.ConfigLoader.load", lambda self: _config())
    monkeypatch.setattr(
        "locus_quarter_app.cli.FeedParserClient",
        lambda: FakeFeedClient(
            entries=[
                FeedEntry(title="Te koop: A", link="x", summary="80 m2", published="today"),
            ]
        ),
    )
    monkeypatch.setattr("locus_quarter_app.cli.GoogleMapsClient", lambda api_key: FakeMapsClient())
    monkeypatch.setattr("locus_quarter_app.cli.GmailClient", lambda cfg: fake_mail)

    result = runner.invoke(main, ["--email", "--no-save-artifacts"])
    assert result.exit_code == 0
    assert fake_mail.sent is True
