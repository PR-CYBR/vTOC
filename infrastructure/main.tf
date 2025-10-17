locals {
  supabase = {
    project_ref      = var.supabase_project_ref
    api_url          = var.supabase_api_url
    anon_key         = var.supabase_anon_key
    service_role_key = var.supabase_service_role_key
    jwt_secret       = var.supabase_jwt_secret
  }

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
      for alias, schema in var.postgres_search_paths : upper(alias) => format(
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
      for alias, schema in var.postgres_search_paths : upper(alias) => format(
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
      AGENTKIT_API_BASE_URL    = var.agentkit_api_base_url
      AGENTKIT_API_KEY         = var.agentkit_api_key
      AGENTKIT_ORG_ID          = var.agentkit_org_id
      AGENTKIT_TIMEOUT_SECONDS = tostring(var.agentkit_timeout_seconds)
      CHATKIT_WEBHOOK_SECRET   = var.chatkit_webhook_secret
      CHATKIT_ALLOWED_TOOLS    = join(",", var.chatkit_allowed_tools)
      CHATKIT_API_KEY          = var.chatkit_api_key
      CHATKIT_ORG_ID           = var.chatkit_org_id
      SUPABASE_URL             = local.supabase.api_url
      SUPABASE_PROJECT_REF     = local.supabase.project_ref
      SUPABASE_SERVICE_ROLE_KEY = local.supabase.service_role_key
      SUPABASE_JWT_SECRET      = local.supabase.jwt_secret
    }
  )

  scraper_env = {
    BACKEND_BASE_URL = var.backend_internal_base_url
  }

  frontend_env = merge(
    {
      VITE_PORT                            = tostring(var.frontend_port)
      VITE_API_BASE_URL                    = var.backend_public_base_url
      VITE_MAP_TILES_URL                   = var.frontend_map_tiles_url
      VITE_MAP_ATTRIBUTION                 = var.frontend_map_attribution
      VITE_DEFAULT_DIV                     = var.frontend_default_div
      VITE_RSS_ENABLED                     = tostring(var.frontend_rss_enabled)
      VITE_CHAT_ENABLED                    = tostring(var.frontend_chat_enabled)
      VITE_CHATKIT_WIDGET_URL              = var.chatkit_widget_url
      VITE_CHATKIT_API_KEY                 = var.chatkit_api_key
      VITE_CHATKIT_TELEMETRY_CHANNEL       = var.chatkit_telemetry_channel
      VITE_AGENTKIT_ORG_ID                 = var.agentkit_org_id
      VITE_AGENTKIT_DEFAULT_STATION_CONTEXT = var.agentkit_default_station_context
      VITE_AGENTKIT_API_BASE_PATH          = var.agentkit_api_base_path
      VITE_SUPABASE_URL                    = local.supabase.api_url
      VITE_SUPABASE_ANON_KEY               = local.supabase.anon_key
    },
    var.additional_frontend_env,
  )

  fly_secret_map = merge(
    local.backend_env,
    local.backend_database_env_public_labeled,
    {
      SUPABASE_ANON_KEY = local.supabase.anon_key
    },
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

locals {
  fly_machine_region = var.fly_machine_region != "" ? var.fly_machine_region : var.fly_primary_region
  fly_machine_name   = var.fly_machine_name != "" ? var.fly_machine_name : format("%s-primary", var.fly_app_name)
  fly_machine_image  = var.fly_machine_image != "" ? var.fly_machine_image : format("%s:latest", var.backend_image_repository)
  fly_machine_port   = length(var.fly_machine_services) > 0 ? tostring(var.fly_machine_services[0].internal_port) : "8080"
  fly_machine_env    = merge({ PORT = local.fly_machine_port }, var.fly_machine_env)
  fly_machine_services = [
    for service in var.fly_machine_services : {
      protocol      = service.protocol
      internal_port = service.internal_port
      ports = [
        for port in service.ports : {
          port     = port.port
          handlers = port.handlers
        }
      ]
    }
  ]
  fly_machine_mounts = [
    for mount in var.fly_machine_mounts : merge(
      {
        path   = mount.path
        volume = mount.volume
      },
      try({ encrypted = mount.encrypted }, {}),
      try({ size_gb = mount.size_gb }, {}),
    )
  ]
}

resource "fly_app" "vtoc" {
  name = var.fly_app_name
  org  = var.fly_org_slug
}

resource "fly_app_secret" "vtoc" {
  app     = fly_app.vtoc.id
  secrets = local.fly_secret_map
}

resource "fly_machine" "vtoc_backend" {
  app    = fly_app.vtoc.id
  region = local.fly_machine_region
  name   = local.fly_machine_name
  image  = local.fly_machine_image
  env    = local.fly_machine_env
  services = local.fly_machine_services
  mounts   = local.fly_machine_mounts

  depends_on = [fly_app_secret.vtoc]
}
