# Secret management and Terraform Cloud workflow

This repository stores all runtime credentials and public configuration in the
`infrastructure/terraform` workspace. The Terraform Cloud workspace variables
listed below are the single source of truth for every environment that consumes
secrets (`docker-compose.yml`, `docker-stack.yml`, Fly deployments, GitHub
workflows, the setup scripts, and the frontend `.env` files).

## Workspace variable catalogue

| Context | Runtime variable(s) | Terraform variable | Notes |
| --- | --- | --- | --- |
| Database containers | `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | `postgres_database`, `postgres_user`, `postgres_password` | Used by Docker Postgres and rendered into backend connection strings. |
| Backend connection strings | `DATABASE_URL`, `DATABASE_URL_TOC_*` | Derived from `postgres_*` variables and `postgres_search_paths` | Generated for both in-cluster and public connectivity. |
| Scraper | `BACKEND_BASE_URL` | `backend_internal_base_url` | Drives the scraper's service discovery. |
| Frontend (.env) | `VITE_PORT`, `VITE_API_BASE_URL`, `VITE_MAP_TILES_URL`, `VITE_MAP_ATTRIBUTION`, `VITE_DEFAULT_DIV`, `VITE_RSS_ENABLED`, `VITE_CHAT_ENABLED`, `VITE_CHATKIT_WIDGET_URL`, `VITE_CHATKIT_API_KEY`, `VITE_CHATKIT_TELEMETRY_CHANNEL`, `VITE_AGENTKIT_ORG_ID`, `VITE_AGENTKIT_DEFAULT_STATION_CONTEXT`, `VITE_AGENTKIT_API_BASE_PATH`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` | `frontend_port`, `backend_public_base_url`, `frontend_map_tiles_url`, `frontend_map_attribution`, `frontend_default_div`, `frontend_rss_enabled`, `frontend_chat_enabled`, `chatkit_widget_url`, `chatkit_api_key`, `chatkit_telemetry_channel`, `agentkit_org_id`, `agentkit_default_station_context`, `agentkit_api_base_path`, `supabase_api_url`, `supabase_anon_key` | Rendered into `.env.local` via `terraform output frontend_env_file`. |
| Backend services | `AGENTKIT_API_BASE_URL`, `AGENTKIT_API_KEY`, `AGENTKIT_ORG_ID`, `AGENTKIT_TIMEOUT_SECONDS`, `CHATKIT_WEBHOOK_SECRET`, `CHATKIT_ALLOWED_TOOLS`, `CHATKIT_API_KEY`, `CHATKIT_ORG_ID`, `SUPABASE_URL`, `SUPABASE_PROJECT_REF`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET` | `agentkit_api_base_url`, `agentkit_api_key`, `agentkit_org_id`, `agentkit_timeout_seconds`, `chatkit_webhook_secret`, `chatkit_allowed_tools`, `chatkit_api_key`, `chatkit_org_id`, `supabase_api_url`, `supabase_project_ref`, `supabase_service_role_key`, `supabase_jwt_secret` | Delivered to Docker, Fly secrets, and Ansible roles through the Terraform outputs. |
| Fly deployment secrets | `DATABASE_URL*`, `SUPABASE_*`, `CHATKIT_*`, `AGENTKIT_*` | Same inputs as backend/frontends | `terraform output -raw fly_secrets_env` yields the payload consumed by `flyctl secrets import`. |
| Fly API + GHCR auth | `FLY_API_TOKEN`, `FLY_APP_NAME`, `GHCR_USERNAME`, `GHCR_TOKEN`, image repositories | `fly_api_token`, `fly_app_name`, `ghcr_deploy_username`, `ghcr_deploy_token`, `backend_image_repository`, `frontend_image_repository`, `scraper_image_repository` | Parsed by `terraform output fly_runtime_credentials` and exported for deploy scripts. |
| GitHub Actions (container publishing) | `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` | GitHub repository secrets | Required for reusable container workflows so they can authenticate to Docker Hub, tag images under `<username>/*`, and push alongside GHCR. |
| Optional networking | `ZEROTIER_NETWORK_ID`, `TS_AUTHKEY` | `zerotier_network_id`, `tailscale_auth_key` | Included for optional Docker stack integrations. |
| Terraform Cloud API | `TF_TOKEN_app_terraform_io` (GitHub Actions secret) | N/A | Required so CI can run `terraform output` against the workspace. |

### Supabase keys

Supabase credentials are represented by the Terraform variables
`supabase_project_ref`, `supabase_api_url`, `supabase_anon_key`,
`supabase_service_role_key`, and `supabase_jwt_secret`. The frontend receives the
anon key and API URL, while the backend/Fly secrets include all four values (anon
key, service role key, project ref, and JWT secret).

## Consuming Terraform outputs

Terraform produces structured outputs that the scripts and pipelines consume:

* `terraform output -json config_bundle` — master map consumed by
  `scripts/setup_container.sh` and `scripts/setup_cloud.sh` for docker-compose
  generation and infrastructure scaffolding.
* `terraform output -raw frontend_env_file` — rendered `.env.local` content used
  by `scripts/setup_local.sh`.
* `terraform output -raw fly_secrets_env` — newline-delimited key/value pairs for
  `flyctl secrets import`, used by `scripts/fly_deploy.sh` and CI.
* `terraform output -json fly_runtime_credentials` — deployment credentials for
  Fly/GHCR, exported into the environment by `scripts/fly_deploy.sh` and the Fly
  GitHub workflow.

Every setup or deployment script invokes `terraform init` followed by the
relevant `terraform output` call. If outputs are unavailable, the scripts abort
with instructions to run `terraform apply` inside `infrastructure/terraform`
(first locally, then via Terraform Cloud) to hydrate state from workspace
variables.

### GitHub Actions configuration

Add the `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets to the repository
settings before triggering container publication workflows. The username should
match the Docker Hub namespace that will own the images; the token must have
`write:packages` access so the reusable jobs can log in, push tags, and satisfy
the `Publish Containers` and `Live Release PR Gate` checks.

## Secret rotation workflow

1. **Update the Terraform Cloud workspace.** Change the variable value in the
   `infrastructure/terraform` workspace (UI, CLI, or `terraform variables` API).
   Use the names listed in the table above.
2. **Re-apply the workspace.** Run `terraform apply` (locally or via Terraform
   Cloud) so the state reflects the updated variable values.
3. **Regenerate local artefacts.**
   * `scripts/setup_local.sh` regenerates `frontend/.env.local`.
   * `scripts/setup_container.sh` refreshes `docker-compose.generated.yml`.
   * `scripts/setup_cloud.sh` rewrites the Ansible inventory/playbook when
     required.
4. **Redeploy Fly.** Execute `scripts/fly_deploy.sh` (or trigger the
   `Fly Deploy` GitHub workflow). The script pulls fresh outputs, updates Fly
   secrets via `flyctl secrets import`, and deploys the backend image.
5. **Clean up old credentials.** After the new secret is verified, revoke or
   delete the rotated credential from its upstream provider.

This workflow keeps secrets out of git history while ensuring every runtime
surface (local Docker, Fly Machines, GitHub Actions, and the frontend) stays in
sync with Terraform Cloud.
