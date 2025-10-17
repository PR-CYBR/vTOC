"""Tests for the storage scanner."""
from __future__ import annotations

from h4m_bridge.scanner import LogScanner


def test_scanner_discovers_supported_logs(sample_logs, storage_dir):
    scanner = LogScanner(storage_dir)
    records = list(scanner.scan())
    paths = {record.path for record in records}

    for expected in sample_logs.values():
        assert str(expected.resolve()) in paths

    decoded = [r for r in records if r.log_type == "decoded"]
    assert any(r.metadata.get("channel") == "alpha" for r in decoded)
    assert any("timestamp=1" in r.metadata.get("preview", "") for r in decoded)

    iq_records = [r for r in records if r.log_type == "iq"]
    assert iq_records
    assert all("iq_summary" in r.metadata for r in iq_records)


def test_scanner_handles_missing_storage(tmp_path):
    scanner = LogScanner(tmp_path / "missing")
    assert list(scanner.scan()) == []

