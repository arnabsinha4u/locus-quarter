from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from locus_quarter_app.interfaces import FeedEntry


class FakeFeedClient:
    def __init__(self, entries: list[FeedEntry]):
        self.entries = entries

    def parse(self, url: str) -> list[FeedEntry]:
        return self.entries


class FakeMapsClient:
    def geocode(self, address: str) -> tuple[dict[str, float], str]:
        return {"lat": 52.1, "lng": 4.3}, f"{address} (formatted)"

    def places_nearby(self, location: dict[str, float], place_type: str) -> list[dict[str, Any]]:
        return [
            {
                "name": f"{place_type} one",
                "geometry": {"location": {"lat": 52.11, "lng": 4.31}},
            },
            {
                "name": f"{place_type} two",
                "geometry": {"location": {"lat": 52.12, "lng": 4.32}},
            },
        ]

    def distance_matrix(
        self,
        origins: dict[str, float],
        mode: str,
        destinations: list[dict[str, float]] | list[str] | dict[str, float],
    ) -> dict[str, Any]:
        if isinstance(destinations, list) and destinations and isinstance(destinations[0], str):
            destination_addresses = destinations
            elements = [
                {"distance": {"text": "8.1 km"}, "duration": {"text": "15 mins"}}
                for _ in destination_addresses
            ]
            return {
                "destination_addresses": destination_addresses,
                "rows": [{"elements": elements}],
            }
        return {
            "rows": [{"elements": [{"distance": {"text": "0.8 km"}, "duration": {"text": "10 mins"}}]}]
        }


@dataclass
class FakeMailClient:
    sent: bool = False

    def send(self, sender: str, to: str, subject: str, body_text: str) -> None:
        self.sent = True
