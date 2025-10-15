#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_JSON="${VTOC_CONFIG_JSON:-{}}"
APPLY="${VTOC_SETUP_APPLY:-false}"
CONFIGURE="${VTOC_SETUP_CONFIGURE:-false}"

export ROOT_DIR CONFIG_JSON

python - <<'PY'
import json
from pathlib import Path
import os

root_dir = Path(os.environ['ROOT_DIR'])
config_json = os.environ.get('CONFIG_JSON', '{}')
config = json.loads(config_json)
cloud = config.get('cloud', {})
provider = cloud.get('provider', 'aws')
region = cloud.get('region', 'us-east-1')
project = config.get('projectName', 'vtoc')

terraform_dir = root_dir / 'infra' / 'terraform'
ansible_dir = root_dir / 'infra' / 'ansible'
terraform_dir.mkdir(parents=True, exist_ok=True)
ansible_dir.mkdir(parents=True, exist_ok=True)

main_tf = """terraform {{
  required_version = ">= 1.5.0"
  required_providers {{
    {provider} = {{ source = "hashicorp/{provider}" }}
  }}
}}

provider "{provider}" {{
  region = "{region}"
}}

resource "{provider}_instance" "vtoc" {{
  ami           = var.ami
  instance_type = var.instance_type
  tags = {{
    Name = "{project}-backend"
  }}
}}
""".format(provider=provider, region=region, project=project)
(terraform_dir / 'main.tf').write_text(main_tf)

variables_tf = """variable "ami" {
  description = "Base AMI ID"
  type        = string
}

variable "instance_type" {
  description = "Compute instance type"
  type        = string
  default     = "t3.micro"
}
"""
(terraform_dir / 'variables.tf').write_text(variables_tf)

outputs_tf = """output "backend_ip" {
  value = {provider}_instance.vtoc.public_ip
}
""".format(provider=provider)
(terraform_dir / 'outputs.tf').write_text(outputs_tf)

inventory = """[vtoc]
backend ansible_host=1.2.3.4
"""
(ansible_dir / 'inventory.ini').write_text(inventory)

playbook = """---
- name: Configure vTOC backend host
  hosts: vtoc
  become: true
  vars:
    docker_image: {{ docker_image | default('ghcr.io/pr-cybr/vtoc/backend:latest') }}
  tasks:
    - name: Ensure Docker is installed
      ansible.builtin.package:
        name: docker.io
        state: present

    - name: Run backend container
      community.docker.docker_container:
        name: vtoc-backend
        image: "{{ docker_image }}"
        restart_policy: unless-stopped
        env:
          DATABASE_URL: {{ database_url | default('postgresql+psycopg2://vtoc:vtocpass@database:5432/vtoc') }}
        published_ports:
          - "8080:8080"
"""
(ansible_dir / 'playbook.yml').write_text(playbook)
PY

if [[ "$APPLY" == "true" ]]; then
  (cd "$ROOT_DIR/infra/terraform" && terraform init && terraform apply -auto-approve)
fi

if [[ "$CONFIGURE" == "true" ]]; then
  (cd "$ROOT_DIR/infra/ansible" && ansible-playbook -i inventory.ini playbook.yml)
fi

printf 'Cloud scaffolding generated in infra/.\n'
