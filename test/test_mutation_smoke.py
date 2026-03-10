from __future__ import annotations

from locus_quarter_app.config import resolve_env_value
from locus_quarter_app.service import LocusQuarterService


def test_mutation_smoke_resolve_env_value_passthrough() -> None:
    assert resolve_env_value("direct", "ANY") == "direct"


def test_mutation_smoke_first_element_none_for_empty_rows() -> None:
    assert LocusQuarterService._first_element({"rows": []}) is None
