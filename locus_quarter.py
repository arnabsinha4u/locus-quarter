#!/usr/bin/env python3
"""Backward-compatible CLI entrypoint for Locus Quarter."""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    root = Path(__file__).resolve().parent
    src = root / "src"
    if src.exists() and str(src) not in sys.path:
        sys.path.insert(0, str(src))


def main() -> None:
    _ensure_src_on_path()
    from locus_quarter_app.cli import main as cli_main

    cli_main(standalone_mode=True)


if __name__ == "__main__":
    main()
