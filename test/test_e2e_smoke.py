from __future__ import annotations

from click.testing import CliRunner

from locus_quarter_app.cli import main
from locus_quarter_app.models import AppConfig, EmailConfig, QueryConfig
from test.fakes import FakeFeedClient, FakeMapsClient


def test_e2e_smoke_json_output(monkeypatch) -> None:
    config = AppConfig(
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
            receiver_mail_address=None,
            sender_mail_address=None,
            email_subject="LQ",
        ),
        raw_config_path="x",
    )
    monkeypatch.setattr("locus_quarter_app.cli.ConfigLoader.load", lambda self: config)
    monkeypatch.setattr("locus_quarter_app.cli.FeedParserClient", lambda: FakeFeedClient(entries=[]))
    monkeypatch.setattr("locus_quarter_app.cli.GoogleMapsClient", lambda api_key: FakeMapsClient())

    runner = CliRunner()
    result = runner.invoke(main, ["--format", "json", "--no-save-artifacts"])
    assert result.exit_code == 0
    assert '"records": []' in result.output
