from __future__ import annotations

import json
from pathlib import Path

from scripts.bootstrap import local


def _noop_emitter(event: str, payload: dict[str, object]) -> None:
    pass


def test_resolve_config_bundle_uses_fallback_when_terraform_unavailable(monkeypatch, tmp_path: Path) -> None:
    fallback_bundle = {
        "frontend": {
            "env": {
                "FOO": "BAR",
            }
        }
    }
    fallback_path = tmp_path / "config_bundle.json"
    fallback_path.write_text(json.dumps(fallback_bundle))

    def fake_fetch(terraform_dir: Path, *, emitter: local.Emitter):
        return None, "not_found"

    monkeypatch.setattr(local, "fetch_terraform_bundle", fake_fetch)

    selection = local.resolve_config_bundle(
        config={},
        terraform_dir=tmp_path / "terraform",
        fallback_path=fallback_path,
        emitter=_noop_emitter,
    )

    assert selection.source == "fallback"
    assert selection.bundle["frontend"]["env"]["FOO"] == "BAR"
