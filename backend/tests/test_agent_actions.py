import hashlib
import hmac
import json
import os
from datetime import datetime
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

from backend.app import schemas
from backend.app.config import reset_settings_cache
from backend.app.main import app
from backend.app.services.agentkit import get_agentkit_client
from backend.app.services.supabase import get_supabase_repository

os.environ.setdefault("AGENTKIT_API_BASE_URL", "https://agentkit.test/api")
os.environ.setdefault("AGENTKIT_API_KEY", "test-key")
os.environ.setdefault("AGENTKIT_ORG_ID", "test-org")
os.environ.setdefault("CHATKIT_WEBHOOK_SECRET", "super-secret")

reset_settings_cache()


class FakeSupabaseRepository:
    def __init__(self) -> None:
        self._audits_by_id: Dict[int, schemas.AgentActionAuditRead] = {}
        self._ids_by_action: Dict[str, int] = {}
        self._id_seq = 1

    def list_agent_action_audits(self, limit: int = 100) -> List[schemas.AgentActionAuditRead]:
        audits = sorted(
            self._audits_by_id.values(),
            key=lambda audit: audit.created_at,
            reverse=True,
        )
        return audits[:limit]

    def get_agent_action_audit_by_action_id(
        self, action_id: str
    ) -> schemas.AgentActionAuditRead | None:
        audit_id = self._ids_by_action.get(action_id)
        if audit_id is None:
            return None
        return self._audits_by_id[audit_id]

    def create_agent_action_audit(
        self, payload: schemas.AgentActionAuditCreate
    ) -> schemas.AgentActionAuditRead:
        now = datetime.utcnow()
        audit = schemas.AgentActionAuditRead(
            id=self._id_seq,
            action_id=payload.action_id,
            tool_name=payload.tool_name,
            status=payload.status,
            request_payload=payload.request_payload,
            response_payload=payload.response_payload,
            error_message=payload.error_message,
            created_at=now,
            updated_at=now,
            completed_at=payload.completed_at,
        )
        self._audits_by_id[self._id_seq] = audit
        self._ids_by_action[audit.action_id] = self._id_seq
        self._id_seq += 1
        return audit

    def update_agent_action_audit(
        self, audit_id: int, payload: schemas.AgentActionAuditUpdate
    ) -> schemas.AgentActionAuditRead:
        existing = self._audits_by_id.get(audit_id)
        if existing is None:
            raise AssertionError("Audit not found")
        data = existing.model_dump()
        updates = payload.model_dump(exclude_unset=True)
        data.update(updates)
        data["id"] = audit_id
        data["updated_at"] = datetime.utcnow()
        audit = schemas.AgentActionAuditRead.model_validate(data)
        self._audits_by_id[audit_id] = audit
        self._ids_by_action[audit.action_id] = audit_id
        return audit


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
def fake_supabase_repo() -> FakeSupabaseRepository:
    return FakeSupabaseRepository()


@pytest.fixture()
def client(fake_supabase_repo: FakeSupabaseRepository) -> TestClient:
    test_client = TestClient(app)

    async def _override_client() -> DummyAgentKit:
        return DummyAgentKit()

    app.dependency_overrides[get_agentkit_client] = _override_client
    app.dependency_overrides[get_supabase_repository] = lambda: fake_supabase_repo

    try:
        yield test_client
    finally:
        app.dependency_overrides.pop(get_agentkit_client, None)
        app.dependency_overrides.pop(get_supabase_repository, None)
        test_client.close()


def test_execute_action_creates_audit_record(
    client: TestClient, fake_supabase_repo: FakeSupabaseRepository
):
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

    audits = fake_supabase_repo.list_agent_action_audits()
    assert len(audits) == 1
    audit = audits[0]
    assert audit.tool_name == "ping"
    assert audit.status == "queued"
    assert audit.request_payload == {"host": "1.1.1.1"}


def test_webhook_updates_audit(
    client: TestClient, fake_supabase_repo: FakeSupabaseRepository
):
    fake_supabase_repo.create_agent_action_audit(
        schemas.AgentActionAuditCreate(
            action_id="agentkit-action-123",
            tool_name="ping",
            status="queued",
        )
    )

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

    audit = fake_supabase_repo.get_agent_action_audit_by_action_id("agentkit-action-123")
    assert audit is not None
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


def test_execute_action_requires_agentkit_configuration(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("AGENTKIT_API_KEY", raising=False)
    monkeypatch.delenv("AGENTKIT_ORG_ID", raising=False)
    reset_settings_cache()

    response = client.post(
        "/api/v1/agent-actions/execute",
        json={"tool_name": "ping", "action_input": {"message": "hello"}},
    )

    assert response.status_code == 503

    monkeypatch.setenv("AGENTKIT_API_KEY", "test-key")
    monkeypatch.setenv("AGENTKIT_ORG_ID", "test-org")
    reset_settings_cache()


def test_execute_action_updates_existing_audit(
    client: TestClient,
    fake_supabase_repo: FakeSupabaseRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_supabase_repo.create_agent_action_audit(
        schemas.AgentActionAuditCreate(
            action_id="agentkit-action-123",
            tool_name="ping",
            status="queued",
        )
    )

    async def _complete(self, tool_name: str, action_input: Dict[str, Any], metadata=None):
        self.executions.append({
            "tool_name": tool_name,
            "action_input": action_input,
            "metadata": metadata,
        })
        return {
            "action_id": "agentkit-action-123",
            "status": "succeeded",
            "result": {"accepted": True},
        }

    monkeypatch.setattr(DummyAgentKit, "execute_action", _complete, raising=True)

    response = client.post(
        "/api/v1/agent-actions/execute",
        json={
            "tool_name": "ping",
            "action_input": {"host": "1.1.1.1"},
            "metadata": {"priority": "high"},
        },
    )

    assert response.status_code == 202
    audit = fake_supabase_repo.get_agent_action_audit_by_action_id("agentkit-action-123")
    assert audit is not None
    assert audit.status == "succeeded"
    assert audit.response_payload == {"accepted": True}
    assert audit.completed_at is not None
