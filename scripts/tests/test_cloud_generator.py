from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.bootstrap import cloud


GOLDEN_DIR = Path(__file__).parent / "golden" / "cloud"


def _read(path: Path) -> str:
    return path.read_text()


def _golden(name: str) -> str:
    return _read(GOLDEN_DIR / name)


@pytest.mark.usefixtures("tmp_path")
def test_generate_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Running with defaults should mirror the golden assets."""

    monkeypatch.setattr(cloud.shutil, "which", lambda name: None)

    output_root = tmp_path / "infra"
    result = cloud.generate_cloud_assets(
        {},
        repo_root=cloud.REPO_ROOT,
        terraform_source_dir=cloud.DEFAULT_TERRAFORM_SOURCE_DIR,
        output_root=output_root,
        fallback_bundle_path=cloud.DEFAULT_FALLBACK_BUNDLE_PATH,
    )

    terraform_dir = output_root / "terraform"
    ansible_dir = output_root / "ansible"

    assert _read(terraform_dir / "main.tf") == _golden("main.tf")
    assert _read(terraform_dir / "variables.tf") == _golden("variables.tf")
    assert _read(terraform_dir / "outputs.tf") == _golden("outputs.tf")

    assert _read(ansible_dir / "inventory.ini") == _golden("inventory.ini")
    assert _read(ansible_dir / "group_vars" / "all.yml") == _golden("group_vars_all.yml")
    assert _read(ansible_dir / "playbook.yml") == _golden("playbook.yml")

    manifest = json.loads(result.manifest_path.read_text())
    assert manifest["bundleSource"] == "fallback"
    assert manifest["inventory"]["source"] == "lookup-command"
    assert manifest["inventory"]["path"] == "ansible/inventory.ini"
    assert manifest["images"]["backend"] == ""
    assert any("fallback" in warning for warning in manifest["warnings"])
