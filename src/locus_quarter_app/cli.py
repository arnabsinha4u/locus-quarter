from __future__ import annotations

import json
import logging
import sys

import click
from locus_quarter_app.adapters import FeedParserClient, GoogleMapsClient
from locus_quarter_app.config import ConfigError, ConfigLoader
from locus_quarter_app.emailer import GmailClient
from locus_quarter_app.reporting import Reporter
from locus_quarter_app.service import LocusQuarterService


logger = logging.getLogger("locus-quarter")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@click.command()
@click.option("--address", default=None, help="Process a single address instead of RSS feeds.")
@click.option("--config", "config_path", default="config-locus-quarter.ini", show_default=True)
@click.option("--email/--no-email", default=False, show_default=True)
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
@click.option("--output-dir", default="reports", show_default=True, help="Directory for timestamped artifacts.")
@click.option("--save-artifacts/--no-save-artifacts", default=True, show_default=True)
@click.option("--trigger", default="manual", show_default=True, help="Run trigger label, e.g. cron/nightly/manual.")
@click.option("--print-metrics/--no-print-metrics", default=True, show_default=True)
def main(
    address: str | None,
    config_path: str,
    email: bool,
    output_format: str,
    output_dir: str,
    save_artifacts: bool,
    trigger: str,
    print_metrics: bool,
) -> None:
    """Run Locus Quarter analysis."""
    try:
        config = ConfigLoader(config_path).load()
        service = LocusQuarterService(
            config=config,
            feed_client=FeedParserClient(),
            maps_client=GoogleMapsClient(config.maps_api_key),
        )
        artifact, reporter = service.run(address=address, trigger=trigger)
        text_output = reporter.render_text()

        if output_format == "json":
            click.echo(Reporter.render_json(artifact))
        else:
            click.echo(text_output)

        if save_artifacts:
            json_path, text_path = Reporter.write_artifacts(output_dir, artifact, text_output)
            logger.info("Artifacts written: json=%s text=%s", json_path, text_path)
        if print_metrics:
            logger.info(
                "Run metrics: trigger=%s houses=%s feeds=%s geocode=%s places=%s distance=%s warnings=%s errors=%s duration_s=%.3f",
                artifact.trigger,
                artifact.metrics.houses_processed,
                artifact.metrics.feed_entries_seen,
                artifact.metrics.geocode_calls,
                artifact.metrics.places_calls,
                artifact.metrics.distance_calls,
                artifact.metrics.warnings,
                artifact.metrics.errors,
                artifact.metrics.duration_seconds,
            )

        if email:
            if not config.email.receiver_mail_address or not config.email.sender_mail_address:
                raise ConfigError(
                    "Email sending requested, but sender/receiver addresses are not configured."
                )
            GmailClient(config.email).send(
                sender=config.email.sender_mail_address,
                to=config.email.receiver_mail_address,
                subject=config.email.email_subject,
                body_text=text_output,
            )
            logger.info("Email sent to %s", config.email.receiver_mail_address)

        if artifact.metrics.errors > 0:
            raise SystemExit(1)
    except ConfigError as exc:
        logger.error("Configuration error: %s", exc)
        raise SystemExit(2) from exc
    except Exception as exc:  # pragma: no cover - defensive wrapper
        logger.error("Unhandled execution error: %s", exc)
        if "--format" in sys.argv and "json" in sys.argv:
            click.echo(json.dumps({"error": str(exc)}))
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
