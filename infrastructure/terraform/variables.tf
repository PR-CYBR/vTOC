variable "docker_host" {
  description = "Docker host address"
  type        = string
  default     = "unix:///var/run/docker.sock"
}

variable "network_name" {
  description = "Name of the Docker network"
  type        = string
  default     = "vtoc-network"
}

variable "volumes" {
  description = "Docker volumes configuration"
  type        = map(string)
  default = {
    postgres = "vtoc_postgres_data"
    n8n      = "vtoc_n8n_data"
  }
}
