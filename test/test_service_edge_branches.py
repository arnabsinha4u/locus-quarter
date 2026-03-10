from __future__ import annotations

from typing import Any

from locus_quarter_app.interfaces import FeedEntry
from locus_quarter_app.models import AppConfig, EmailConfig, QueryConfig
from locus_quarter_app.service import LocusQuarterService, _SummaryParser
from test.fakes import FakeFeedClient


def _config(
    nearby_limit: int = 2,
    office_addresses: list[str] | None = None,
    office_modes: list[str] | None = None,
) -> AppConfig:
    return AppConfig(
        query=QueryConfig(
            regions_urls=["https://example.test/feed"],
            nearby_place_types=["school"],
            travel_modes=["walking"],
            limit_houses=1,
            limit_search_places_nearby=nearby_limit,
            office_addresses=office_addresses or [],
            office_travel_modes=office_modes or [],
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


class _EdgeNearbyMapsClient:
    @staticmethod
    def geocode(address: str) -> tuple[dict[str, float], str]:
        return {"lat": 1.0, "lng": 2.0}, address

    @staticmethod
    def places_nearby(location: dict[str, float], place_type: str) -> list[dict[str, Any]]:  # noqa: ARG004
        return [
            {"name": "missing-location", "geometry": {}},
            {"name": "missing-distance", "geometry": {"location": {"lat": 1.1, "lng": 2.2}}},
        ]

    @staticmethod
    def distance_matrix(origins: dict[str, float], mode: str, destinations):  # noqa: ARG004
        if isinstance(destinations, list):
            return {"destination_addresses": destinations, "rows": [{"elements": []}]}
        return {"rows": [{"elements": [{}]}]}


def test_summary_parser_edge_paths() -> None:
    parser = _SummaryParser()
    parser.handle_data("   ")
    parser.handle_data("plain text")
    parser.handle_data(".")
    assert parser.lines == []


def test_service_warns_for_missing_nearby_location_and_distance_data() -> None:
    service = LocusQuarterService(
        config=_config(),
        feed_client=FakeFeedClient(
            entries=[FeedEntry(title="Te koop: X", link="link", summary="80 m2", published="today")]
        ),
        maps_client=_EdgeNearbyMapsClient(),
    )
    artifact, reporter = service.run()
    text = reporter.render_text()
    assert artifact.metrics.warnings >= 2
    assert "missing location for nearby place" in text
    assert "distance data missing for travel mode" in text


class _OfficeRowsMissingMapsClient:
    @staticmethod
    def geocode(address: str) -> tuple[dict[str, float], str]:
        return {"lat": 1.0, "lng": 2.0}, address

    @staticmethod
    def places_nearby(location: dict[str, float], place_type: str) -> list[dict[str, Any]]:  # noqa: ARG004
        return []

    @staticmethod
    def distance_matrix(origins: dict[str, float], mode: str, destinations):  # noqa: ARG004
        if isinstance(destinations, list):
            return {"destination_addresses": destinations, "rows": []}
        return {
            "rows": [{"elements": [{"distance": {"text": "1 km"}, "duration": {"text": "2 mins"}}]}]
        }


def test_service_warns_when_office_rows_missing() -> None:
    service = LocusQuarterService(
        config=_config(nearby_limit=0, office_addresses=["Office 1"], office_modes=["driving"]),
        feed_client=FakeFeedClient(
            entries=[FeedEntry(title="Te koop: X", link="link", summary="80 m2", published="today")]
        ),
        maps_client=_OfficeRowsMissingMapsClient(),
    )
    artifact, reporter = service.run()
    assert artifact.metrics.warnings >= 1
    assert "office distance row data missing" in reporter.render_text()


class _OfficeElementsMissingMapsClient:
    @staticmethod
    def geocode(address: str) -> tuple[dict[str, float], str]:
        return {"lat": 1.0, "lng": 2.0}, address

    @staticmethod
    def places_nearby(location: dict[str, float], place_type: str) -> list[dict[str, Any]]:  # noqa: ARG004
        return []

    @staticmethod
    def distance_matrix(origins: dict[str, float], mode: str, destinations):  # noqa: ARG004
        if isinstance(destinations, list):
            return {
                "destination_addresses": destinations,
                "rows": [{"elements": [{}]}],
            }
        return {
            "rows": [{"elements": [{"distance": {"text": "1 km"}, "duration": {"text": "2 mins"}}]}]
        }


def test_service_warns_when_office_distance_fields_missing() -> None:
    service = LocusQuarterService(
        config=_config(nearby_limit=0, office_addresses=["Office 1"], office_modes=["driving"]),
        feed_client=FakeFeedClient(
            entries=[FeedEntry(title="Te koop: X", link="link", summary="80 m2", published="today")]
        ),
        maps_client=_OfficeElementsMissingMapsClient(),
    )
    artifact, reporter = service.run()
    assert artifact.metrics.warnings >= 1
    assert "office distance data missing" in reporter.render_text()


def test_first_element_returns_none_when_first_row_is_not_dict() -> None:
    assert LocusQuarterService._first_element({"rows": ["invalid"]}) is None
