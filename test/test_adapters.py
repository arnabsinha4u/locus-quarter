from __future__ import annotations

from types import SimpleNamespace

from locus_quarter_app.adapters import FeedParserClient, GoogleMapsClient


def test_feed_parser_client_maps_entries(monkeypatch) -> None:
    payload = SimpleNamespace(
        entries=[
            SimpleNamespace(
                title="Te koop: House A",
                link="https://example.test/a",
                summary="80 m2",
                published="today",
            )
        ]
    )
    monkeypatch.setattr("locus_quarter_app.adapters.feedparser.parse", lambda url: payload)
    entries = FeedParserClient().parse("https://example.test/feed")
    assert len(entries) == 1
    assert entries[0].title == "Te koop: House A"


def test_google_maps_client_calls_underlying_library(monkeypatch) -> None:
    class _FakeGoogleClient:
        def __init__(self, key: str):
            self.key = key

        def geocode(self, address: str):
            return [
                {
                    "formatted_address": "House A (formatted)",
                    "geometry": {"location": {"lat": 1.0, "lng": 2.0}},
                }
            ]

        def places_nearby(self, location, type, rank_by):  # noqa: A002
            return {"results": [{"name": "School", "geometry": {"location": {"lat": 1.1, "lng": 2.2}}}]}

        def distance_matrix(self, origins, mode, destinations):
            return {"rows": [{"elements": [{"distance": {"text": "1 km"}, "duration": {"text": "2 mins"}}]}]}

    monkeypatch.setattr("locus_quarter_app.adapters.googlemaps.Client", _FakeGoogleClient)
    client = GoogleMapsClient("fake-key")
    lat_lng, formatted = client.geocode("House A")
    assert formatted == "House A (formatted)"
    assert lat_lng["lat"] == 1.0
    assert client.places_nearby({"lat": 1.0, "lng": 2.0}, "school")
    assert client.distance_matrix({"lat": 1.0, "lng": 2.0}, "walking", {"lat": 1.1, "lng": 2.2})


def test_google_maps_client_geocode_raises_on_empty_result(monkeypatch) -> None:
    class _FakeGoogleClient:
        def __init__(self, key: str):  # noqa: ARG002
            pass

        @staticmethod
        def geocode(address: str):  # noqa: ARG004
            return []

        @staticmethod
        def places_nearby(location, type, rank_by):  # noqa: ARG004, A002
            return {"results": []}

        @staticmethod
        def distance_matrix(origins, mode, destinations):  # noqa: ARG004
            return {"rows": []}

    monkeypatch.setattr("locus_quarter_app.adapters.googlemaps.Client", _FakeGoogleClient)
    client = GoogleMapsClient("fake-key")
    try:
        client.geocode("Nowhere")
    except ValueError as exc:
        assert "No geocode result" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected ValueError for empty geocode result")
