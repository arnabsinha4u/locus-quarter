from __future__ import annotations

import json
from pathlib import Path

from locus_quarter_app.service import LocusQuarterService


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


def _load_fixture(name: str) -> dict:
    path = _resolve_repo_file(f"test/fixtures/{name}")
    return json.loads(path.read_text(encoding="utf-8"))


def test_distance_matrix_contract_valid_fixture() -> None:
    payload = _load_fixture("distance_matrix_valid.json")
    element = LocusQuarterService._first_element(payload)
    assert element is not None
    assert element["distance"]["text"] == "8.1 km"
    assert element["duration"]["text"] == "15 mins"


def test_distance_matrix_contract_missing_fields_fixture() -> None:
    payload = _load_fixture("distance_matrix_missing_fields.json")
    element = LocusQuarterService._first_element(payload)
    assert element is not None
    assert "distance" not in element
