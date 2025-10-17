"""Test fixtures for H4M bridge."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Iterable

import pytest

BRIDGE_ROOT = Path(__file__).resolve().parents[1]
if str(BRIDGE_ROOT) not in sys.path:
    sys.path.insert(0, str(BRIDGE_ROOT))

from h4m_bridge.dedup import FileDeduplicator  # noqa: E402  pylint: disable=wrong-import-position


@pytest.fixture()
def storage_dir(tmp_path: Path) -> Path:
    base = tmp_path / "storage"
    base.mkdir()
    return base


@pytest.fixture()
def dedup_state_path(tmp_path: Path) -> Path:
    return tmp_path / "dedup" / "state.json"


def create_file(path: Path, content: bytes | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        path.write_text(content)
    else:
        path.write_bytes(content)


@pytest.fixture()
def sample_logs(storage_dir: Path) -> Dict[str, Path]:
    paths = {
        "iq": storage_dir / "captures" / "2024" / "sample.iq",
        "decoded_json": storage_dir / "decoded" / "message.json",
        "decoded_txt": storage_dir / "decoded" / "legacy.log",
    }
    create_file(paths["iq"], b"IQDATA" * 16)
    create_file(paths["decoded_json"], json.dumps({"channel": "alpha", "frames": 12}) + "\n")
    create_file(paths["decoded_txt"], "timestamp=1 level=INFO message=ok\n")
    return paths


@pytest.fixture()
def deduplicator(dedup_state_path: Path) -> Iterable[FileDeduplicator]:
    with FileDeduplicator(dedup_state_path) as dedup:
        yield dedup

