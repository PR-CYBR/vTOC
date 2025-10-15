# Contributing to vTOC

Thank you for your interest in improving vTOC! The project now features ChatKit/AgentKit orchestration and multi-station
provisioning. This guide explains how to set up your environment, run tests, and follow project standards.

## Code of conduct

- Be respectful and inclusive.
- Provide constructive feedback.
- Follow project standards and conventions.

## Getting started

### 1. Fork and clone

```bash
git clone https://github.com/YOUR-USERNAME/vTOC.git
cd vTOC
```

### 2. Bootstrap the stack

Use the unified setup script via the Makefile. This installs dependencies, generates environment files, and provisions station
metadata.

```bash
make setup-local
```

If you prefer containers run:

```bash
make setup-container
make compose-up
```

Stop services with `make compose-down`.

### 3. Create a branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

## Development guidelines

### Backend (FastAPI)

```
backend/
├── app/
│   ├── api/            # Routers
│   ├── services/       # Domain services (AgentKit, ChatKit, telemetry)
│   ├── schemas/        # Pydantic models
│   └── main.py         # Application entry point
└── tests/              # Pytest suites
```

- Follow PEP 8, use type hints, and add docstrings to public functions.
- Keep endpoints asynchronous.
- Add unit tests for new services or routers (`make backend-test`).
- When touching database models update Alembic migrations and note changes in [`docs/CHANGELOG.md`](docs/CHANGELOG.md).

### Frontend (React + TypeScript)

```
frontend/
├── src/
│   ├── components/     # Reusable UI
│   ├── features/       # Station role widgets
│   ├── pages/          # Route-level views
│   ├── services/       # API clients
│   └── App.tsx         # Root component
└── tests/              # Vitest setup
```

- Prefer functional components and hooks.
- Keep components role-aware using `VITE_STATION_ROLE` props.
- Co-locate tests with components when practical.
- Run `make frontend-test` before opening a PR.

### Database changes

- Always create migrations for schema updates: `alembic revision --autogenerate -m "message"`.
- Run `alembic upgrade head` for each station role or use the helper loop documented in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md#multi-station-postgres).
- Document breaking changes in [`docs/CHANGELOG.md`](docs/CHANGELOG.md).

### AgentKit / ChatKit integrations

- Define new playbooks in `agents/config/agentkit.yml` and document them in [`docs/TELEMETRY_CONNECTORS.md`](docs/TELEMETRY_CONNECTORS.md).
- Ensure backend webhook logic remains idempotent and covers signature validation.
- Provide fixtures or mock responses for new ChatKit/AgentKit endpoints when adding tests.

## Testing

Use the Makefile targets to keep workflows consistent:

```bash
make backend-test    # pytest -q
make frontend-test   # pnpm test -- --watch=false --passWithNoTests
make scraper-run     # run telemetry scraper locally
```

For integration testing, start the generated Compose stack and exercise APIs:

```bash
make compose-up
curl http://localhost:8080/healthz
curl http://localhost:8080/api/v1/chatkit/webhook -d '{"text":"ping"}'
make compose-down
```

## Documentation expectations

- Update relevant docs in the `docs/` directory when introducing user-facing changes.
- Cross-link new sections from `README.md` and [`docs/CHANGELOG.md`](docs/CHANGELOG.md).
- Include station role considerations when modifying setup instructions.

## Submitting changes

1. Run the appropriate tests.
2. Commit with clear messages (e.g., `git commit -am "feat: add intel playbook"`).
3. Push your branch and open a pull request. Summarize ChatKit/AgentKit impacts and reference updated docs.

Thank you for contributing!
