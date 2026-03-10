from __future__ import annotations

from locus_quarter_app.interfaces import FeedEntry
from locus_quarter_app.models import AppConfig, EmailConfig, QueryConfig
from locus_quarter_app.service import LocusQuarterService
from test.fakes import FakeFeedClient, FakeMapsClient


def _config() -> AppConfig:
    return AppConfig(
        query=QueryConfig(
            regions_urls=["https://example.test/feed"],
            nearby_place_types=["school", "transit_station"],
            travel_modes=["walking", "bicycling"],
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


def test_address_mode_pipeline() -> None:
    service = LocusQuarterService(
        config=_config(),
        feed_client=FakeFeedClient(entries=[]),
        maps_client=FakeMapsClient(),
    )
    artifact, reporter = service.run(address="Demo Address")
    assert artifact.mode == "address"
    assert artifact.records[0]["address"].startswith("Demo Address")
    assert "Date published:manual" in reporter.render_text()


def test_feed_mode_pipeline() -> None:
    service = LocusQuarterService(
        config=_config(),
        feed_client=FakeFeedClient(
            entries=[
                FeedEntry(
                    title="Te koop: A",
                    link="https://example.test/a",
                    summary="90 m2",
                    published="today",
                )
            ]
        ),
        maps_client=FakeMapsClient(),
    )
    artifact, _ = service.run()
    assert artifact.mode == "feed"
    assert artifact.metrics.houses_processed == 1
