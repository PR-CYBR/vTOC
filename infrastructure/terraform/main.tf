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

resource "docker_volume" "station_toc_s1" {
  name = var.volumes["station_toc_s1"]
}

resource "docker_volume" "station_toc_s2" {
  name = var.volumes["station_toc_s2"]
}

resource "docker_volume" "station_toc_s3" {
  name = var.volumes["station_toc_s3"]
}

resource "docker_volume" "station_toc_s4" {
  name = var.volumes["station_toc_s4"]
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

output "station_volume_names" {
  value = {
    toc_s1 = docker_volume.station_toc_s1.name
    toc_s2 = docker_volume.station_toc_s2.name
    toc_s3 = docker_volume.station_toc_s3.name
    toc_s4 = docker_volume.station_toc_s4.name
  }
  description = "Station-specific PostgreSQL volumes"
}
