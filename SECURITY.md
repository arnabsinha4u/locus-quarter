# Security Policy

## Reporting a Vulnerability

Please report security issues privately to the maintainers before public disclosure.
Include:
1. Affected version/commit.
2. Reproduction steps.
3. Impact assessment.
4. Suggested remediation (if available).

## Secure Configuration Defaults

1. Do not commit real API keys, OAuth client secrets, or token files.
2. Use environment variables for sensitive fields:
   - `LQ_GOOGLE_MAPS_API_KEY`
   - `LQ_GMAIL_CLIENT_SECRET_FILE`
   - `LQ_RECEIVER_MAIL_ADDRESS`
   - `LQ_SENDER_MAIL_ADDRESS`
3. Keep `.secrets.baseline` current and run `detect-secrets` in CI.

## Dependency Hygiene

1. Run `pip-audit` on every PR.
2. Keep runtime dependencies minimal and current.
3. Remove deprecated auth libraries and APIs.

## Runtime Hardening

1. Handle malformed external API payloads defensively.
2. Avoid silent exception swallowing for route/distance failures.
3. Log warnings/errors with enough context for incident triage.
