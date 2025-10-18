terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = { source = "hashicorp/aws" }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_instance" "vtoc" {
  ami           = var.ami
  instance_type = var.instance_type
  tags = {
    Name = "vtoc-backend"
  }
}}
