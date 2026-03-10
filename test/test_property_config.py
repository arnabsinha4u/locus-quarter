from __future__ import annotations

from hypothesis import given, strategies as st

from locus_quarter_app.config import _parse_list


@given(st.lists(st.text(min_size=0, max_size=20), max_size=8))
def test_parse_list_roundtrip(values: list[str]) -> None:
    literal = repr(values)
    assert _parse_list(literal, "x") == [item.strip() for item in values]
