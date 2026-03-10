from __future__ import annotations

from pathlib import Path

from locus_quarter_app.models import RunArtifact
from locus_quarter_app.reporting import Reporter


def test_reporter_writes_artifacts(tmp_path: Path) -> None:
    artifact = RunArtifact.new(mode="feed", trigger="unit-test")
    artifact.records.append({"x": 1})
    artifact.finalize()
    text_output = "hello\n"
    json_path, text_path = Reporter.write_artifacts(str(tmp_path), artifact, text_output)
    assert json_path.exists()
    assert text_path.exists()
    assert '"trigger": "unit-test"' in json_path.read_text(encoding="utf-8")
    assert text_path.read_text(encoding="utf-8") == "hello\n"


def test_run_artifact_to_dict_contains_metrics() -> None:
    artifact = RunArtifact.new(mode="address")
    payload = artifact.to_dict()
    assert "metrics" in payload
    assert payload["metrics"]["houses_processed"] == 0
