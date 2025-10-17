"""Tests for the bridge importer."""
from __future__ import annotations

import datetime
import logging
from typing import List
from unittest import mock

import pytest

from h4m_bridge.bridge import BridgeImporter
from h4m_bridge.scanner import LogRecord, LogScanner


class DummyScanner(LogScanner):
    def __init__(self, records):
        self._records = records

    def scan(self):
        for record in self._records:
            yield record


@pytest.fixture()
def patched_scanner(monkeypatch):
    records: List = []

    def factory(*args, **kwargs):
        return DummyScanner(records)

    monkeypatch.setattr("h4m_bridge.bridge.LogScanner", factory)
    return records


@pytest.fixture()
def fake_record(sample_logs):
    path = sample_logs["decoded_json"].resolve()
    stat = path.stat()
    return LogRecord(
        path=str(path),
        log_type="decoded",
        size=stat.st_size,
        modified_at=datetime.datetime.fromtimestamp(stat.st_mtime),
        metadata={"channel": "alpha"},
    )


def test_importer_dry_run_skips_marking(sample_logs, storage_dir, dedup_state_path, fake_record, patched_scanner, caplog):
    caplog.set_level(logging.INFO)
    patched_scanner.append(fake_record)
    with mock.patch("h4m_bridge.bridge.BridgeClient.post_event") as mocked_post:
        importer = BridgeImporter(
            storage_path=storage_dir,
            backend_url="http://example",  # unused because patched
            dedup_path=str(dedup_state_path),
            dry_run=True,
        )
        summary = importer.run()

    assert summary.imported == 1
    assert mocked_post.call_count == 0
    assert not dedup_state_path.exists()
    assert any("Dry run" in rec.message for rec in caplog.records)


def test_importer_marks_deduplicator(storage_dir, dedup_state_path, fake_record, patched_scanner):
    patched_scanner.append(fake_record)
    with mock.patch("h4m_bridge.bridge.BridgeClient.post_event") as mocked_post:
        importer = BridgeImporter(
            storage_path=storage_dir,
            backend_url="http://example",
            dedup_path=str(dedup_state_path),
            dry_run=False,
        )
        summary = importer.run()

    mocked_post.assert_called_once()
    assert summary.imported == 1
    assert dedup_state_path.exists()

    # Second run should be skipped as duplicate
    patched_scanner.clear()
    patched_scanner.append(fake_record)
    with mock.patch("h4m_bridge.bridge.BridgeClient.post_event") as mocked_post:
        importer = BridgeImporter(
            storage_path=storage_dir,
            backend_url="http://example",
            dedup_path=str(dedup_state_path),
            dry_run=False,
        )
        summary = importer.run()

    mocked_post.assert_not_called()
    assert summary.duplicates == 1


def test_importer_handles_client_errors(storage_dir, dedup_state_path, fake_record, patched_scanner, caplog):
    caplog.set_level(logging.INFO)
    patched_scanner.append(fake_record)
    with mock.patch("h4m_bridge.bridge.BridgeClient.post_event", side_effect=RuntimeError("boom")):
        importer = BridgeImporter(
            storage_path=storage_dir,
            backend_url="http://example",
            dedup_path=str(dedup_state_path),
            dry_run=False,
        )
        summary = importer.run()

    assert summary.failed == 1
    assert summary.imported == 0
    assert "Failed to import log" in caplog.text
    assert not dedup_state_path.exists()

