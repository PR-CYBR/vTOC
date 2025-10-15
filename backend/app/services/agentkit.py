"""AgentKit API client abstractions."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from ..config import Settings, get_settings


class AgentKitError(RuntimeError):
    """Raised when the AgentKit API returns an error."""


class AgentKitNotConfiguredError(AgentKitError):
    """Raised when AgentKit credentials are missing."""


class AgentKitClient:
    """Thin async wrapper around the AgentKit HTTP API."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._transport = transport

    def _require_configuration(self) -> Settings:
        if not self._settings.is_agentkit_configured:
            raise AgentKitNotConfiguredError("AgentKit credentials are not configured")
        return self._settings

    def _client_kwargs(self) -> Dict[str, Any]:
        settings = self._require_configuration()
        base_url = settings.agentkit_api_base_url.rstrip('/')
        return {
            'base_url': base_url,
            'timeout': settings.agentkit_timeout_seconds,
            'transport': self._transport,
            'headers': {
                'Authorization': f"Bearer {settings.agentkit_api_key}",
                'X-AgentKit-Org': settings.agentkit_org_id,
                'Content-Type': 'application/json',
            },
        }

    async def list_tools(self) -> List[Dict[str, Any]]:
        settings = self._require_configuration()
        async with httpx.AsyncClient(**self._client_kwargs()) as client:
            try:
                response = await client.get(f"/orgs/{settings.agentkit_org_id}/tools")
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:  # pragma: no cover - network error path
                raise AgentKitError(f"AgentKit tools request failed: {exc.response.text}") from exc
            payload = response.json()
            tools = payload.get('tools') if isinstance(payload, dict) else payload
            if tools is None:
                return []
            if isinstance(tools, list):
                return tools
            raise AgentKitError('Unexpected tools response payload from AgentKit')

    async def execute_action(
        self,
        tool_name: str,
        action_input: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        settings = self._require_configuration()
        body = {'tool_name': tool_name, 'action_input': action_input}
        if metadata:
            body['metadata'] = metadata
        async with httpx.AsyncClient(**self._client_kwargs()) as client:
            try:
                response = await client.post(
                    f"/orgs/{settings.agentkit_org_id}/actions", json=body
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:  # pragma: no cover - network error path
                raise AgentKitError(f"AgentKit action failed: {exc.response.text}") from exc
            return response.json()

    async def get_action(self, action_id: str) -> Dict[str, Any]:
        settings = self._require_configuration()
        async with httpx.AsyncClient(**self._client_kwargs()) as client:
            try:
                response = await client.get(
                    f"/orgs/{settings.agentkit_org_id}/actions/{action_id}"
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:  # pragma: no cover - network error path
                raise AgentKitError(f"AgentKit action lookup failed: {exc.response.text}") from exc
            return response.json()


async def get_agentkit_client() -> AgentKitClient:
    return AgentKitClient()
