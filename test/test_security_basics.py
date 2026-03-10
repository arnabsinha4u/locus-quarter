from __future__ import annotations

from pathlib import Path


def _resolve_repo_file(relative_path: str) -> Path:
    candidates = [
        Path(relative_path),
        Path(__file__).resolve().parents[1] / relative_path,
        Path(__file__).resolve().parents[2] / relative_path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not resolve repository file: {relative_path}")


def test_no_hardcoded_google_api_key_prefixes_in_committed_configs() -> None:
    config_files = [
        "config-locus-quarter.ini",
        "config-mini-locus-quarter.ini",
        "example-config-locus-quarter.ini",
        "test/config-test-locus-quarter.ini",
    ]
    for config_file in config_files:
        config_path = _resolve_repo_file(config_file)
        content = config_path.read_text(encoding="utf-8")
        assert "AIza" not in content


def test_feed_urls_are_https_in_default_configs() -> None:
    config_files = [
        "config-locus-quarter.ini",
        "config-mini-locus-quarter.ini",
        "example-config-locus-quarter.ini",
    ]
    for config_file in config_files:
        config_path = _resolve_repo_file(config_file)
        content = config_path.read_text(encoding="utf-8")
        assert "http://partnerapi.funda.nl" not in content
