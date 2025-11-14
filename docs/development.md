# Development environment reference

This document explains how to work with the devcontainer, helper scripts, and Make targets that automate the vTOC developer experience. The goal is to keep backend, frontend, and automation tooling aligned regardless of whether you use VS Code, Cursor AI, or a plain Docker CLI workflow.

## Devcontainer layout

The devcontainer lives under `.devcontainer/` and is composed of three key files:

| File | Purpose |
| ---- | ------- |
| `devcontainer.json` | Declares the workspace folder, forwards VS Code settings, runs `make setup-local` on create, and replays dependency sync commands when the editor attaches. |
| `Dockerfile` | Builds on the official `mcr.microsoft.com/devcontainers/base` image, installs Python 3.10 tooling, Node.js 18 with pnpm 8.6, uv, and Postgres client libraries, and prepares a project-local virtual environment. |
| `docker-compose.devcontainer.yml` | Defines the `devcontainer` service alongside a Postgres sidecar that mimics the default bootstrap stack. Named volumes cache Python, pnpm, and Postgres data across rebuilds. |

When the container is created the `postCreateCommand` runs `make setup-local`, which delegates to `python -m scripts.bootstrap.local`. The bootstrap routine generates `.env.local`/`.env.station`, validates configuration bundles, and installs frontend dependencies before emitting next steps. After the editor attaches the `postAttachCommand` runs `pnpm --dir frontend install` and `uv pip sync backend/requirements.txt` to guarantee dependencies stay in sync with lockfiles.

### Running without the VS Code extension

Use `scripts/dev_shell.sh` to recreate the devcontainer locally. The script wraps `docker compose` so you can:

- Launch an interactive shell: `./scripts/dev_shell.sh`
- Run the bootstrap inside the container: `./scripts/dev_shell.sh --setup`
- Execute ad-hoc commands without the Postgres sidecar: `./scripts/dev_shell.sh --no-database -- pnpm --dir frontend test`

The script respects the same `.devcontainer/docker-compose.devcontainer.yml` definition as VS Code, so any changes to the image or sidecars automatically apply to manual workflows.

### Stopping services and cleaning up

The Compose project name defaults to the folder name (`vtoc`). Run `docker compose -f .devcontainer/docker-compose.devcontainer.yml down` to stop the developer stack and remove the Postgres volume. To prune cached dependency volumes, pass `--volumes`.

## Make targets

The `Makefile` now includes a `dev-shell` target that delegates to the helper script:

```bash
make dev-shell            # interactive shell with cached dependencies
make dev-shell ARGS="--setup"  # run bootstrap before dropping into the shell
```

All existing targets continue to route through `scripts/bootstrap_cli.py`, ensuring consistent behavior between containerized and bare-metal workflows.

## Troubleshooting tips

- **Bootstrap failures about pnpm** – The devcontainer installs pnpm via Corepack. If the host CLI path overrides it, run `corepack prepare pnpm@8.6.12 --activate` inside the container or ensure `pnpm` resolves to the version pinned in the Dockerfile.
- **Terraform timeouts** – The local bootstrap attempts to read Terraform outputs when the binary is present. Set `VTOC_CONFIG_JSON` with a `configBundle` override or install Terraform using `asdf`/`brew` before re-running `make setup-local` if you need infrastructure-driven bundles.
- **Postgres already running** – `scripts/dev_shell.sh` starts the sidecar unless `--no-database` is provided. Use that flag if you have an existing Postgres instance bound to port 5432.

For deeper architectural details, see the main README.dev.md in the repository root and the service-specific docs under `docs/`.
