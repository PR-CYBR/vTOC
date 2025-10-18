# vTOC Developer Guide

This README supplements the main project documentation for contributors working off the `dev` branch. It focuses on local tooling, devcontainer workflows, and debugging practices that keep the FastAPI backend and Vite frontend aligned with the automation bootstrap scripts that ship in this repository.

## Supported development environments

The repository provides a reproducible devcontainer as well as automation for bare-metal setups:

- **VS Code / Cursor AI** – Opening the folder with the Dev Containers extension (VS Code) or Cursor's remote environments automatically builds the image defined in [`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json). The container installs Python, Node.js, pnpm, uv, and Postgres client tooling, then runs `make setup-local` so the bootstrap logic wires generated `.env` files and installs frontend dependencies.
- **Docker CLI** – `./scripts/dev_shell.sh` mirrors the devcontainer experience for contributors without the VS Code extension. It launches the same image using Docker Compose, brings up a Postgres sidecar, and optionally runs the bootstrap script before dropping you into an interactive shell.
- **Local host bootstrap** – Existing workflows that run directly on macOS/Linux remain supported through `make setup-local` or `python -m scripts.bootstrap_cli setup local`. The prerequisite checker still verifies `pnpm` (8.6+), Python 3.10+, and Docker tooling before touching the filesystem.

## Dependency expectations

The bootstrap CLI drives all Make targets and scripts so contributors do not need to memorize tool-specific commands:

- `make setup-local` / `python -m scripts.bootstrap_cli setup local` – Generates `.env.local`, `.env.station`, installs frontend dependencies with pnpm, and prepares backend settings from the config bundle.
- `make dev-shell ARGS="--setup"` – Builds the devcontainer, starts Postgres, runs the local bootstrap inside the container, and leaves you in an interactive shell with the virtualenv active.
- `pnpm --dir frontend dev` – Runs the Vite dev server on port 5173 once the bootstrap script has hydrated environment files.
- `uvicorn backend.app.main:app --reload` – Uses the `.venv` created inside the devcontainer (or your local virtualenv) to serve the FastAPI backend on port 8080.

The devcontainer image pins pnpm 8.6, Node.js 18, Python 3.10, uv, and Postgres client utilities to match CI expectations. If you bootstrap locally without Docker ensure the same versions are installed or rely on the prerequisite helper in `scripts/lib/prereqs.sh`.

## Debugging workflows

- **Backend (FastAPI)** – Run `uvicorn backend.app.main:app --reload` and attach VS Code's Python debugger using the `Python: Remote Attach` configuration. The default interpreter points at `.venv/bin/python` so breakpoints work out of the box inside the devcontainer shell.
- **Frontend (Vite/React)** – Use `pnpm --dir frontend dev -- --host` to expose the dev server inside the container. VS Code's built-in Edge/Chrome debug profiles can attach via `http://localhost:5173`.
- **Database (Postgres)** – The devcontainer Compose file exposes a `database` service seeded by the bootstrap pipeline. Connect with `psql postgresql://vtoc:vtocpass@localhost:5432/vtoc` from inside the container or `docker compose -f .devcontainer/docker-compose.devcontainer.yml exec database psql -U vtoc` from the host.
- **Automation scripts** – Use `python -m scripts.bootstrap_cli --help` to discover subcommands and re-run targeted workflows such as `python -m scripts.bootstrap_cli frontend test` for vitest or `python -m scripts.bootstrap_cli backend lint` for Ruff.

Refer to [`docs/development.md`](docs/development.md) for deeper dives into the devcontainer architecture, available Make targets, and troubleshooting tips shared by the wider contributor community.
