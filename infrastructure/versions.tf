terraform {
  required_version = ">= 1.5.0"

  required_providers {
    fly = {
      source  = "dov.dev/fly/fly-provider"
      version = "~> 0.0.24"
    }
  }

  cloud {
    organization = "pr-cybr"
    workspaces {
      name = "vtoc-live"
    }
  }
}
