from __future__ import annotations

from locus_quarter_app.interfaces import FeedEntry
from locus_quarter_app.models import AppConfig, EmailConfig, QueryConfig
from locus_quarter_app.service import LocusQuarterService
from test.fakes import FakeFeedClient, FakeMapsClient


def _build_config() -> AppConfig:
    return AppConfig(
        query=QueryConfig(
            regions_urls=["https://example.test/feed"],
            nearby_place_types=["school"],
            travel_modes=["walking"],
            limit_houses=1,
            limit_search_places_nearby=1,
            office_addresses=["Office 1"],
            office_travel_modes=["driving"],
        ),
        maps_api_key="fake-key",
        email=EmailConfig(
            secrets_path=".",
            token_json="token.json",
            action_scope="https://www.googleapis.com/auth/gmail.send",
            client_secret_file=None,
            application_name="locus-quarter",
            receiver_mail_address=None,
            sender_mail_address=None,
            email_subject="Locus Quarter",
        ),
        raw_config_path="config-mini-locus-quarter.ini",
    )


def test_service_builds_records_and_metrics() -> None:
    config = _build_config()
    feed = FakeFeedClient(
        entries=[
            FeedEntry(
                title="Te koop: Demo Address 1",
                link="https://example.test/house/1",
                summary="80 m2",
                published="2026-03-10",
            )
        ]
    )
    service = LocusQuarterService(config=config, feed_client=feed, maps_client=FakeMapsClient())

    artifact, reporter = service.run()
    text = reporter.render_text()

    assert artifact.metrics.feed_entries_seen == 1
    assert artifact.metrics.houses_processed == 1
    assert artifact.metrics.geocode_calls == 1
    assert artifact.records
    assert "Demo Address 1" in text
    assert "Facility Type:school" in text


def test_service_warns_on_unparseable_title() -> None:
    config = _build_config()
    feed = FakeFeedClient(
        entries=[
            FeedEntry(
                title="Unexpected title format",
                link="https://example.test/house/1",
                summary="80 m2",
                published="2026-03-10",
            )
        ]
    )
    service = LocusQuarterService(config=config, feed_client=feed, maps_client=FakeMapsClient())
    artifact, reporter = service.run()
    assert artifact.metrics.warnings >= 1
    assert "unable to parse destination" in reporter.render_text().lower()
