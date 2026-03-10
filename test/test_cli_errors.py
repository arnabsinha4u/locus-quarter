from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from locus_quarter_app.cli import main
from locus_quarter_app.config import ConfigError
from locus_quarter_app.models import AppConfig, EmailConfig, QueryConfig, RunArtifact
from locus_quarter_app.reporting import Reporter
from test.fakes import FakeFeedClient, FakeMapsClient


def _config(
    receiver: str | None = "to@example.com", sender: str | None = "from@example.com"
) -> AppConfig:
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
            receiver_mail_address=receiver,
            sender_mail_address=sender,
            email_subject="LQ",
        ),
        raw_config_path="config-mini-locus-quarter.ini",
    )


def test_cli_returns_2_for_config_error(monkeypatch) -> None:
    def _raise_config_error(self):
        raise ConfigError("bad config")

    monkeypatch.setattr("locus_quarter_app.cli.ConfigLoader.load", _raise_config_error)
    result = CliRunner().invoke(main, [])
    assert result.exit_code == 2


def test_cli_returns_1_and_json_error_for_unhandled_exception(monkeypatch) -> None:
    class _FakeLoader:
        def __init__(self, path: str):  # noqa: ARG002
            pass

        def load(self):
            raise RuntimeError("boom")

    monkeypatch.setattr("locus_quarter_app.cli.ConfigLoader", _FakeLoader)
    result = CliRunner().invoke(main, ["--format", "json"])
    assert result.exit_code == 1
    assert '"error": "boom"' in result.output


def test_cli_writes_artifacts_when_enabled(monkeypatch) -> None:
    monkeypatch.setattr("locus_quarter_app.cli.ConfigLoader.load", lambda self: _config())
    monkeypatch.setattr(
        "locus_quarter_app.cli.FeedParserClient", lambda: FakeFeedClient(entries=[])
    )
    monkeypatch.setattr("locus_quarter_app.cli.GoogleMapsClient", lambda api_key: FakeMapsClient())
    monkeypatch.setattr(
        "locus_quarter_app.cli.Reporter.write_artifacts",
        lambda output_dir, artifact, text: (Path("a.json"), Path("a.txt")),
    )

    result = CliRunner().invoke(main, [])
    assert result.exit_code == 0


def test_cli_no_print_metrics_branch(monkeypatch) -> None:
    monkeypatch.setattr("locus_quarter_app.cli.ConfigLoader.load", lambda self: _config())
    monkeypatch.setattr(
        "locus_quarter_app.cli.FeedParserClient", lambda: FakeFeedClient(entries=[])
    )
    monkeypatch.setattr("locus_quarter_app.cli.GoogleMapsClient", lambda api_key: FakeMapsClient())
    result = CliRunner().invoke(main, ["--no-print-metrics", "--no-save-artifacts"])
    assert result.exit_code == 0


def test_cli_email_requires_sender_receiver(monkeypatch) -> None:
    monkeypatch.setattr("locus_quarter_app.cli.ConfigLoader.load", lambda self: _config(None, None))
    monkeypatch.setattr(
        "locus_quarter_app.cli.FeedParserClient", lambda: FakeFeedClient(entries=[])
    )
    monkeypatch.setattr("locus_quarter_app.cli.GoogleMapsClient", lambda api_key: FakeMapsClient())
    result = CliRunner().invoke(main, ["--email", "--no-save-artifacts"])
    assert result.exit_code == 2


def test_cli_exits_when_metrics_contains_errors(monkeypatch) -> None:
    class _FailingService:
        def __init__(self, config, feed_client, maps_client):  # noqa: ARG002
            pass

        @staticmethod
        def run(address=None, trigger="manual"):  # noqa: ARG004
            artifact = RunArtifact.new(mode="feed", trigger=trigger)
            artifact.metrics.errors = 1
            artifact.finalize()
            reporter = Reporter()
            reporter.add("x")
            return artifact, reporter

    monkeypatch.setattr("locus_quarter_app.cli.ConfigLoader.load", lambda self: _config())
    monkeypatch.setattr("locus_quarter_app.cli.LocusQuarterService", _FailingService)
    monkeypatch.setattr(
        "locus_quarter_app.cli.FeedParserClient", lambda: FakeFeedClient(entries=[])
    )
    monkeypatch.setattr("locus_quarter_app.cli.GoogleMapsClient", lambda api_key: FakeMapsClient())
    result = CliRunner().invoke(main, ["--no-save-artifacts", "--no-print-metrics"])
    assert result.exit_code == 1
