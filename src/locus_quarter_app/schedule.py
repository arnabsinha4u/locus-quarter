from __future__ import annotations

import os
import subprocess


def main() -> None:
    """Cron-friendly wrapper around the CLI."""
    config_path = os.getenv("LQ_CONFIG_PATH", "config-locus-quarter.ini")
    output_dir = os.getenv("LQ_OUTPUT_DIR", "reports")
    command = [
        "python",
        "locus_quarter.py",
        "--config",
        config_path,
        "--trigger",
        "cron",
        "--output-dir",
        output_dir,
    ]
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
