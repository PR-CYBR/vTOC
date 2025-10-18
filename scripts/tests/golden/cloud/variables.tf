variable "ami" {
  description = "Base AMI ID"
  type        = string
}

variable "instance_type" {
  description = "Compute instance type"
  type        = string
  default     = "t3.micro"
}
