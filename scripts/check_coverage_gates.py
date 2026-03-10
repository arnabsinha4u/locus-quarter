#!/usr/bin/env python3
"""Validate statement and branch coverage thresholds."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys


def read_totals() -> dict:
    subprocess.run(
        ["python", "-m", "coverage", "json", "-o", "coverage.json"],
        check=True,
        capture_output=True,
        text=True,
    )
    with open("coverage.json", "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return payload.get("totals", {})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-statement", type=float, required=True)
    parser.add_argument("--min-branch", type=float, required=True)
    args = parser.parse_args()

    totals = read_totals()
    statement = float(totals.get("percent_covered", 0.0))
    covered_branches = int(totals.get("covered_branches", 0))
    num_branches = int(totals.get("num_branches", 0))
    branch = 100.0 if num_branches == 0 else (covered_branches / num_branches) * 100

    print(f"Statement coverage: {statement:.2f}%")
    print(f"Branch coverage: {branch:.2f}%")

    if statement < args.min_statement:
        print(
            f"Statement coverage below threshold: expected >= {args.min_statement}%",
            file=sys.stderr,
        )
        return 1
    if branch < args.min_branch:
        print(
            f"Branch coverage below threshold: expected >= {args.min_branch}%",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
