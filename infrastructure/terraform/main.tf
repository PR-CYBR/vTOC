terraform {
  required_version = ">= 1.0"
  
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {
  host = "unix:///var/run/docker.sock"
}

# Docker network
resource "docker_network" "vtoc_network" {
  name = "vtoc-network"
}

# PostgreSQL volume
resource "docker_volume" "postgres_data" {
  name = "vtoc_postgres_data"
}

# n8n volume
resource "docker_volume" "n8n_data" {
  name = "vtoc_n8n_data"
}

# Outputs
output "network_id" {
  value       = docker_network.vtoc_network.id
  description = "The ID of the Docker network"
}

output "postgres_volume_name" {
  value       = docker_volume.postgres_data.name
  description = "The name of the PostgreSQL volume"
}
