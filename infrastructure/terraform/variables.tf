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
    station_toc_s1 = "vtoc_station_toc_s1"
    station_toc_s2 = "vtoc_station_toc_s2"
    station_toc_s3 = "vtoc_station_toc_s3"
    station_toc_s4 = "vtoc_station_toc_s4"
  }
}
