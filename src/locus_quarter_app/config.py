from __future__ import annotations

import ast
import configparser
import os
from dataclasses import dataclass

from locus_quarter_app.models import AppConfig, EmailConfig, QueryConfig


class ConfigError(ValueError):
    """Raised when config values are invalid."""


def _parse_list(value: str, option: str) -> list[str]:
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError) as exc:
        raise ConfigError(f"Invalid list literal for {option}: {value}") from exc
    if not isinstance(parsed, list):
        raise ConfigError(f"Expected list for {option}, got {type(parsed).__name__}")
    normalized: list[str] = []
    for item in parsed:
        if not isinstance(item, str):
            raise ConfigError(f"Expected string items for {option}, got {type(item).__name__}")
        normalized.append(item.strip())
    return normalized


def resolve_env_value(raw_value: str | None, default_env_var: str | None = None) -> str | None:
    if raw_value is None:
        return os.getenv(default_env_var) if default_env_var else None
    value = str(raw_value).strip()
    if value.startswith("env:"):
        env_name = value.split("env:", 1)[1].strip()
        return os.getenv(env_name)
    if value in ("", "CHANGE_ME", "REPLACE_ME"):
        return os.getenv(default_env_var) if default_env_var else None
    return value


def _required(value: str | None, description: str) -> str:
    if not value:
        raise ConfigError(f"Missing required configuration: {description}")
    return value


@dataclass(frozen=True)
class ConfigLoader:
    path: str

    def load(self) -> AppConfig:
        parser = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        found = parser.read(self.path)
        if not found:
            raise ConfigError(f"Configuration file not found: {self.path}")

        query = QueryConfig(
            regions_urls=_parse_list(
                parser.get("LOCUS-QUARTER", "g_list_of_regions_urls"), "g_list_of_regions_urls"
            ),
            nearby_place_types=_parse_list(
                parser.get("LOCUS-QUARTER", "g_list_nearby_types_of_places"),
                "g_list_nearby_types_of_places",
            ),
            travel_modes=_parse_list(parser.get("LOCUS-QUARTER", "g_travel_mode"), "g_travel_mode"),
            limit_houses=parser.getint("LOCUS-QUARTER", "g_limit_houses"),
            limit_search_places_nearby=parser.getint(
                "LOCUS-QUARTER", "g_limit_search_places_nearby"
            ),
            office_addresses=_parse_list(
                parser.get("LOCUS-QUARTER", "g_office_addresses"),
                "g_office_addresses",
            ),
            office_travel_modes=_parse_list(
                parser.get("LOCUS-QUARTER", "g_office_travel_mode"),
                "g_office_travel_mode",
            ),
        )

        maps_api_key = _required(
            resolve_env_value(
                parser.get("GOOGLE-API", "g_google_maps_client_api_key"),
                "LQ_GOOGLE_MAPS_API_KEY",
            ),
            "Google Maps API key (g_google_maps_client_api_key or LQ_GOOGLE_MAPS_API_KEY)",
        )

        email = EmailConfig(
            secrets_path=parser.get("EMAIL", "g_gmail_secrets_path", fallback="."),
            token_json=parser.get("EMAIL", "g_gmail_secret_json", fallback="gmail-token.json"),
            action_scope=parser.get(
                "EMAIL",
                "g_gmail_action_scope",
                fallback="https://www.googleapis.com/auth/gmail.send",
            ),
            client_secret_file=resolve_env_value(
                parser.get("EMAIL", "g_gmail_client_secret_file", fallback=""),
                "LQ_GMAIL_CLIENT_SECRET_FILE",
            ),
            application_name=parser.get(
                "EMAIL", "g_gmail_google_developer_application_name", fallback="locus-quarter"
            ),
            receiver_mail_address=resolve_env_value(
                parser.get("EMAIL", "g_receiver_mail_address", fallback=""),
                "LQ_RECEIVER_MAIL_ADDRESS",
            ),
            sender_mail_address=resolve_env_value(
                parser.get("EMAIL", "g_sender_mail_address", fallback=""),
                "LQ_SENDER_MAIL_ADDRESS",
            ),
            email_subject=parser.get("EMAIL", "g_email_subject", fallback="Locus Quarter"),
        )

        return AppConfig(
            query=query, maps_api_key=maps_api_key, email=email, raw_config_path=self.path
        )
