variable "postgres_database" {
  description = "Name of the primary Postgres database."
  type        = string
}

variable "postgres_user" {
  description = "Application database user."
  type        = string
}

variable "postgres_password" {
  description = "Password for the application database user."
  type        = string
  sensitive   = true
}

variable "postgres_host" {
  description = "Publicly reachable hostname for the primary Postgres instance."
  type        = string
}

variable "postgres_internal_host" {
  description = "Hostname used by in-cluster services to reach Postgres."
  type        = string
  default     = "database"
}

variable "postgres_port" {
  description = "Postgres port."
  type        = number
  default     = 5432
}

variable "postgres_search_paths" {
  description = "Mapping of logical station identifiers to Postgres schemas."
  type        = map(string)
  default = {
    toc_s1 = "toc_s1"
    toc_s2 = "toc_s2"
    toc_s3 = "toc_s3"
    toc_s4 = "toc_s4"
  }
}

variable "backend_internal_base_url" {
  description = "Internal URL for the backend that other services (scraper, etc.) should target."
  type        = string
  default     = "http://backend:8080"
}

variable "backend_public_base_url" {
  description = "Public URL that clients should use to reach the backend API."
  type        = string
}

variable "timeline_event_limit" {
  description = "Maximum number of timeline events the backend returns per mission."
  type        = number
  default     = 100
}

variable "frontend_port" {
  description = "Port used by the Vite dev server."
  type        = number
  default     = 5173
}

variable "frontend_map_tiles_url" {
  description = "Tile server URL template."
  type        = string
  default     = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
}

variable "frontend_map_attribution" {
  description = "HTML attribution string for map tiles."
  type        = string
  default     = "© OpenStreetMap contributors"
}

variable "frontend_default_div" {
  description = "Default DIV/station identifier displayed in the UI."
  type        = string
  default     = "PR-SJU"
}

variable "frontend_rss_enabled" {
  description = "Toggle RSS widgets in the UI."
  type        = bool
  default     = true
}

variable "frontend_chat_enabled" {
  description = "Toggle chat widgets in the UI."
  type        = bool
  default     = true
}

variable "chatkit_widget_url" {
  description = "URL for loading the ChatKit web widget."
  type        = string
  default     = "https://cdn.chatkit.example.com/widget.js"
}

variable "chatkit_api_key" {
  description = "ChatKit publishable key exposed to the frontend."
  type        = string
}

variable "chatkit_telemetry_channel" {
  description = "Default telemetry channel for ChatKit analytics."
  type        = string
  default     = "vtoc-intel"
}

variable "chatkit_org_id" {
  description = "ChatKit organization identifier shared with the backend."
  type        = string
}

variable "chatkit_webhook_secret" {
  description = "Webhook signing secret for ChatKit callbacks."
  type        = string
  sensitive   = true
}

variable "chatkit_allowed_tools" {
  description = "Comma separated list of tool identifiers ChatKit may invoke."
  type        = list(string)
  default     = []
}

variable "agentkit_api_base_url" {
  description = "Base URL for AgentKit API calls."
  type        = string
  default     = "https://agentkit.example.com/api"
}

variable "agentkit_api_key" {
  description = "API key used when the backend talks to AgentKit."
  type        = string
  sensitive   = true
}

variable "agentkit_org_id" {
  description = "Organization identifier for AgentKit usage."
  type        = string
}

variable "agentkit_timeout_seconds" {
  description = "Timeout for AgentKit API calls."
  type        = number
  default     = 30
}

variable "agentkit_default_station_context" {
  description = "Default station context forwarded to AgentKit from the frontend."
  type        = string
  default     = "PR-SJU"
}

variable "agentkit_api_base_path" {
  description = "Relative API path for frontend AgentKit requests."
  type        = string
  default     = "/api/v1/agent-actions"
}

variable "supabase_project_ref" {
  description = "Supabase project reference identifier."
  type        = string
}

variable "supabase_api_url" {
  description = "Base URL for the Supabase REST API."
  type        = string
}

variable "supabase_anon_key" {
  description = "Anon/public Supabase key exposed to the frontend."
  type        = string
  sensitive   = true
}

variable "supabase_service_role_key" {
  description = "Supabase service role key for privileged backend calls."
  type        = string
  sensitive   = true
}

variable "supabase_jwt_secret" {
  description = "JWT secret used for Supabase auth hooks."
  type        = string
  sensitive   = true
}

variable "fly_app_name" {
  description = "Name of the Fly.io application."
  type        = string
}

variable "fly_api_token" {
  description = "Fly.io API token used for deployments."
  type        = string
  sensitive   = true
}

variable "ghcr_deploy_username" {
  description = "Username used when authenticating the Fly remote builder to GHCR."
  type        = string
}

variable "ghcr_deploy_token" {
  description = "Personal access token or PAT for pulling images from GHCR."
  type        = string
  sensitive   = true
}

variable "backend_image_repository" {
  description = "Fully qualified image repository for backend deployments."
  type        = string
  default     = "ghcr.io/pr-cybr/vtoc/backend"
}

variable "frontend_image_repository" {
  description = "Fully qualified image repository for frontend deployments."
  type        = string
  default     = "ghcr.io/pr-cybr/vtoc/frontend"
}

variable "scraper_image_repository" {
  description = "Fully qualified image repository for scraper deployments."
  type        = string
  default     = "ghcr.io/pr-cybr/vtoc/scraper"
}

variable "zerotier_network_id" {
  description = "Optional ZeroTier network identifier for edge connectivity."
  type        = string
  default     = ""
}

variable "tailscale_auth_key" {
  description = "Optional Tailscale auth key for overlay network agents."
  type        = string
  sensitive   = true
  default     = ""
}

variable "additional_fly_secrets" {
  description = "Arbitrary extra Fly secrets to merge into the deployment map."
  type        = map(string)
  default     = {}
}

variable "additional_frontend_env" {
  description = "Extra frontend environment variables to include when generating .env files."
  type        = map(string)
  default     = {}
}

variable "gps_serial_device" {
  description = "Serial device path presented to the GPS ingest container."
  type        = string
  default     = "/dev/ttyUSB0"
}

variable "gps_baud_rate" {
  description = "Baud rate used when reading from the GPS serial device."
  type        = number
  default     = 9600
}

variable "gps_source_slug" {
  description = "Telemetry source slug recorded by the GPS ingest service."
  type        = string
  default     = "station-gps"
}

variable "adsb_feed_url" {
  description = "URL for ADS-B JSON feeds (e.g., dump1090)."
  type        = string
  default     = "http://dump1090:8080/data/aircraft.json"
}

variable "adsb_source_slug" {
  description = "Telemetry source slug recorded by the ADS-B ingest service."
  type        = string
  default     = "station-adsb"
}

variable "rtlsdr_device_serial" {
  description = "Optional RTL-SDR device serial to pin within the ADS-B ingest container."
  type        = string
  default     = ""
}

variable "h4m_serial_device" {
  description = "Serial device path presented to the H4M bridge container."
  type        = string
  default     = "/dev/ttyUSB1"
}

variable "h4m_baud_rate" {
  description = "Baud rate used by the H4M bridge serial interface."
  type        = number
  default     = 115200
}

variable "h4m_channel" {
  description = "Channel identifier for the H4M bridge to register with the backend."
  type        = string
  default     = "station-h4m"
}

variable "h4m_source_slug" {
  description = "Telemetry source slug recorded by the H4M bridge service."
  type        = string
  default     = "station-h4m"
}
