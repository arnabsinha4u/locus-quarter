# Locus Quarter

Locus Quarter automates property-feed analysis by combining:
1. RSS listing intake.
2. Nearby place discovery (Google Places).
3. Commute-time scoring (Google Distance Matrix).
4. Optional Gmail report delivery.

The project is now modernized for Python 3.11+, typed modular code, CI quality gates, and deterministic tests.

## Quick Start

### Requirements
1. Python 3.11 or newer.
2. A Google Maps API key.
3. Optional: Gmail API credentials for email delivery.

### Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

### Configure Secrets (recommended via env vars)
```bash
export LQ_GOOGLE_MAPS_API_KEY="..."
export LQ_GMAIL_CLIENT_SECRET_FILE="/absolute/path/client_secret.json"   # optional
export LQ_RECEIVER_MAIL_ADDRESS="to@example.com"                         # optional
export LQ_SENDER_MAIL_ADDRESS="from@example.com"                         # optional
```

### Run
```bash
python locus_quarter.py
```

Single address mode:
```bash
python locus_quarter.py --address "Henriette Bosmanslaan 2, 1187 HH Amstelveen, Netherlands"
```

JSON output:
```bash
python locus_quarter.py --format json
```

No artifact files:
```bash
python locus_quarter.py --no-save-artifacts
```

Email on:
```bash
python locus_quarter.py --email
```

## CLI Reference

| Option | Description | Default |
|---|---|---|
| `--address` | Analyze one address instead of RSS feeds | `None` |
| `--config` | Config INI path | `config-locus-quarter.ini` |
| `--email/--no-email` | Send report via Gmail | `--no-email` |
| `--format text\|json` | Console output format | `text` |
| `--output-dir` | Directory for run artifacts (`.json` + `.txt`) | `reports` |
| `--save-artifacts/--no-save-artifacts` | Toggle artifact persistence | `--save-artifacts` |
| `--trigger` | Trigger label for run metadata (`manual`, `cron`, etc.) | `manual` |
| `--print-metrics/--no-print-metrics` | Log run counters and duration | `--print-metrics` |

## Configuration Reference

All list fields use Python list literal syntax in INI files.

### `[LOCUS-QUARTER]`
| Key | Type | Required | Notes |
|---|---|---|---|
| `g_list_of_regions_urls` | `list[str]` | yes | RSS feed URLs (HTTPS recommended) |
| `g_list_nearby_types_of_places` | `list[str]` | yes | Google supported place types |
| `g_travel_mode` | `list[str]` | yes | e.g. `walking`, `bicycling`, `driving`, `transit` |
| `g_limit_houses` | `int` | yes | Max houses per feed |
| `g_limit_search_places_nearby` | `int` | yes | Max places per type |
| `g_office_addresses` | `list[str]` | no | Destination addresses for commute scoring |
| `g_office_travel_mode` | `list[str]` | no | Travel modes for office commute |

### `[GOOGLE-API]`
| Key | Type | Required | Notes |
|---|---|---|---|
| `g_google_maps_client_api_key` | `str` | yes | Use `env:LQ_GOOGLE_MAPS_API_KEY` |

### `[EMAIL]`
| Key | Type | Required | Notes |
|---|---|---|---|
| `g_gmail_secrets_path` | `str` | no | Token storage dir |
| `g_gmail_secret_json` | `str` | no | Token filename |
| `g_gmail_action_scope` | `str` | no | Comma-separated scopes |
| `g_gmail_client_secret_file` | `str` | optional | Use `env:LQ_GMAIL_CLIENT_SECRET_FILE` |
| `g_gmail_google_developer_application_name` | `str` | no | App display name |
| `g_receiver_mail_address` | `str` | optional | Use `env:LQ_RECEIVER_MAIL_ADDRESS` |
| `g_sender_mail_address` | `str` | optional | Use `env:LQ_SENDER_MAIL_ADDRESS` |
| `g_email_subject` | `str` | no | Subject line |

## Artifacts and Metrics

Each run can emit:
1. `reports/<run_id>.txt` text report.
2. `reports/<run_id>.json` structured payload.

JSON includes:
1. `mode` (`feed` or `address`)
2. `trigger` (`manual`, `cron`, etc.)
3. `records` (per-house details)
4. `metrics` (feed/geocode/places/distance calls, warnings/errors, duration)

## Testing and Quality Gates

Run all tests:
```bash
pytest
```

Run lint/type checks:
```bash
ruff check .
ruff format --check .
mypy src locus_quarter.py
```

Security and dependency checks:
```bash
detect-secrets scan --baseline .secrets.baseline
pip-audit
```

Mutation checks:
```bash
mutmut run | tee mutmut-run.log
python scripts/check_mutation_score.py --log-file mutmut-run.log
```

Coverage gates:
```bash
pytest -q --cov=src/locus_quarter_app --cov-branch --cov-report=xml
python scripts/check_coverage_gates.py --min-statement 90 --min-branch 80
```

## Scheduling

Cron-friendly wrapper:
```bash
locus-quarter-scheduled
```

Environment knobs:
1. `LQ_CONFIG_PATH` (default `config-locus-quarter.ini`)
2. `LQ_OUTPUT_DIR` (default `reports`)

## Migration Guide (Legacy -> Modern)

1. `--email=true` is replaced by `--email` (and disable via `--no-email`).
2. Prefer `--format json` instead of parsing free-form text.
3. API keys/emails should come from env vars, not committed secrets.
4. Legacy one-file implementation is replaced by `src/locus_quarter_app/*`; `locus_quarter.py` is now a compatibility wrapper.

## Troubleshooting

1. `Configuration error: Missing required configuration`
Set `LQ_GOOGLE_MAPS_API_KEY` or configure `g_google_maps_client_api_key`.

2. Gmail auth prompt keeps appearing
Confirm token file path (`g_gmail_secrets_path` + `g_gmail_secret_json`) and client secret path.

3. Empty or missing distance fields
This can happen for unsupported route/mode combinations from Google API.

4. RSS yields no houses
Verify feed URLs and configured locality/price filters.

## License

MIT (see `LICENSE`).
