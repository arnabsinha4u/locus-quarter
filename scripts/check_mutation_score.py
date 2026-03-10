#!/usr/bin/env python3
"""Validate mutation score produced by mutmut."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def _parse_score_from_log(log_file: str) -> float:
    path = Path(log_file)
    if not path.exists():
        raise RuntimeError(f"Mutation log file not found: {log_file}")
    content = path.read_text(encoding="utf-8", errors="replace")

    killed_matches = re.findall(r"🎉\s*(\d+)", content)
    survived_matches = re.findall(r"🙁\s*(\d+)", content)
    if not killed_matches and not survived_matches:
        raise RuntimeError("Could not parse mutation counters from mutmut log output")

    killed = int(killed_matches[-1]) if killed_matches else 0
    survived = int(survived_matches[-1]) if survived_matches else 0
    total = killed + survived
    if total == 0:
        return 0.0
    return round((killed / total) * 100, 2)


def fetch_score(log_file: str) -> float:
    try:
        completed = subprocess.run(
            ["mutmut", "results", "--json"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return _parse_score_from_log(log_file)

    if completed.returncode == 0:
        try:
            payload = json.loads(completed.stdout or "{}")
        except json.JSONDecodeError:
            return _parse_score_from_log(log_file)
        killed = int(payload.get("killed_mutants", 0))
        survived = int(payload.get("survived_mutants", 0))
        total = killed + survived
        if total == 0:
            return 0.0
        return round((killed / total) * 100, 2)

    return _parse_score_from_log(log_file)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-score", type=float, default=None)
    parser.add_argument("--log-file", default="mutmut-run.log")
    args = parser.parse_args()

    score = fetch_score(args.log_file)
    print(f"Mutation score: {score}%")
    if args.min_score is not None and score < args.min_score:
        print(f"Mutation score below threshold: expected >= {args.min_score}%", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
