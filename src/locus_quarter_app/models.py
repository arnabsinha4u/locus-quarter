from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class QueryConfig:
    regions_urls: list[str]
    nearby_place_types: list[str]
    travel_modes: list[str]
    limit_houses: int
    limit_search_places_nearby: int
    office_addresses: list[str]
    office_travel_modes: list[str]


@dataclass(frozen=True)
class EmailConfig:
    secrets_path: str
    token_json: str
    action_scope: str
    client_secret_file: str | None
    application_name: str
    receiver_mail_address: str | None
    sender_mail_address: str | None
    email_subject: str


@dataclass(frozen=True)
class AppConfig:
    query: QueryConfig
    maps_api_key: str
    email: EmailConfig
    raw_config_path: str


@dataclass
class RunMetrics:
    feed_entries_seen: int = 0
    houses_processed: int = 0
    geocode_calls: int = 0
    places_calls: int = 0
    distance_calls: int = 0
    warnings: int = 0
    errors: int = 0
    duration_seconds: float = 0.0


@dataclass
class RunArtifact:
    run_id: str
    started_at_utc: str
    finished_at_utc: str | None = None
    mode: str = "feed"
    trigger: str = "manual"
    records: list[dict] = field(default_factory=list)
    metrics: RunMetrics = field(default_factory=RunMetrics)

    @classmethod
    def new(cls, mode: str, trigger: str = "manual") -> "RunArtifact":
        started_at = datetime.now(tz=timezone.utc).isoformat()
        return cls(
            run_id=started_at.replace(":", "-"),
            started_at_utc=started_at,
            mode=mode,
            trigger=trigger,
        )

    def finalize(self) -> None:
        self.finished_at_utc = datetime.now(tz=timezone.utc).isoformat()

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["metrics"] = asdict(self.metrics)
        return payload
