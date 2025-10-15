import hashlib
import hmac
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:?cache=shared")
os.environ.setdefault("AGENTKIT_API_BASE_URL", "https://agentkit.test/api")
os.environ.setdefault("AGENTKIT_API_KEY", "test-key")
os.environ.setdefault("AGENTKIT_ORG_ID", "test-org")
os.environ.setdefault("CHATKIT_WEBHOOK_SECRET", "super-secret")

from backend.app.config import reset_settings_cache  # noqa: E402
from backend.app.db import Base, SessionLocal, engine, get_db  # noqa: E402
from backend.app.main import app  # noqa: E402
from backend.app.models import AgentActionAudit  # noqa: E402
from backend.app.services.agentkit import get_agentkit_client  # noqa: E402

reset_settings_cache()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        with engine.begin() as connection:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(table.delete())


class DummyAgentKit:
    def __init__(self) -> None:
        self.executions: List[Dict[str, Any]] = []

    async def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "ping",
                "description": "Simple connectivity check",
                "signature": {"type": "object"},
            }
        ]

    async def execute_action(
        self,
        tool_name: str,
        action_input: Dict[str, Any],
        metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        self.executions.append(
            {"tool_name": tool_name, "action_input": action_input, "metadata": metadata}
        )
        return {
            "action_id": "agentkit-action-123",
            "status": "queued",
            "result": {"accepted": True},
        }

    async def get_action(self, action_id: str) -> Dict[str, Any]:
        return {
            "action_id": action_id,
            "tool_name": "ping",
            "status": "succeeded",
            "result": {"accepted": True},
        }


@pytest.fixture()
def client() -> TestClient:
    test_client = TestClient(app)

    async def _override_client() -> DummyAgentKit:
        return DummyAgentKit()

    app.dependency_overrides[get_agentkit_client] = _override_client

    def _override_db() -> Iterator[SessionLocal]:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_db

    try:
        yield test_client
    finally:
        app.dependency_overrides.pop(get_agentkit_client, None)
        app.dependency_overrides.pop(get_db, None)
        test_client.close()


def test_execute_action_creates_audit_record(client: TestClient):
    response = client.post(
        "/api/v1/agent-actions/execute",
        json={
            "tool_name": "ping",
            "action_input": {"host": "1.1.1.1"},
        },
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["action_id"] == "agentkit-action-123"

    with SessionLocal() as session:
        audits = session.query(AgentActionAudit).all()
        assert len(audits) == 1
        audit = audits[0]
        assert audit.tool_name == "ping"
        assert audit.status == "queued"
        assert audit.request_payload == {"host": "1.1.1.1"}


def test_webhook_updates_audit(client: TestClient):
    # seed audit record
    with SessionLocal() as session:
        session.add(
            AgentActionAudit(
                action_id="agentkit-action-123",
                tool_name="ping",
                status="queued",
            )
        )
        session.commit()

    body = {
        "action_id": "agentkit-action-123",
        "status": "succeeded",
        "result": {"accepted": True},
    }
    raw = json.dumps(body).encode("utf-8")
    signature = hmac.new(
        os.environ["CHATKIT_WEBHOOK_SECRET"].encode("utf-8"),
        raw,
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        "/api/v1/agent-actions/webhook",
        data=raw,
        headers={
            "x-chatkit-signature": signature,
            "content-type": "application/json",
        },
    )

    assert response.status_code == 202

    with SessionLocal() as session:
        audit = session.query(AgentActionAudit).one()
        assert audit.status == "succeeded"
        assert audit.response_payload == {"accepted": True}
        assert audit.completed_at is not None


def test_webhook_rejects_bad_signature(client: TestClient):
    body = json.dumps({"action_id": "x", "status": "queued"}).encode("utf-8")
    response = client.post(
        "/api/v1/agent-actions/webhook",
        data=body,
        headers={"x-chatkit-signature": "invalid", "content-type": "application/json"},
    )

    assert response.status_code == 401
