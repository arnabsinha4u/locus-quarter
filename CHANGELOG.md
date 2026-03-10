# Changelog

## [Unreleased]

### Added
1. Typed modular architecture under `src/locus_quarter_app`.
2. Structured JSON artifacts and run metrics.
3. Cron-friendly scheduling entrypoint.
4. Full test matrix: unit, integration, CLI, contract, snapshot, property, mutation smoke, security.
5. CI workflows for lint, typing, tests, coverage gates, security checks, and mutation runs.
6. Contributor and security documentation.

### Changed
1. CLI now uses explicit `--email/--no-email`.
2. Added `--format text|json`, `--trigger`, and artifact controls.
3. Migrated config secrets to env-compatible placeholders.
4. Updated dependency stack and removed legacy/deprecated auth usage.

### Fixed
1. Sender/receiver bug in email flow.
2. Fragile RSS destination parsing and empty geocode handling.
3. Silent error swallowing in distance parsing.
4. Malformed list syntax in example config.
