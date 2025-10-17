# Terraform Cloud workspace reference

## Workspace settings
- Configure a Terraform Cloud workspace that tracks the `infrastructure/terraform` directory in this repository.
- Set the Terraform version to `>= 1.5.0` to match the module constraint in `main.tf`.
- Keep remote state in Terraform Cloud; do not create or commit local state artefacts.
- Trigger plans from VCS pushes and require manual approval for applies when rotating credentials.

## Variable catalogue
The following variables are defined by `variables.tf`. Create them in the workspace and mark any value flagged as **sensitive** accordingly.

### Postgres configuration
- `postgres_database` – Name of the primary Postgres database.
- `postgres_user` – Database user for application services.
- `postgres_password` (**sensitive**) – Password for `postgres_user`.
- `postgres_host` – Public hostname for the database.
- `postgres_internal_host` – Internal hostname for in-cluster access (default `database`).
- `postgres_port` – Postgres port (default `5432`).
- `postgres_search_paths` – Map of station identifiers to schema names (defaults to `toc_s1`…`toc_s4`).

### Backend and scraper connectivity
- `backend_internal_base_url` – Internal URL other services use (default `http://backend:8080`).
- `backend_public_base_url` – Public API base URL exposed to clients.

### Frontend presentation
- `frontend_port` – Vite dev-server port (default `5173`).
- `frontend_map_tiles_url` – Tile server template URL.
- `frontend_map_attribution` – Attribution string for rendered tiles.
- `frontend_default_div` – Default DIV/station identifier.
- `frontend_rss_enabled` – Enables RSS widgets (default `true`).
- `frontend_chat_enabled` – Enables chat widgets (default `true`).

### ChatKit and AgentKit
- `chatkit_widget_url` – Script URL for the ChatKit widget.
- `chatkit_api_key` – Publishable ChatKit key for the frontend.
- `chatkit_telemetry_channel` – Default telemetry channel name.
- `chatkit_org_id` – ChatKit organization identifier shared with backend.
- `chatkit_webhook_secret` (**sensitive**) – Signing secret for ChatKit callbacks.
- `chatkit_allowed_tools` – List of enabled ChatKit tool identifiers.
- `agentkit_api_base_url` – Base URL for backend AgentKit calls.
- `agentkit_api_key` (**sensitive**) – Backend AgentKit API key.
- `agentkit_org_id` – AgentKit organization identifier.
- `agentkit_timeout_seconds` – Timeout (seconds) for AgentKit HTTP requests (default `30`).
- `agentkit_default_station_context` – Default station context forwarded from the frontend.
- `agentkit_api_base_path` – Relative API path used by the frontend AgentKit client.

### Supabase
- `supabase_project_ref` – Supabase project reference slug.
- `supabase_api_url` – Supabase REST API base URL.
- `supabase_anon_key` (**sensitive**) – Frontend anon key.
- `supabase_service_role_key` (**sensitive**) – Backend service-role key.
- `supabase_jwt_secret` (**sensitive**) – JWT signing secret for hooks.

### Fly/GHCR deployment
- `fly_app_name` – Target Fly.io application name.
- `fly_api_token` (**sensitive**) – Fly.io API token for deployments.
- `ghcr_deploy_username` – Username for pulling GHCR images.
- `ghcr_deploy_token` (**sensitive**) – PAT/token for GHCR pulls.
- `backend_image_repository` – Backend image repository (default `ghcr.io/pr-cybr/vtoc/backend`).
- `frontend_image_repository` – Frontend image repository (default `ghcr.io/pr-cybr/vtoc/frontend`).
- `scraper_image_repository` – Scraper image repository (default `ghcr.io/pr-cybr/vtoc/scraper`).

### Optional integrations
- `zerotier_network_id` – Optional ZeroTier network ID.
- `tailscale_auth_key` (**sensitive**) – Optional Tailscale auth key.
- `additional_fly_secrets` – Extra Fly secrets to merge into the deployment map.
- `additional_frontend_env` – Additional frontend environment key/value pairs.

## Sensitive `secrets` map
Terraform assembles a sensitive `fly_secret_map` from workspace variables. Populate and rotate the upstream values so the map renders the following keys for `flyctl secrets import`:

- `DATABASE_URL` and any `DATABASE_URL_<ALIAS>` values derived from `postgres_*` and `postgres_search_paths`.
- `AGENTKIT_API_BASE_URL`, `AGENTKIT_API_KEY`, `AGENTKIT_ORG_ID`, `AGENTKIT_TIMEOUT_SECONDS`.
- `CHATKIT_WEBHOOK_SECRET`, `CHATKIT_ALLOWED_TOOLS`, `CHATKIT_API_KEY`, `CHATKIT_ORG_ID`.
- `SUPABASE_URL`, `SUPABASE_PROJECT_REF`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, plus `SUPABASE_ANON_KEY` for Fly runtime parity.
- Any entries merged from `additional_fly_secrets`.

Regenerate the map with `terraform output -raw fly_secrets_env` after each update and feed it directly to Fly.

## Keeping secrets out of git
- Store every credential as a Terraform Cloud workspace variable; never commit populated `terraform.tfvars` files.
- Leave `terraform.tfstate` and `terraform.tfvars` in `.gitignore` so state and secrets never land in version control.
- Use `terraform output` to materialize `.env` files or Fly payloads instead of copying values into the repository.
- Rotate credentials by updating the workspace, applying the run in Terraform Cloud, and rerunning the setup scripts (`scripts/setup_local.sh`, `scripts/setup_container.sh`, `scripts/fly_deploy.sh`) to refresh generated artefacts.
