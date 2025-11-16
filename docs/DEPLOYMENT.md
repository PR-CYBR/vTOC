# Deployment Guide

This guide covers local workflows, containerized deployments, multi-station Postgres provisioning, Supabase integration, and
Fly.io delivery from the `live` branch. The ChatKit/AgentKit rollout introduces additional environment variables and setup steps
described below.

## Raspberry Pi (low-power)

Operators provisioning Raspberry Pi 5 stations should follow the dedicated
[`docs/deployment/raspberry-pi.md`](deployment/raspberry-pi.md) checklist. It
documents hardware expectations (8 GB RAM, NVMe storage, active cooling),
headless Raspberry Pi OS tuning (GPU split, cgroups, ZRAM, minimal swap),
service enablement/disablement guidance, and a resource-conscious bootstrap
command:

```bash
python3 -m scripts.bootstrap_cli setup local --headless --prefer-remote-supabase
```

The companion compose profile keeps Postgres remote (Supabase) and disables
optional scrapers so the Pi remains within the 2–3 GB RAM envelope during
missions.

## Supabase integration overview

Supabase now hosts the managed Postgres cluster backing vTOC along with row-level security (RLS) policies and authentication
providers consumed by the frontend. Each station role maps to a dedicated schema (or database) inside Supabase and the platform
relies on two Supabase keys:

- `SUPABASE_ANON_KEY` — provided to the frontend for authenticated operator sessions and realtime channels.
- `SUPABASE_SERVICE_ROLE_KEY` — scoped to the backend and automation agents for privileged database access and webhook
  management.

`DATABASE_URL` still points to a Postgres connection string, but the hostname now resolves to the Supabase project. Local
deployments can continue to use the bundled Postgres container; production environments should transition to Supabase to gain
managed backups, PITR, and Auth integration.

## Local development

1. Copy environment examples if desired: `cp .env.example .env`.
2. Run `python -m scripts.bootstrap_cli setup local` (or the `make setup-local` alias) to install dependencies, generate `.env.local`/`.env.station`, and provision ChatKit sandbox channels.
   Provide secrets interactively when prompted or forward a prepared payload via `--config-json` / `--config-json @path/to/config.json`.
   The JSON accepts `chatkit`, `agentkit`, `supabase`, and `station` sections matching [`scripts/inputs.schema.json`](https://github.com/vasa-dev/vTOC/blob/main/scripts/inputs.schema.json);
   the CLI compacts the payload, writes `.env.local`, `.env.station`, and `frontend/.env.local`, then prints structured next-step guidance.
3. Launch the dev servers:
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8080
   pnpm --dir frontend dev
   ```
4. Health checks:
   - Backend: `curl http://localhost:8080/healthz`
   - ChatKit webhook echo: `curl -X POST http://localhost:8080/api/v1/chatkit/webhook -d '{"text":"ping"}'`
   - Frontend: http://localhost:5173

When `.env.local` references a Supabase project the backend connects remotely while the frontend uses the anon key for Auth.
For air-gapped development, set `USE_LOCAL_POSTGRES=1` before running the setup CLI to keep using the bundled Postgres container.

## Docker Compose (development + testing)

CI runs on the `CI` workflow now upload the generated manifest as an artifact named
`docker-compose-generated`. Download it from the workflow run to reuse the
compose bundle emitted by `scripts/setup_container.sh --build-local` without
rerunning the generator locally.

1. Generate the compose file and role secrets:
   ```bash
   python -m scripts.bootstrap_cli setup container --apply
   ```
2. Start the stack:
   ```bash
   python -m scripts.bootstrap_cli compose up
   ```
3. Services:
   - Backend: http://localhost:8080
   - Frontend (nginx): http://localhost:8081
   - Postgres (optional local fallback): `localhost:5432` with databases `vtoc_ops`, `vtoc_intel`, `vtoc_logistics`
   - Traefik dashboard (optional): http://localhost:8080 when enabled in config

If Supabase credentials are present the compose stack skips the Postgres container and points `DATABASE_URL` at Supabase while
still running other services locally.

To stop and clean up run `python -m scripts.bootstrap_cli compose down` (or the legacy `make compose-down`).

### Published images and demo refreshes

The [`Publish Containers` workflow](workflows/publish-containers.md) builds the backend, frontend, and scraper images after the
full test matrix passes. Each run uploads a `docker-compose.generated.yml` artifact that pins the newly published tags; when a
Git tag is created the same file is attached to the release assets. Prior to workshops or demos you can either download the
latest compose artifact from the workflow run or trigger the workflow manually (optionally providing a release tag). Once the
artifact is in hand, run:

```bash
scripts/setup_container.sh --pull --image-tag <tag-from-workflow>
docker compose -f docker-compose.generated.yml up -d
```

The `--pull` flag updates local caches and rewrites the manifest to point at the published images so attendees can launch the
stack without rebuilding containers. The [`Build Live Images` workflow](workflows/build-image-live.md) keeps Fly.io aligned by
retagging the same containers with `:live` whenever the hardened branch advances.

## Docker Swarm (production)

1. Authenticate with your swarm manager.
2. Ensure secrets are available (`CHATKIT_API_KEY`, `CHATKIT_ORG_ID`, `AGENTKIT_CLIENT_ID`, `AGENTKIT_CLIENT_SECRET`,
   `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`). Manage them with `docker secret` or your preferred secret store.
3. Deploy:
   ```bash
   docker stack deploy -c docker-stack.yml vtoc
   ```
4. Traefik routes:
   - `Host("vtoc.local")` → frontend (port 8081 in container)
   - `Host("api.vtoc.local")` → backend (port 8080)

Optional integrations (ZeroTier/Tailscale/MediaMTX/TAK Server) can be enabled by adjusting `scripts/inputs.schema.json` and
rerunning `python -m scripts.bootstrap_cli setup container --config path.json --apply` (or the equivalent Make target).

## Multi-station Postgres provisioning with Supabase

Supabase projects ship with a single Postgres instance. For vTOC we recommend creating a schema per station role (the bootstrap
CLI can automate this when Supabase admin credentials are provided). To provision manually:

1. In the Supabase dashboard create schemas `ops`, `intel`, and `logistics` (or custom roles that match `POSTGRES_STATION_ROLE`).
2. Define Postgres roles scoped to each schema and enable RLS policies to limit row access to the station claims carried in
   Supabase JWTs.
3. Use the Supabase SQL editor or `psql` to run Alembic migrations per schema:
   ```bash
   for role in ops intel logistics; do
     POSTGRES_STATION_ROLE=$role alembic upgrade head
   done
   ```
4. Update `.env.local` so `DATABASE_URL` references the Supabase connection string (available via the Database settings panel) or
   export the value with `supabase db list`. The bootstrap CLI writes this automatically when supplied a Supabase service key.

More topology examples are available in [`docs/DIAGRAMS.md`](DIAGRAMS.md#multi-station-topology).

### Migrating from self-hosted Postgres to Supabase

Existing operators can lift-and-shift data with the following approach:

1. Freeze writes in the legacy cluster and create logical backups per station role:
   ```bash
   pg_dump --format=custom --dbname=postgresql://vtoc_ops@legacy-host/vtoc_ops --file=ops.dump
   ```
2. Create a Supabase project and capture the `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` from the
   dashboard.
3. Import dumps using `supabase db push ops.dump --schema ops` (requires the Supabase CLI) or by uploading through the SQL
   editor.
4. Re-run Alembic migrations against the Supabase connection to ensure extensions and metadata tables match the current release.
5. Update deployment secrets (`DATABASE_URL`, Supabase keys) and restart backend pods/services. The frontend will detect the new
   anon key automatically.
6. Validate Supabase Auth configuration by signing in with an operator account and confirming RLS policies block cross-station
   access.

Supabase enforces RLS by default; the bootstrap CLI applies policies aligned with station roles. When importing data manually,
reapply policies or run `python -m scripts.bootstrap_cli setup cloud --apply` to let the automation restore them.

### Cloud bootstrap workflow

Running `python -m scripts.bootstrap_cli setup cloud` now delegates to a Python generator that mirrors the container workflow:

- A `configBundle` override supplied via `--config`/`--config-json` is preferred. When no override is present the generator
  attempts to read the `config_bundle` Terraform output from `infrastructure/terraform` and gracefully falls back to
  [`scripts/defaults/config_bundle.local.json`](https://github.com/vasa-dev/vTOC/blob/main/scripts/defaults/config_bundle.local.json) when state or the Terraform binary
  is unavailable.
- Terraform and Ansible assets are written under `infra/terraform` and `infra/ansible` along with
  `infra/cloud-manifest.json`. The manifest captures Fly.io image references, required secrets, next commands, and the dynamic
  inventory source so AI assistants can return structured guidance to operators.
- `infra/ansible/inventory.ini` resolves the backend host IP from Terraform outputs. Until `terraform apply` completes the
  companion `group_vars/all.yml` issues `terraform -chdir infra/terraform output -raw backend_ip` at playbook runtime, avoiding
  the previous `1.2.3.4` placeholder.
- The CLI prints the manifest JSON after generation, making it easy to hand the structured summary back to an operator or feed
  it into downstream automation.

When `--apply` or `--configure` is specified, the generator runs `terraform apply`/`ansible-playbook` from the generated
directories and refreshes the manifest so the inventory reflects the assigned address.

### Supabase Auth considerations

- Operator logins use Supabase Auth. Configure providers (email, SSO) in the Supabase dashboard and align JWT claims with the
  `stationRole` metadata expected by the frontend.
- Backend service tokens should be stored as managed secrets (Fly.io, Terraform Cloud variables, or Docker Swarm secrets). Never
  expose the service-role key to the frontend.
- Enable email confirmations or password resets per your security posture; vTOC reads Supabase user metadata to personalize the
  mission console.
- Raspberry Pi deployments benefit from the slimmer backend container. Summing the arm64 base image layers (~46.8 MiB), the
  packaged runtime dependencies (~38.5 MiB), and the runtime shared libraries (~0.14 MiB) yields an ~85.4 MiB image. The
  previous single-stage build kept build toolchains (~8.7 MiB compressed) and larger wheels (~40.9 MiB), pushing the image to
  roughly 96.4 MiB. The multi-stage builder therefore trims about 11 MiB (≈11%) from the Raspberry Pi footprint while still
  delivering the same FastAPI application bundles.【b86e62†L1-L8】【39f59f†L1-L2】【1d2815†L1-L2】【51d630†L1-L8】【e4814d†L1-L2】

## Fly.io (live branch)

The Fly deployment ships the backend container using the `live` branch as the source of truth.

1. Ensure `fly.toml` has `primary_region`, `app`, and `[env]` entries for the backend secrets managed by Terraform. The
   manifest ships blank values for `AGENTKIT_*`, `CHATKIT_*`, and `SUPABASE_*` variables so Fly secrets replace them at
   deploy time. Populate the values with `flyctl secrets set` before deploying:

   ```bash
   flyctl secrets set \
     AGENTKIT_API_BASE_URL=<agentkit-api-base-url> \
     AGENTKIT_API_KEY=<agentkit-api-key> \
     AGENTKIT_ORG_ID=<agentkit-org-id> \
     AGENTKIT_TIMEOUT_SECONDS=<agentkit-timeout-seconds> \
     CHATKIT_ALLOWED_TOOLS=<chatkit-allowed-tools> \
     CHATKIT_API_KEY=<chatkit-api-key> \
     CHATKIT_ORG_ID=<chatkit-org-id> \
     CHATKIT_WEBHOOK_SECRET=<chatkit-webhook-secret> \
     SUPABASE_ANON_KEY=<supabase-anon-key> \
     SUPABASE_JWT_SECRET=<supabase-jwt-secret> \
     SUPABASE_PROJECT_REF=<supabase-project-ref> \
     SUPABASE_SERVICE_ROLE_KEY=<supabase-service-role-key> \
     SUPABASE_URL=<supabase-url>
   ```

   The values typically come from Terraform outputs (or `terraform output fly_secrets_env`) and should match the secrets used
   by your other deployment targets.
2. Authenticate: `flyctl auth login` (or set `FLY_API_TOKEN`).
3. Generate a **read-only** GitHub Container Registry token:
   - Navigate to <https://github.com/settings/tokens?type=beta>.
   - Create a fine-grained personal access token scoped to the `PR-CYBR/vTOC` repository with **read-only** permissions for
     GitHub Packages.
   - Record the username (usually your GitHub handle) and the token value.
4. Export registry credentials for the remote Fly builder:
   ```bash
   export GHCR_USERNAME=<github-handle>
   export GHCR_TOKEN=<read-only-ghcr-pat>
   AUTH=$(printf '%s:%s' "$GHCR_USERNAME" "$GHCR_TOKEN" | base64 | tr -d '\n')
   cat <<EOF > docker-auth.json
{"auths":{"ghcr.io":{"auth":"$AUTH"}}}
EOF
   export DOCKER_AUTH_CONFIG=$(cat docker-auth.json)
   rm docker-auth.json
   ```
   The inline auth export mirrors `docker login ghcr.io` and ensures the remote-only build step can pull the private image.
   Alternatively, run `docker login ghcr.io` and export `DOCKER_CONFIG` pointing to your Docker config directory before
   invoking `flyctl deploy`.
5. Deploy the current `live` branch with the prebuilt image:
   ```bash
   git checkout live
   flyctl deploy --remote-only
   ```
   Operators can use the helper script `scripts/fly_deploy.sh` to automate the auth JSON handoff when running promotions from
   their workstation.
6. GitHub Actions triggers (`fly-deploy.yml`) automatically deploy when `live` updates or when `v*` tags are pushed.
7. Post-deployment, verify health: `flyctl status`, `flyctl logs`, `curl https://<app>.fly.dev/healthz`, and (if you manage
   Supabase keys centrally) `supabase secrets list` to confirm rotation timestamps.

### Terraform Cloud automation

The `python -m scripts.bootstrap_cli setup cloud` workflow can emit Terraform configuration that targets Supabase resources in
addition to ancillary infrastructure. When using Terraform Cloud:

1. Create workspace variables for `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and station-role schema names. Mark the
   service-role key as **sensitive**.
2. Use the Supabase Terraform provider to manage database roles, storage buckets, and Auth settings. The generated module under
   `infrastructure/terraform/supabase` includes examples for creating schema-level policies and issuing anon keys for frontend
   deploys.
3. Enable automatic runs so updates to Supabase configuration (RLS, Auth providers) are version-controlled. The provider surface
   also supports scheduled rotation by uploading new service-role keys and invalidating the prior key via `supabase projects
   secrets revoke`.
4. Downstream modules (Fly.io, Docker secrets, GitHub Actions) should consume the rotated keys via Terraform outputs. Coordinate
   rollouts by updating Fly and Swarm secrets immediately after Terraform applies.

Terraform Cloud variable sets can provide anon keys to frontend deploy pipelines while restricting service-role keys to backend
workspaces.

## Ingress

When exposing vTOC to external traffic, configure TLS/HTTPS for secure communications:

**Traefik (Docker Swarm/Compose):**
- Enable ACME/Let's Encrypt in `traefik/traefik.yml`
- Configure certificate resolvers for automatic TLS
- Set up HTTP to HTTPS redirect rules
- Example in `docker-compose.yml`: Traefik labels for `websecure` entrypoint

**Fly.io:**
- Automatic TLS certificates via Fly.io platform
- Configure custom domains in `fly.toml`
- Certificates managed by Fly proxy layer

**Reverse Proxy (nginx/Caddy):**
- Place reverse proxy in front of backend container
- Configure TLS certificates (Let's Encrypt recommended)
- Proxy pass to `http://localhost:8080/api/v1/`
- Set appropriate headers (`X-Forwarded-For`, `X-Real-IP`)

**Backend Configuration:**
- Backend expects `X-Forwarded-Proto: https` when behind proxy
- Configure CORS origins in `.env.local` to match your domain
- Set `BACKEND_BASE_URL` to your public HTTPS endpoint

## Hardening

Security hardening checklist for production deployments:

**System Level:**
- Enable automatic security updates (`unattended-upgrades` on Debian/Ubuntu)
- Configure firewall (UFW, iptables) to allow only necessary ports
- Disable password authentication for SSH (use keys only)
- Set up fail2ban for SSH brute force protection
- Use non-root user for all services (`vtoc` user recommended)

**Container Security:**
- Run containers as non-root user (use `USER` directive in Dockerfile)
- Apply resource limits (CPU, memory) in Docker Compose/Swarm
- Enable Docker content trust for image verification
- Regularly update base images and rebuild containers
- Scan images for vulnerabilities (`docker scan` or Trivy)

**Secrets Management:**
- Never commit secrets to version control
- Use Docker secrets (Swarm) or environment variable injection
- Rotate ChatKit/AgentKit/Supabase credentials quarterly
- Set restrictive file permissions on `.env` files (600)
- Use secret management systems (Vault, AWS Secrets Manager) for production

**Network Security:**
- Segment vTOC services into isolated network (Docker network, VPC)
- Use VLANs for sensor networks (separate from management)
- Enable encryption for database connections (Supabase provides TLS)
- Configure Traefik middleware for rate limiting and IP filtering
- Set up monitoring and alerting for suspicious traffic

**Application Security:**
- Enable HTTPS for all external communications (see [Ingress](#ingress))
- Configure Supabase RLS (Row Level Security) policies
- Validate and sanitize all API inputs
- Set secure session cookies (httpOnly, secure, sameSite)
- Review ChatKit webhook signature validation

**Access Control:**
- Implement least privilege for database users
- Use separate Supabase keys for frontend (anon) and backend (service role)
- Configure station role-based access control
- Enable audit logging for sensitive operations
- Regular access reviews and permission cleanup

**Monitoring:**
- Set up log aggregation (Loki, ELK stack)
- Configure alerts for failed login attempts
- Monitor resource usage and set thresholds
- Track API error rates and response times
- Review ChatKit/AgentKit webhook failures

## Network Topologies

vTOC supports multiple network configurations for resilience and connectivity:

**Single WAN Connection:**
- Basic deployment with single internet uplink
- Suitable for lab/development environments
- Configure default route through primary gateway
- Monitor uplink health with periodic health checks

**Dual WAN Failover:**
- Primary WAN (fiber/cable) + secondary WAN (LTE/Starlink)
- Automatic failover on primary link failure
- Implementation options:
  - **Router-based:** Use router with WAN failover (pfSense, OPNsense)
  - **Linux-based:** Use `mwan3` or custom routing scripts
  - **Container-based:** HAProxy or Traefik with health checks

**Example Failover Configuration (Linux):**
```bash
# Primary interface (eth0) and backup (wwan0)
ip route add default via 192.168.1.1 dev eth0 metric 100
ip route add default via 10.0.0.1 dev wwan0 metric 200

# Monitor primary gateway
while true; do
  if ! ping -c 1 -W 2 8.8.8.8 -I eth0 > /dev/null 2>&1; then
    ip route change default via 10.0.0.1 dev wwan0 metric 100
  fi
  sleep 10
done
```

**VPN Overlay Networks:**
- Use ZeroTier, Tailscale, or WireGuard for mesh connectivity
- Enables station-to-station communication over public internet
- Simplifies multi-site deployments without static IPs
- Configure in `scripts/inputs.schema.json` under `services`

**VLAN Segmentation:**
- Separate management, telemetry sensors, and public traffic
- Example VLANs:
  - VLAN 10: Management (SSH, web UI)
  - VLAN 20: Telemetry sensors (ADS-B, AIS)
  - VLAN 30: Public/guest network
- Configure on managed switch (see [Netgear GS105E](HARDWARE/NETGEAR-GS105E.md))
- Tag compute node ports for multi-VLAN access

**Load Balancing:**
- Deploy multiple backend replicas in Docker Swarm
- Use Traefik for HTTP load balancing
- Configure health checks for automatic failover
- Database load handled by Supabase (managed service)

**Mesh Networking:**
- LoRa/WiFi HaLow mesh for field operations
- See [Mesh Planning Overview](MESH_PLANNING/OVERVIEW.md)
- Integrate mesh nodes with vTOC telemetry APIs
- Gateway nodes connect mesh to internet uplink

**Example Multi-Site Topology:**
```
Internet
   |
   +-- [Firewall/Router] -- [Primary WAN: Fiber]
   |                      \-- [Secondary WAN: LTE]
   |
   +-- [Traefik Load Balancer]
   |      |
   |      +-- [Backend Pod 1] -- [Supabase Postgres]
   |      +-- [Backend Pod 2] -- [Supabase Postgres]
   |
   +-- [Frontend nginx]
   |
   +-- [VPN Gateway] -- [Remote Station 1]
                     \-- [Remote Station 2]
```

## ChatKit configuration steps

1. Create or select a ChatKit organization and generate an API key with webhook permissions.
2. Configure a webhook endpoint pointing at your backend’s `/api/v1/chatkit/webhook` URL. Set the signature secret to match
   `CHATKIT_WEBHOOK_SECRET` (optional if using defaults).
3. Create channels for each station role. The setup script can automate this when `chatkit.autoProvision` is enabled in the
   config JSON.
4. Invite operator accounts and the AgentKit service user to each channel.
5. In AgentKit, register client credentials and map playbooks to the same station roles used in ChatKit. Update
   `agents/config/agentkit.yml` accordingly.

For visibility into what is currently running in production, use the GitHub Discussion **Deployment Strategy: live branch**. Copy the [live branch operations guide](communications/live-branch.md) into the discussion to seed it if it does not exist, and post deployment or rollback updates there so operators can subscribe to changes.

## Sample configuration inputs

Example `inputs.json` enabling Traefik, specifying station roles, and seeding ChatKit automation:

```json
{
  "projectName": "vtoc",
  "stationRoles": ["ops", "intel", "logistics"],
  "chatkit": {
    "autoProvision": true,
    "orgId": "${CHATKIT_ORG_ID}",
    "webhookSecret": "${CHATKIT_WEBHOOK_SECRET}"
  },
  "agentkit": {
    "clientId": "${AGENTKIT_CLIENT_ID}",
    "clientSecret": "${AGENTKIT_CLIENT_SECRET}"
  },
  "services": {
    "traefik": true,
    "postgres": true,
    "n8n": false,
    "wazuh": false
  }
}
```

Pass this file to `python -m scripts.bootstrap_cli setup container --config inputs.json --apply` (or `make setup-container -- --config inputs.json`) or inline with `--config-json`.

## Additional resources

- [`docs/QUICKSTART.md`](QUICKSTART.md) — station bootstrap instructions.
- [`docs/CHANGELOG.md`](CHANGELOG.md) — migration notes for existing operators.
- [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) — architecture overview.
