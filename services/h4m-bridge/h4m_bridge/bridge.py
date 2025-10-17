"""Bridge orchestration for importing logs."""
from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict

from .client import BridgeClient
from .dedup import FileDeduplicator
from .scanner import LogScanner

LOGGER = logging.getLogger(__name__)


@dataclass
class ImportSummary:
    processed: int = 0
    imported: int = 0
    duplicates: int = 0
    failed: int = 0
    by_type: Counter = field(default_factory=Counter)

    def as_dict(self) -> Dict[str, object]:
        return {
            "processed": self.processed,
            "imported": self.imported,
            "duplicates": self.duplicates,
            "failed": self.failed,
            "by_type": dict(self.by_type),
        }


@dataclass
class BridgeImporter:
    storage_path: str
    backend_url: str
    dedup_path: str
    dry_run: bool = False

    def run(self) -> ImportSummary:
        scanner = LogScanner(self.storage_path)
        deduplicator = FileDeduplicator(self.dedup_path)
        client = BridgeClient(self.backend_url)
        summary = ImportSummary()
        pending_records = []

        for record in scanner.scan():
            summary.processed += 1
            if deduplicator.is_duplicate(record):
                summary.duplicates += 1
                continue

            payload = {
                "path": record.path,
                "log_type": record.log_type,
                "size": record.size,
                "modified_at": record.modified_at.isoformat(),
                "metadata": record.metadata,
            }

            try:
                if not self.dry_run:
                    client.post_event(payload)
                else:
                    LOGGER.info("Dry run: skipping backend post", extra={"path": record.path})
                summary.imported += 1
                summary.by_type[record.log_type] += 1
                pending_records.append(record)
            except Exception:
                summary.failed += 1
                LOGGER.exception("Failed to import log", extra={"path": record.path})

        if not self.dry_run:
            deduplicator.mark_many(pending_records)
            deduplicator.flush()
        else:
            LOGGER.info("Dry run complete; no files marked as imported")

        LOGGER.info("Import summary", extra=summary.as_dict())
        return summary

