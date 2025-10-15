# Deployment Guide

This document covers running vTOC locally, in Docker Swarm, and via Fly.io. All flows rely on the container images produced by the GitHub Actions pipeline.

## Local development

1. Copy the environment examples if desired: `cp .env.example .env`.
2. Run `make setup-local` to install dependencies and verify the frontend build.
3. Launch the dev servers:
   ```bash
   pnpm --dir frontend dev
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8080
   ```
4. Health checks:
   - Backend: `curl http://localhost:8080/healthz`
   - Frontend (Vite dev server): http://localhost:5173

## Docker Compose (development)

1. Generate the compose file (optional flags can enable Traefik/n8n/Wazuh):
   ```bash
   ./scripts/setup.sh --mode container --config scripts/examples/container.json
   ```
2. Start the stack:
   ```bash
   docker compose -f docker-compose.generated.yml up -d
   ```
3. Services:
   - Backend: http://localhost:8080
   - Frontend (nginx): http://localhost:8081
   - `/healthz` should return HTTP 200 once the backend is up.

## Docker Swarm (production)

Deploy the stack using the provided `docker-stack.yml` after logging into your swarm manager:

```bash
docker stack deploy -c docker-stack.yml vtoc
```

### Traefik routing

* `Host("vtoc.local")` → frontend service (port 8081 in the container)
* `Host("api.vtoc.local")` → backend service (port 8080)

Attach your DNS or overlay networking solution (ZeroTier/Tailscale) by uncommenting the relevant sections and providing the secrets `ZEROTIER_NETWORK_ID` / `TS_AUTHKEY` at deploy time.

Optional integrations (MediaMTX, TAK Server) are scaffolded and commented for future enablement.

## Fly.io

The `fly.toml` definition targets the backend container on port 8080.

Deployment workflow:

```bash
flyctl auth token ${FLY_API_TOKEN}
flyctl deploy --image ghcr.io/<repo>/backend:<sha> --remote-only
```

A GitHub Actions workflow (`fly-deploy.yml`) runs the same command when triggered manually or on version tags starting with `v`.

## Sample configuration inputs

Example `inputs.json` enabling Traefik in container mode and customizing the cloud provider:

```json
{
  "projectName": "vtoc",
  "services": {
    "traefik": true,
    "postgres": true,
    "n8n": false,
    "wazuh": false
  },
  "cloud": {
    "provider": "aws",
    "region": "us-east-1"
  }
}
```

Pass this file via `./scripts/setup.sh --mode container --config inputs.json` or inline with `--config-json`.
