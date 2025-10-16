locals {
  supabase = {
    project_ref        = var.supabase_project_ref
    api_url            = var.supabase_api_url
    anon_key           = var.supabase_anon_key
    service_role_key   = var.supabase_service_role_key
    jwt_secret         = var.supabase_jwt_secret
  }
}
