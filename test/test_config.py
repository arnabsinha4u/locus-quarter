from __future__ import annotations

from pathlib import Path

import pytest

from locus_quarter_app.config import (
    ConfigError,
    ConfigLoader,
    _parse_list,
    _required,
    resolve_env_value,
)


def test_config_loader_resolves_env_map_key(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("LQ_GOOGLE_MAPS_API_KEY", "test-google-maps-key")
    config_path = tmp_path / "config.ini"
    config_path.write_text(
        """[LOCUS-QUARTER]
g_list_of_regions_urls = ["https://example.test/feed"]
g_list_nearby_types_of_places = ["school"]
g_travel_mode = ["walking"]
g_limit_houses = 1
g_limit_search_places_nearby = 1
g_office_addresses = []
g_office_travel_mode = []
[GOOGLE-API]
g_google_maps_client_api_key = env:LQ_GOOGLE_MAPS_API_KEY
""",
        encoding="utf-8",
    )
    config = ConfigLoader(str(config_path)).load()
    assert config.maps_api_key == "test-google-maps-key"


def test_config_loader_raises_for_bad_list(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LQ_GOOGLE_MAPS_API_KEY", "test-google-maps-key")
    bad = tmp_path / "bad.ini"
    bad.write_text(
        """[LOCUS-QUARTER]
g_list_of_regions_urls = not-a-list
g_list_nearby_types_of_places = ["school"]
g_travel_mode = ["walking"]
g_limit_houses = 1
g_limit_search_places_nearby = 1
g_office_addresses = []
g_office_travel_mode = []
[GOOGLE-API]
g_google_maps_client_api_key = env:LQ_GOOGLE_MAPS_API_KEY
""",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        ConfigLoader(str(bad)).load()


def test_config_loader_raises_for_missing_file() -> None:
    with pytest.raises(ConfigError):
        ConfigLoader("does-not-exist.ini").load()


def test_parse_list_rejects_non_list() -> None:
    with pytest.raises(ConfigError):
        _parse_list("{'a': 1}", "bad_option")


def test_parse_list_rejects_non_string_items() -> None:
    with pytest.raises(ConfigError):
        _parse_list("[1, 2, 3]", "bad_option")


def test_required_raises_when_empty() -> None:
    with pytest.raises(ConfigError):
        _required(None, "maps_api_key")


@pytest.mark.parametrize(
    ("raw_value", "env_value", "expected"),
    [
        ("env:MY_VAR", "value1", "value1"),
        ("CHANGE_ME", "value2", "value2"),
        ("direct", "ignored", "direct"),
    ],
)
def test_resolve_env_value(
    raw_value: str,
    env_value: str,
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MY_VAR", env_value)
    assert resolve_env_value(raw_value, "MY_VAR") == expected


def test_resolve_env_value_with_none_and_no_default() -> None:
    assert resolve_env_value(None, None) is None
