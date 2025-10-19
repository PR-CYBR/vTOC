from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_setup_pi_generates_minimal_compose(tmp_path: Path) -> None:
    script = REPO_ROOT / "scripts" / "setup_pi.sh"
    assert script.exists(), "setup_pi.sh should be present"

    output_path = tmp_path / "docker-compose.pi.yml"

    env = os.environ.copy()
    env.setdefault("VTOC_CONFIG_JSON", json.dumps({"projectName": "pi-demo"}))
    env["VTOC_BUILD_LOCAL"] = "true"
    env["VTOC_PULL_IMAGES"] = "false"
    env["VTOC_COMPOSE_FILENAME"] = str(output_path)

    subprocess.run([str(script), "--build-local"], check=True, cwd=REPO_ROOT, env=env)

    assert output_path.exists()

    compose_data = yaml.safe_load(output_path.read_text())

    assert set(compose_data["services"].keys()) == {"backend", "frontend", "scraper"}
    assert "database" not in compose_data["services"]
    for service in compose_data["services"].values():
        assert service["platform"] == "linux/arm64"
        assert "build" in service
