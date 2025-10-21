locals {
  postgres = {
    database      = var.postgres_database
    user          = var.postgres_user
    password      = var.postgres_password
    host          = var.postgres_host
    internal_host = var.postgres_internal_host
    port          = var.postgres_port
  }

  backend_base_database_url_internal = format(
    "postgresql+psycopg2://%s:%s@%s:%d/%s",
    var.postgres_user,
    var.postgres_password,
    var.postgres_internal_host,
    var.postgres_port,
    var.postgres_database,
  )

  backend_base_database_url_public = format(
    "postgresql+psycopg2://%s:%s@%s:%d/%s",
    var.postgres_user,
    var.postgres_password,
    var.postgres_host,
    var.postgres_port,
    var.postgres_database,
  )

  backend_database_env_internal = merge(
    {
      DATABASE_URL = local.backend_base_database_url_internal
    },
    {
      for alias, schema in var.postgres_search_paths : upper(alias)
      => format(
        "%s?options=-csearch_path%%3D%s",
        local.backend_base_database_url_internal,
        schema,
      )
    }
  )

  backend_database_env_public = merge(
    {
      DATABASE_URL = local.backend_base_database_url_public
    },
    {
      for alias, schema in var.postgres_search_paths : upper(alias)
      => format(
        "%s?options=-csearch_path%%3D%s",
        local.backend_base_database_url_public,
        schema,
      )
    }
  )

  backend_database_env = {
    for key, value in local.backend_database_env_internal :
    key == "DATABASE_URL" ? key : format("DATABASE_URL_%s", key) => value
  }

  backend_database_env_public_labeled = {
    for key, value in local.backend_database_env_public :
    key == "DATABASE_URL" ? key : format("DATABASE_URL_%s", key) => value
  }

  backend_env = merge(
    local.backend_database_env,
    {
      AGENTKIT_API_BASE_URL   = var.agentkit_api_base_url
      AGENTKIT_API_KEY        = var.agentkit_api_key
      AGENTKIT_ORG_ID         = var.agentkit_org_id
      AGENTKIT_TIMEOUT_SECONDS = tostring(var.agentkit_timeout_seconds)
      MISSION_TIMELINE_LIMIT  = tostring(var.timeline_event_limit)
      CHATKIT_WEBHOOK_SECRET  = var.chatkit_webhook_secret
      CHATKIT_ALLOWED_TOOLS   = join(",", var.chatkit_allowed_tools)
      CHATKIT_API_KEY         = var.chatkit_api_key
      CHATKIT_ORG_ID          = var.chatkit_org_id
      SUPABASE_URL            = local.supabase.api_url
      SUPABASE_PROJECT_REF    = local.supabase.project_ref
      SUPABASE_SERVICE_ROLE_KEY = local.supabase.service_role_key
      SUPABASE_JWT_SECRET     = local.supabase.jwt_secret
    }
  )

  scraper_env = {
    BACKEND_BASE_URL = var.backend_internal_base_url
  }

  frontend_env = merge(
    {
      VITE_PORT                           = tostring(var.frontend_port)
      VITE_API_BASE_URL                   = var.backend_public_base_url
      VITE_MAP_TILES_URL                  = var.frontend_map_tiles_url
      VITE_MAP_ATTRIBUTION                = var.frontend_map_attribution
      VITE_DEFAULT_DIV                    = var.frontend_default_div
      VITE_RSS_ENABLED                    = tostring(var.frontend_rss_enabled)
      VITE_CHAT_ENABLED                   = tostring(var.frontend_chat_enabled)
      VITE_CHATKIT_WIDGET_URL             = var.chatkit_widget_url
      VITE_CHATKIT_API_KEY                = var.chatkit_api_key
      VITE_CHATKIT_TELEMETRY_CHANNEL      = var.chatkit_telemetry_channel
      VITE_AGENTKIT_ORG_ID                = var.agentkit_org_id
      VITE_AGENTKIT_DEFAULT_STATION_CONTEXT = var.agentkit_default_station_context
      VITE_AGENTKIT_API_BASE_PATH         = var.agentkit_api_base_path
      VITE_SUPABASE_URL                   = local.supabase.api_url
      VITE_SUPABASE_ANON_KEY              = local.supabase.anon_key
    },
    var.additional_frontend_env,
  )

  ingest_env = {
    GPS_SERIAL_DEVICE     = var.gps_serial_device
    GPS_BAUD_RATE         = tostring(var.gps_baud_rate)
    GPS_SOURCE_SLUG       = var.gps_source_slug
    ADSB_FEED_URL         = var.adsb_feed_url
    ADSB_SOURCE_SLUG      = var.adsb_source_slug
    RTLSDR_DEVICE_SERIAL  = var.rtlsdr_device_serial
    H4M_SERIAL_DEVICE     = var.h4m_serial_device
    H4M_BAUD_RATE         = tostring(var.h4m_baud_rate)
    H4M_CHANNEL           = var.h4m_channel
    H4M_SOURCE_SLUG       = var.h4m_source_slug
  }

  fly_secret_map = merge(
    local.backend_env,
    local.backend_database_env_public_labeled,
    {
      SUPABASE_ANON_KEY = local.supabase.anon_key
    },
    local.ingest_env,
    var.additional_fly_secrets,
  )

  fly_runtime_credentials = {
    app_name       = var.fly_app_name
    api_token      = var.fly_api_token
    ghcr_username  = var.ghcr_deploy_username
    ghcr_token     = var.ghcr_deploy_token
    backend_image  = var.backend_image_repository
    frontend_image = var.frontend_image_repository
    scraper_image  = var.scraper_image_repository
  }

  optional_integrations = {
    zerotier_network_id = var.zerotier_network_id
    tailscale_auth_key  = var.tailscale_auth_key
  }
}
