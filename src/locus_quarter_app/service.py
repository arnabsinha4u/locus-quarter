from __future__ import annotations

import re
import time
from html.parser import HTMLParser
from typing import Any, cast

from locus_quarter_app.interfaces import FeedClient, MapsClient
from locus_quarter_app.models import AppConfig, RunArtifact
from locus_quarter_app.reporting import Reporter


class _SummaryParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        if ("m2" in text or "." in text) and "k.k" not in text:
            match = re.search(r"[0-9].*", text)
            if match:
                self.lines.append(match.group(0))


class LocusQuarterService:
    DESTINATION_FILTER_PATTERN = re.compile(r"(Te koop:\s*)(.*)")

    def __init__(self, config: AppConfig, feed_client: FeedClient, maps_client: MapsClient):
        self.config = config
        self.feed_client = feed_client
        self.maps_client = maps_client

    def run(
        self, address: str | None = None, trigger: str = "manual"
    ) -> tuple[RunArtifact, Reporter]:
        mode = "address" if address else "feed"
        artifact = RunArtifact.new(mode=mode, trigger=trigger)
        reporter = Reporter()
        started = time.perf_counter()
        try:
            if address:
                self._process_address(address, "", "manual", "", artifact, reporter)
            else:
                self._run_feeds(artifact, reporter)
        finally:
            artifact.metrics.duration_seconds = round(time.perf_counter() - started, 4)
            artifact.finalize()
        return artifact, reporter

    def _run_feeds(self, artifact: RunArtifact, reporter: Reporter) -> None:
        for feed_url in self.config.query.regions_urls:
            entries = self.feed_client.parse(feed_url)
            artifact.metrics.feed_entries_seen += len(entries)
            if not entries:
                reporter.add("No houses found in RSS feed for configured criteria.")
                continue
            for entry in entries[: self.config.query.limit_houses]:
                destination = self._extract_destination(entry.title)
                if not destination:
                    artifact.metrics.warnings += 1
                    reporter.add(f"Warning: unable to parse destination from title: {entry.title}")
                    continue
                self._process_address(
                    destination,
                    entry.link,
                    entry.published,
                    entry.summary,
                    artifact,
                    reporter,
                )

    def _extract_destination(self, title: str) -> str | None:
        match = self.DESTINATION_FILTER_PATTERN.search(title)
        if not match:
            return None
        return match.group(2).strip()

    def _process_address(
        self,
        destination: str,
        source_link: str,
        published: str,
        summary: str,
        artifact: RunArtifact,
        reporter: Reporter,
    ) -> None:
        artifact.metrics.geocode_calls += 1
        src_lat_lng, src_formatted_address = self.maps_client.geocode(destination)
        artifact.metrics.houses_processed += 1

        reporter.add("+-------------------------------------------------------------+")
        if source_link:
            reporter.add(source_link)
        reporter.add(src_formatted_address)
        reporter.add(f"Date published:{published}")

        parser = _SummaryParser()
        parser.feed(summary)
        for line in parser.lines:
            reporter.add(line)

        record: dict[str, Any] = {
            "source_link": source_link,
            "address": src_formatted_address,
            "published": published,
            "summary_lines": parser.lines,
            "nearby": [],
            "office_commutes": [],
        }

        self._nearby_report(src_lat_lng, artifact, reporter, record)
        self._office_report(src_lat_lng, artifact, reporter, record)
        reporter.add("+-------------------------------------------------------------+")
        artifact.records.append(record)

    def _nearby_report(
        self,
        src_lat_lng: dict[str, float],
        artifact: RunArtifact,
        reporter: Reporter,
        record: dict[str, Any],
    ) -> None:
        for place_type in self.config.query.nearby_place_types:
            artifact.metrics.places_calls += 1
            results = self.maps_client.places_nearby(src_lat_lng, place_type)
            for place in results[: self.config.query.limit_search_places_nearby]:
                name = str(place.get("name", "unknown"))
                location = place.get("geometry", {}).get("location")
                if not location:
                    artifact.metrics.warnings += 1
                    reporter.add(f"Warning: missing location for nearby place {name}")
                    continue
                reporter.add(f"Facility Type:{place_type}")
                reporter.add(f"Facility Name:{name}")
                place_record: dict[str, Any] = {
                    "type": place_type,
                    "name": name,
                    "travel": [],
                }
                for mode in self.config.query.travel_modes:
                    artifact.metrics.distance_calls += 1
                    matrix = self.maps_client.distance_matrix(src_lat_lng, mode, location)
                    element = self._first_element(matrix)
                    if not element or "distance" not in element or "duration" not in element:
                        artifact.metrics.warnings += 1
                        reporter.add(f"Warning: distance data missing for travel mode {mode}")
                        continue
                    distance = element["distance"]["text"]
                    duration = element["duration"]["text"]
                    reporter.add(f"Travel type:{mode} Distance:{distance} Time:{duration}")
                    place_record["travel"].append(
                        {
                            "mode": mode,
                            "distance": distance,
                            "duration": duration,
                        }
                    )
                record["nearby"].append(place_record)

    def _office_report(
        self,
        src_lat_lng: dict[str, float],
        artifact: RunArtifact,
        reporter: Reporter,
        record: dict[str, Any],
    ) -> None:
        if not self.config.query.office_addresses or not self.config.query.office_travel_modes:
            return
        reporter.add("Fixed Addresses")
        for mode in self.config.query.office_travel_modes:
            artifact.metrics.distance_calls += 1
            matrix = self.maps_client.distance_matrix(
                src_lat_lng, mode, self.config.query.office_addresses
            )
            destination_addresses = matrix.get("destination_addresses", [])
            rows = matrix.get("rows", [])
            if not rows:
                artifact.metrics.warnings += 1
                reporter.add(f"Warning: office distance row data missing for travel mode {mode}")
                continue
            elements = rows[0].get("elements", [])
            for idx, destination_address in enumerate(destination_addresses):
                if idx >= len(elements):
                    artifact.metrics.warnings += 1
                    continue
                element = elements[idx]
                if "distance" not in element or "duration" not in element:
                    artifact.metrics.warnings += 1
                    reporter.add(
                        f"Warning: office distance data missing for travel mode {mode} to {destination_address}"
                    )
                    continue
                distance = element["distance"]["text"]
                duration = element["duration"]["text"]
                reporter.add(
                    f"Travel type:{mode} To:{destination_address} Distance:{distance} Time:{duration}"
                )
                record["office_commutes"].append(
                    {
                        "mode": mode,
                        "to": destination_address,
                        "distance": distance,
                        "duration": duration,
                    }
                )

    @staticmethod
    def _first_element(distance_matrix_payload: dict[str, Any]) -> dict[str, Any] | None:
        rows = distance_matrix_payload.get("rows")
        if not isinstance(rows, list) or not rows:
            return None
        first_row = rows[0]
        if not isinstance(first_row, dict):
            return None
        elements = first_row.get("elements")
        if not isinstance(elements, list) or not elements:
            return None
        first_element = elements[0]
        if not isinstance(first_element, dict):
            return None
        return cast(dict[str, Any], first_element)
