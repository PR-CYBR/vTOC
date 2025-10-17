"""Scan H4M storage for log files."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional

LOGGER = logging.getLogger(__name__)

SUPPORTED_FORMATS = {
    "iq": (".iq", ".cfile", ".iq.tar", ".iq.gz"),
    "decoded": (".json", ".ndjson", ".log", ".txt"),
}


@dataclass
class LogRecord:
    """Represents a log discovered on disk."""

    path: str
    log_type: str
    size: int
    modified_at: datetime
    metadata: Dict[str, object]

    @property
    def signature(self) -> str:
        return f"{self.size}:{int(self.modified_at.timestamp())}"


class LogScanner:
    """Find supported log files within a directory tree."""

    def __init__(
        self,
        base_path: Path,
        include_types: Optional[Iterable[str]] = None,
    ) -> None:
        self.base_path = Path(base_path)
        if include_types is not None:
            invalid = set(include_types) - set(SUPPORTED_FORMATS)
            if invalid:
                raise ValueError(f"Unsupported log types requested: {sorted(invalid)}")
            self._extensions = {
                ext
                for key in include_types
                for ext in SUPPORTED_FORMATS[key]
            }
        else:
            self._extensions = {ext for exts in SUPPORTED_FORMATS.values() for ext in exts}

    def scan(self) -> Iterator[LogRecord]:
        if not self.base_path.exists():
            LOGGER.warning("H4M storage path missing", extra={"base_path": str(self.base_path)})
            return iter(())
        for path in sorted(self.base_path.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in self._extensions:
                continue
            try:
                record = self._create_record(path)
            except Exception as exc:  # pragma: no cover - defensive logging
                LOGGER.exception("Failed to parse metadata", extra={"path": str(path)}, exc_info=exc)
                continue
            LOGGER.debug(
                "Discovered log file", extra={"path": record.path, "log_type": record.log_type, "size": record.size}
            )
            yield record

    def _create_record(self, path: Path) -> LogRecord:
        stat = path.stat()
        log_type = self._detect_log_type(path)
        metadata = self._extract_metadata(path, log_type)
        return LogRecord(
            path=str(path.resolve()),
            log_type=log_type,
            size=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            metadata=metadata,
        )

    def _detect_log_type(self, path: Path) -> str:
        suffix = path.suffix.lower()
        for log_type, extensions in SUPPORTED_FORMATS.items():
            if suffix in extensions:
                return log_type
        raise ValueError(f"Unsupported file extension: {suffix}")

    def _extract_metadata(self, path: Path, log_type: str) -> Dict[str, object]:
        metadata: Dict[str, object] = {
            "filename": path.name,
            "log_type": log_type,
            "size": path.stat().st_size,
            "modified_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        }
        if log_type == "decoded" and path.suffix.lower() in {".json", ".ndjson"}:
            try:
                with path.open("r", encoding="utf-8") as handle:
                    first_line = handle.readline().strip()
                    if first_line:
                        metadata.update(self._parse_json_line(first_line))
            except (OSError, json.JSONDecodeError):
                LOGGER.debug("Failed to parse JSON metadata", exc_info=True, extra={"path": str(path)})
        elif log_type == "decoded":
            with path.open("r", encoding="utf-8", errors="ignore") as handle:
                metadata["preview"] = handle.readline().strip()
        else:
            metadata["iq_summary"] = self._summarize_iq_file(path)
        return metadata

    def _parse_json_line(self, line: str) -> Dict[str, object]:
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            return {"preview": line[:200]}
        if isinstance(parsed, dict):
            return parsed
        return {"preview": line[:200]}

    def _summarize_iq_file(self, path: Path) -> Dict[str, object]:
        stat = path.stat()
        summary = {
            "size": stat.st_size,
        }
        try:
            with path.open("rb") as handle:
                header = handle.read(64)
            summary["header_preview"] = header.hex()[:64]
        except OSError:
            summary["header_preview"] = ""
        return summary

