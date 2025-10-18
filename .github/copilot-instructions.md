# Copilot Guidance for vTOC

## Repository Conventions
- Prefer readable, well-documented code that matches existing formatting tools (e.g., Prettier for JavaScript/TypeScript, Black for Python).
- Use descriptive names for variables, functions, and files. Avoid unnecessary abbreviations.
- Keep changes minimal and focused; split unrelated updates into separate commits when possible.
- Follow existing linting rules and type-checking configurations defined in `package.json`, `pyproject.toml`, or language-specific config files.

## Architectural Context
- `frontend/` contains the user-facing web application (Next.js/React). Maintain component modularity and reuse shared UI primitives from the `components/` directories.
- `backend/` holds FastAPI services. Observe the service boundary patterns already established and reuse shared utility modules instead of duplicating logic.
- `services/` and `stations/` provide additional microservices and data pipelines. Verify interactions through shared message schemas and database models before introducing new integrations.
- Infrastructure code lives under `deploy/`, `infrastructure/`, and `docker*` files. Align any changes with existing deployment workflows and container configurations.

## Testing Requirements
- Update or add unit tests whenever functionality changes. Run the relevant test suites (e.g., `npm test`, `pytest`, or service-specific commands) before submitting.
- Ensure database migrations are reflected in both migration files and documentation. Apply migrations locally to confirm they succeed.
- For frontend changes, run component and end-to-end tests when available, and validate accessibility for new UI elements.

## Guidance for Copilot
- Prefer suggesting changes that integrate with existing frameworks and utilities rather than rewriting large sections of code.
- Surface potential side effects or required documentation updates in code comments or TODOs instead of silently altering behavior.
- Highlight assumptions, feature flags, or configuration values that might impact deployment environments.

## Avoid These Suggestions
- Do not introduce new dependencies without clear justification and accompanying updates to dependency manifests and lockfiles.
- Avoid generating placeholder code that suppresses errors (e.g., broad `try/except` blocks, `eslint-disable` comments, or `# type: ignore` annotations) unless necessary and well-documented.
- Do not add secrets or hard-coded credentials. Use environment variables and existing secret management patterns instead.
- Avoid making breaking API changes without coordinating updates across all services and clients.
