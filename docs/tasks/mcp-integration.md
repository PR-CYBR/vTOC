# MCP Integration Task Backlog

These tasks track the work required to implement the vTOC ↔ OpenAI MCP bridge and expose the new agent-driven workflows across the stack.

## 1. Stand up the MCP adapter service
- [ ] Scaffold `agents/mcp/` with configuration, dependency pins, and an async FastMCP server that proxies vTOC REST operations.
- [ ] Implement tool handlers for operations/mission reads and agent control actions, including environment-driven authentication.
- [ ] Provide a runnable entry point (Uvicorn app) and module documentation describing the exposed MCP tools/resources.

## 2. Add automated validation for the MCP server
- [ ] Create pytest suites under `agents/mcp/tests/` that cover success paths, backend failures, and authorization guardrails via mocked responses.
- [ ] Wire the tests into existing automation (pytest/Makefile or tox) so contributors can run them locally and in CI.
- [ ] Supply developer utilities or examples for manual MCP inspection during development.

## 3. Integrate the MCP component into container workflows
- [ ] Publish an `agents/mcp/Dockerfile` and add a `mcp` service to `docker-compose.yml` and `docker-stack.yml` with appropriate networking and secrets.
- [ ] Extend environment templates (`.env.example`, Compose overrides) with MCP-specific variables like base URL, port, and API tokens.
- [ ] Update Traefik or related routing so external AgentKit/ChatKit clients can reach the MCP server when required.

## 4. Enhance bootstrap automation and tooling
- [ ] Add `mcp` subcommands to `scripts/bootstrap_cli.py` and new Makefile targets for running/testing the MCP service.
- [ ] Ensure container/setup scripts build or pull the MCP image and template any required secrets during `setup-container` and `setup-cloud` flows.
- [ ] Document the new commands in contributor onboarding materials.

## 5. Surface MCP capabilities in the ChatKit frontend
- [ ] Update the ChatKit widget/components to accept MCP configuration (server URL, available tools) and propagate mission context.
- [ ] Add UI affordances or actions that map to MCP tool usage, with accompanying unit tests.
- [ ] Refresh frontend environment docs so operators know how to enable MCP-backed features.

## 6. Document configuration, security, and operations changes
- [ ] Extend backend settings and documentation to include MCP server configuration, guardrails, and secret management guidance.
- [ ] Describe how MCP-exposed tools map to existing REST endpoints in `docs/API.md` or related references.
- [ ] Capture deployment/runbook updates across local, Compose, and cloud scenarios.
