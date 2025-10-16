locals {
  frontend_env_lines = [
    for key in sort(keys(local.frontend_env)) :
    format("%s=%s", key, local.frontend_env[key])
  ]

  fly_secret_lines = [
    for key in sort(keys(local.fly_secret_map)) :
    format("%s=%s", key, local.fly_secret_map[key])
  ]
}

output "config_bundle" {
  description = "Structured secrets and configuration pulled from Terraform Cloud."
  value = {
    postgres = local.postgres
    backend = {
      env                   = local.backend_env
      env_public            = merge(local.backend_env, local.backend_database_env_public_labeled)
      internal_database_env = local.backend_database_env
    }
    scraper = {
      env = local.scraper_env
    }
    frontend = {
      env = local.frontend_env
    }
    fly = {
      runtime      = local.fly_runtime_credentials
      secrets_env  = local.fly_secret_map
    }
    supabase = local.supabase
    optional_integrations = local.optional_integrations
  }
  sensitive = true
}

output "frontend_env_file" {
  description = "Rendered contents for frontend .env files."
  value       = join("\n", concat(local.frontend_env_lines, [""]))
  sensitive   = true
}

output "fly_secrets_env" {
  description = "Rendered secrets payload compatible with `flyctl secrets import`."
  value       = join("\n", concat(local.fly_secret_lines, [""]))
  sensitive   = true
}

output "fly_runtime_credentials" {
  description = "Credentials required by deployment scripts (not stored as Fly secrets)."
  value       = local.fly_runtime_credentials
  sensitive   = true
}
