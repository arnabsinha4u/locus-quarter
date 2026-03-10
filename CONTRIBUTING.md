# Contributing

## Local Setup
1. Use Python 3.11+.
2. Create virtual environment.
3. Install dev dependencies.

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

## Development Workflow
1. Create feature branch.
2. Run checks before commit.
3. Open PR with concise summary and test evidence.

```bash
ruff check .
ruff format --check .
mypy src locus_quarter.py
pytest
detect-secrets scan --baseline .secrets.baseline
pip-audit
```

## Test Matrix
1. Unit tests: config, service, helper functions.
2. Integration tests: service orchestration with mocked adapters.
3. CLI tests: `click` command behavior.
4. Contract tests: fixture payload assumptions.
5. Snapshot tests: stable text output.
6. Property tests: parser/config edge cases.
7. Mutation tests: run with `mutmut`.
8. Security tests: baseline secret and config hardening checks.

## Commit Guidance
1. Keep commits focused and phase-oriented.
2. Prefer one concern per commit (tooling, runtime, refactor, tests, docs).
3. Include migration notes when changing CLI/config behavior.
