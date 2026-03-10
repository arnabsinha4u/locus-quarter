from __future__ import annotations

from click.testing import CliRunner

from locus_quarter_app.cli import main
from locus_quarter_app.config import ConfigError


def test_cli_returns_2_for_config_error(monkeypatch) -> None:
    def _raise_config_error(self):
        raise ConfigError("bad config")

    monkeypatch.setattr("locus_quarter_app.cli.ConfigLoader.load", _raise_config_error)
    result = CliRunner().invoke(main, [])
    assert result.exit_code == 2


def test_cli_returns_1_and_json_error_for_unhandled_exception(monkeypatch) -> None:
    class _FakeLoader:
        def __init__(self, path: str):  # noqa: ARG002
            pass

        def load(self):
            raise RuntimeError("boom")

    monkeypatch.setattr("locus_quarter_app.cli.ConfigLoader", _FakeLoader)
    result = CliRunner().invoke(main, ["--format", "json"])
    assert result.exit_code == 1
    assert '"error": "boom"' in result.output
