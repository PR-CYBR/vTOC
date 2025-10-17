"""Deduplication helpers for the H4M bridge."""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
from typing import Dict, Iterable

from .scanner import LogRecord

LOGGER = logging.getLogger(__name__)


@dataclass
class FileDeduplicator:
    """Track which log files have already been imported.

    The deduplicator stores metadata on disk so subsequent runs do not
    reprocess the same files. Each record is stored by the file's absolute
    path with a signature comprised of the file size and last modification
    timestamp. This provides a good balance between accuracy and performance
    without requiring checksums for large IQ capture files.
    """

    state_path: Path
    _state: Dict[str, str] = field(default_factory=dict, init=False)
    _dirty: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.state_path = Path(self.state_path)
        if self.state_path.exists():
            try:
                self._state = json.loads(self.state_path.read_text())
            except json.JSONDecodeError:
                LOGGER.warning("Deduplicator state file is corrupt; starting fresh", extra={"state_path": str(self.state_path)})
                self._state = {}
        else:
            if not self.state_path.parent.exists():
                self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self._state = {}

    def __enter__(self) -> "FileDeduplicator":
        return self

    def __exit__(self, *exc_info) -> None:
        self.flush()

    def flush(self) -> None:
        if self._dirty:
            self.state_path.write_text(json.dumps(self._state, indent=2, sort_keys=True))
            self._dirty = False

    def is_duplicate(self, record: LogRecord) -> bool:
        signature = record.signature
        stored = self._state.get(record.path)
        is_dup = stored == signature
        LOGGER.debug(
            "Checked deduplication", extra={"path": record.path, "signature": signature, "is_duplicate": is_dup}
        )
        return is_dup

    def mark_imported(self, record: LogRecord) -> None:
        signature = record.signature
        self._state[record.path] = signature
        self._dirty = True
        LOGGER.debug(
            "Marked file as imported", extra={"path": record.path, "signature": signature}
        )

    def mark_many(self, records: Iterable[LogRecord]) -> None:
        for record in records:
            self.mark_imported(record)

