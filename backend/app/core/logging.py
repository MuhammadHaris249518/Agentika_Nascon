"""Logging setup. Never log secrets or CV text."""

import logging


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )
    # Keep third-party HTTP logs quiet; request URLs can include sensitive values.
    logging.getLogger("httpx").setLevel(logging.WARNING)
