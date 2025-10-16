"""Router for AgentKit integrations."""
from __future__ import annotations

import hashlib
import hmac
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status

from .. import schemas
from ..config import Settings, get_settings
from ..services.agentkit import AgentKitClient, AgentKitError, get_agentkit_client
from ..services.supabase import (
    SupabaseApiError,
    SupabaseRepository,
    get_supabase_repository,
)

router = APIRouter(prefix="/api/v1/agent-actions", tags=["agent-actions"])


@router.get("/tools", response_model=List[schemas.AgentTool])
async def list_tools(
    client: AgentKitClient = Depends(get_agentkit_client),
    settings: Settings = Depends(get_settings),
):
    if not settings.is_agentkit_configured:
        return []
    tools = await client.list_tools()
    allowed = set(settings.chatkit_allowed_tools)
    if allowed:
        return [tool for tool in tools if tool.get("name") in allowed]
    return tools


@router.get("/audits", response_model=List[schemas.AgentActionAuditRead])
def list_audits(repo: SupabaseRepository = Depends(get_supabase_repository)):
    try:
        return repo.list_agent_action_audits()
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post(
    "/execute",
    response_model=schemas.AgentActionExecuteResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def execute_action(
    payload: schemas.AgentActionExecuteRequest,
    repo: SupabaseRepository = Depends(get_supabase_repository),
    client: AgentKitClient = Depends(get_agentkit_client),
    settings: Settings = Depends(get_settings),
):
    if not settings.is_agentkit_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AgentKit credentials are not configured",
        )

    try:
        response = await client.execute_action(
            payload.tool_name, payload.action_input, metadata=payload.metadata
        )
    except AgentKitError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AgentKit request failed",
        ) from exc

    action_id = str(response.get("action_id") or response.get("id") or "").strip()
    if not action_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AgentKit did not return an action identifier",
        )

    status_value = response.get("status", "queued")
    try:
        existing_audit = repo.get_agent_action_audit_by_action_id(action_id)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    completed_at = None
    if status_value in {"succeeded", "failed"}:
        completed_at = datetime.utcnow()

    if existing_audit is None:
        audit_payload = schemas.AgentActionAuditCreate(
            action_id=action_id,
            tool_name=payload.tool_name,
            status=status_value,
            request_payload=payload.action_input,
            response_payload=response.get("result"),
            error_message=response.get("error"),
            completed_at=completed_at,
        )
        try:
            repo.create_agent_action_audit(audit_payload)
        except SupabaseApiError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    else:
        update_payload = schemas.AgentActionAuditUpdate(
            tool_name=payload.tool_name,
            status=status_value,
            request_payload=payload.action_input,
            response_payload=response.get("result"),
            error_message=response.get("error"),
            completed_at=completed_at,
        )
        try:
            repo.update_agent_action_audit(existing_audit.id, update_payload)
        except SupabaseApiError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return schemas.AgentActionExecuteResponse(
        action_id=action_id,
        status=status_value,
        result=response.get("result"),
        message=response.get("message"),
    )


def _verify_signature(secret: str, signature: str | None, body: bytes) -> bool:
    if not secret:
        return True
    if not signature:
        return False
    computed = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, computed)


@router.post("/webhook", status_code=status.HTTP_202_ACCEPTED)
async def webhook(
    request: Request,
    repo: SupabaseRepository = Depends(get_supabase_repository),
    client: AgentKitClient = Depends(get_agentkit_client),
    settings: Settings = Depends(get_settings),
):
    body = await request.body()
    signature = request.headers.get("x-chatkit-signature")

    if not _verify_signature(settings.chatkit_webhook_secret, signature, body):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    try:
        event = schemas.AgentActionWebhookEvent.model_validate_json(body)
    except Exception as exc:  # pragma: no cover - Pydantic raises ValidationError
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload") from exc

    try:
        audit = repo.get_agent_action_audit_by_action_id(event.action_id)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    tool_name = None
    if audit is not None:
        tool_name = audit.tool_name

    if tool_name is None and settings.is_agentkit_configured:
        try:
            action_details = await client.get_action(event.action_id)
            tool_name = action_details.get("tool_name") or action_details.get("tool")
        except AgentKitError:
            tool_name = "unknown"
    elif tool_name is None:
        tool_name = "unknown"

    completed_at = None
    if event.status in {"succeeded", "failed"}:
        completed_at = datetime.utcnow()

    if audit is None:
        create_payload = schemas.AgentActionAuditCreate(
            action_id=event.action_id,
            tool_name=tool_name or "unknown",
            status=event.status,
            response_payload=event.result,
            error_message=event.error,
            completed_at=completed_at,
        )
        try:
            repo.create_agent_action_audit(create_payload)
        except SupabaseApiError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    else:
        update_payload = schemas.AgentActionAuditUpdate(
            tool_name=tool_name or audit.tool_name,
            status=event.status,
            response_payload=event.result,
            error_message=event.error,
            completed_at=completed_at,
        )
        try:
            repo.update_agent_action_audit(audit.id, update_payload)
        except SupabaseApiError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return {"received": True}
