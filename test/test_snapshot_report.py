from __future__ import annotations

from pathlib import Path

from locus_quarter_app.interfaces import FeedEntry
from locus_quarter_app.models import AppConfig, EmailConfig, QueryConfig
from locus_quarter_app.service import LocusQuarterService
from test.fakes import FakeFeedClient, FakeMapsClient


def _resolve_repo_file(relative_path: str) -> Path:
    candidates = [
        Path(relative_path),
        Path(__file__).resolve().parents[1] / relative_path,
        Path(__file__).resolve().parents[2] / relative_path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not resolve repository file: {relative_path}")


def test_report_snapshot_matches_expected() -> None:
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
    service = LocusQuarterService(
        config=config,
        feed_client=FakeFeedClient(
            entries=[
                FeedEntry(
                    title="Te koop: A",
                    link="https://example.test/a",
                    summary="80 m2",
                    published="today",
                )
            ]
        ),
        maps_client=FakeMapsClient(),
    )
    _, reporter = service.run()
    expected = _resolve_repo_file("test/snapshots/report_output.txt").read_text(encoding="utf-8")
    assert reporter.render_text() == expected
