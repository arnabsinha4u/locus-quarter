from __future__ import annotations

from typing import Any

import feedparser
import googlemaps

from locus_quarter_app.interfaces import FeedClient, FeedEntry, MapsClient


class FeedParserClient(FeedClient):
    def parse(self, url: str) -> list[FeedEntry]:
        parsed = feedparser.parse(url.strip())
        entries: list[FeedEntry] = []
        for entry in parsed.entries:
            entries.append(
                FeedEntry(
                    title=getattr(entry, "title", ""),
                    link=getattr(entry, "link", ""),
                    summary=getattr(entry, "summary", ""),
                    published=getattr(entry, "published", "unknown"),
                )
            )
        return entries


class GoogleMapsClient(MapsClient):
    def __init__(self, api_key: str):
        self._client = googlemaps.Client(key=api_key)

    def geocode(self, address: str) -> tuple[dict[str, float], str]:
        result = self._client.geocode(address)
        if not result:
            raise ValueError(f"No geocode result for address: {address}")
        formatted_address = result[0]["formatted_address"]
        location = result[0]["geometry"]["location"]
        return location, formatted_address

    def places_nearby(self, location: dict[str, float], place_type: str) -> list[dict[str, Any]]:
        result = self._client.places_nearby(location=location, type=place_type, rank_by="distance")
        return result.get("results", [])

    def distance_matrix(
        self,
        origins: dict[str, float],
        mode: str,
        destinations: list[dict[str, float]] | list[str] | dict[str, float],
    ) -> dict[str, Any]:
        return self._client.distance_matrix(origins=origins, mode=mode, destinations=destinations)
