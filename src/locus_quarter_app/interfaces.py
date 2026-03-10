from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class FeedEntry:
    title: str
    link: str
    summary: str
    published: str


class FeedClient(Protocol):
    def parse(self, url: str) -> list[FeedEntry]:
        """Return parsed entries for a feed URL."""


class MapsClient(Protocol):
    def geocode(self, address: str) -> tuple[dict[str, float], str]:
        """Resolve address into (location, formatted_address)."""

    def places_nearby(self, location: dict[str, float], place_type: str) -> list[dict[str, Any]]:
        """Return nearby places sorted by distance."""

    def distance_matrix(
        self,
        origins: dict[str, float],
        mode: str,
        destinations: list[dict[str, float]] | list[str] | dict[str, float],
    ) -> dict[str, Any]:
        """Return distance matrix payload."""


class MailClient(Protocol):
    def send(self, sender: str, to: str, subject: str, body_text: str) -> None:
        """Send report by email."""
