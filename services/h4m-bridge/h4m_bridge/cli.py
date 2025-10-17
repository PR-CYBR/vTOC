"""Command-line interface for the H4M bridge."""
from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from .bridge import BridgeImporter

LOGGER = logging.getLogger(__name__)


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="H4M bridge log importer")
    parser.add_argument(
        "--storage",
        default=os.environ.get("H4M_STORAGE", "/mnt/h4m"),
        help="Path to mounted H4M storage",
    )
    parser.add_argument(
        "--backend-url",
        default=os.environ.get("H4M_BACKEND_URL", "http://localhost:8000/api/h4m/logs"),
        help="Backend endpoint for posting log events",
    )
    parser.add_argument(
        "--dedup-state",
        default=os.environ.get("H4M_DEDUP_STATE", Path.home() / ".h4m_bridge_state.json"),
        help="Location for deduplication state",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and summarise without posting to backend",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.verbose)

    importer = BridgeImporter(
        storage_path=args.storage,
        backend_url=args.backend_url,
        dedup_path=str(args.dedup_state),
        dry_run=args.dry_run,
    )

    summary = importer.run()
    LOGGER.info("Completed import", extra=summary.as_dict())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

