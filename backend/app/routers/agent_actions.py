"""Router for AgentKit integrations."""
from __future__ import annotations

import hashlib
import hmac
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import Settings, get_settings
from ..db import get_db
from ..services.agentkit import AgentKitClient, AgentKitError, get_agentkit_client

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
def list_audits(db: Session = Depends(get_db)):
    return (
        db.query(models.AgentActionAudit)
        .order_by(models.AgentActionAudit.created_at.desc())
        .limit(100)
        .all()
    )


@router.post(
    "/execute",
    response_model=schemas.AgentActionExecuteResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def execute_action(
    payload: schemas.AgentActionExecuteRequest,
    db: Session = Depends(get_db),
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
    audit = (
        db.query(models.AgentActionAudit)
        .filter(models.AgentActionAudit.action_id == action_id)
        .one_or_none()
    )
    if audit is None:
        audit = models.AgentActionAudit(
            action_id=action_id,
            tool_name=payload.tool_name,
            status=status_value,
            request_payload=payload.action_input,
            response_payload=response.get("result"),
            error_message=response.get("error"),
        )
    else:
        audit.tool_name = payload.tool_name
        audit.status = status_value
        audit.request_payload = payload.action_input
        audit.response_payload = response.get("result")
        audit.error_message = response.get("error")
        audit.updated_at = datetime.utcnow()

    if status_value in {"succeeded", "failed"}:
        audit.completed_at = datetime.utcnow()

    db.add(audit)
    db.commit()

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
    db: Session = Depends(get_db),
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

    audit = (
        db.query(models.AgentActionAudit)
        .filter(models.AgentActionAudit.action_id == event.action_id)
        .one_or_none()
    )

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

    if audit is None:
        audit = models.AgentActionAudit(
            action_id=event.action_id,
            tool_name=tool_name or "unknown",
            status=event.status,
            response_payload=event.result,
            error_message=event.error,
        )
    else:
        audit.status = event.status
        audit.response_payload = event.result
        audit.error_message = event.error
        audit.updated_at = datetime.utcnow()
        if tool_name:
            audit.tool_name = tool_name

    if event.status in {"succeeded", "failed"}:
        audit.completed_at = datetime.utcnow()

    db.add(audit)
    db.commit()

    return {"received": True}
