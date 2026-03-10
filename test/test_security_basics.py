from __future__ import annotations

from pathlib import Path


def test_no_hardcoded_google_api_key_prefixes_in_committed_configs() -> None:
    config_files = [
        Path("config-locus-quarter.ini"),
        Path("config-mini-locus-quarter.ini"),
        Path("example-config-locus-quarter.ini"),
        Path("test/config-test-locus-quarter.ini"),
    ]
    for config_path in config_files:
        content = config_path.read_text(encoding="utf-8")
        assert "AIza" not in content


def test_feed_urls_are_https_in_default_configs() -> None:
    config_files = [
        Path("config-locus-quarter.ini"),
        Path("config-mini-locus-quarter.ini"),
        Path("example-config-locus-quarter.ini"),
    ]
    for config_path in config_files:
        content = config_path.read_text(encoding="utf-8")
        assert "http://partnerapi.funda.nl" not in content
