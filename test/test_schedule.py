from __future__ import annotations

from locus_quarter_app import schedule


def test_schedule_entrypoint_invokes_cli(monkeypatch) -> None:
    calls: list[list[str]] = []

    def _fake_run(command, check):  # noqa: FBT002
        assert check is True
        calls.append(command)
        return None

    monkeypatch.setenv("LQ_CONFIG_PATH", "config-mini-locus-quarter.ini")
    monkeypatch.setenv("LQ_OUTPUT_DIR", "reports")
    monkeypatch.setattr("locus_quarter_app.schedule.subprocess.run", _fake_run)
    schedule.main()

    assert calls
    assert calls[0][0] == "python"
    assert "--trigger" in calls[0]
