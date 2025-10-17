"""Entrypoint for running the GPS ingestion service."""

from __future__ import annotations

import logging

from .config import load_config
from .service import GPSIngestService


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config = load_config()
    service = GPSIngestService(config)
    service.run()


if __name__ == "__main__":
    main()
