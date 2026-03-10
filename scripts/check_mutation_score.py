#!/usr/bin/env python3
"""Validate mutation score produced by mutmut."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys


def fetch_score() -> float:
    completed = subprocess.run(
        ["mutmut", "results", "--json"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "Unable to fetch mutation results")

    payload = json.loads(completed.stdout or "{}")
    killed = int(payload.get("killed_mutants", 0))
    survived = int(payload.get("survived_mutants", 0))
    total = killed + survived
    if total == 0:
        return 0.0
    return round((killed / total) * 100, 2)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-score", type=float, required=True)
    args = parser.parse_args()

    score = fetch_score()
    print(f"Mutation score: {score}%")
    if score < args.min_score:
        print(f"Mutation score below threshold: expected >= {args.min_score}%", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
