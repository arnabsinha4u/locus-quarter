from __future__ import annotations

import json
from pathlib import Path

from locus_quarter_app.models import RunArtifact


class Reporter:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def add(self, line: str = "") -> None:
        self.lines.append(line)

    def render_text(self) -> str:
        return "\n".join(self.lines).strip() + "\n"

    @staticmethod
    def render_json(artifact: RunArtifact) -> str:
        return json.dumps(artifact.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)

    @staticmethod
    def write_artifacts(output_dir: str, artifact: RunArtifact, text_output: str) -> tuple[Path, Path]:
        directory = Path(output_dir)
        directory.mkdir(parents=True, exist_ok=True)
        json_path = directory / f"{artifact.run_id}.json"
        text_path = directory / f"{artifact.run_id}.txt"
        json_path.write_text(Reporter.render_json(artifact), encoding="utf-8")
        text_path.write_text(text_output, encoding="utf-8")
        return json_path, text_path
