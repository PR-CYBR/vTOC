#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../lib/prereqs.sh
source "$SCRIPT_DIR/lib/prereqs.sh"

ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TERRAFORM_DIR="$ROOT_DIR/infrastructure/terraform"
CONFIG_JSON="${VTOC_CONFIG_JSON:-{}}"
APPLY="${VTOC_SETUP_APPLY:-false}"
CONFIGURE="${VTOC_SETUP_CONFIGURE:-false}"

requirements=(
  "python3|3.9.0|https://www.python.org/downloads/"
  "terraform|1.5.0|https://developer.hashicorp.com/terraform/downloads"
)

if [[ "$CONFIGURE" == "true" ]]; then
  requirements+=(
    "ansible-playbook|2.14.0|https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html"
  )
fi

check_prereqs "${requirements[@]}"

terraform -chdir="$TERRAFORM_DIR" init -input=false >/dev/null

export ROOT_DIR CONFIG_JSON TERRAFORM_DIR

python - <<'PY'
import json
import subprocess
from pathlib import Path
import os

root_dir = Path(os.environ['ROOT_DIR'])
terraform_dir = Path(os.environ['TERRAFORM_DIR'])
config_json = os.environ.get('CONFIG_JSON', '{}')
config = json.loads(config_json)
cloud = config.get('cloud', {})
provider = cloud.get('provider', 'aws')
region = cloud.get('region', 'us-east-1')
project = config.get('projectName', 'vtoc')

try:
    bundle_raw = subprocess.check_output(
        ["terraform", "-chdir", str(terraform_dir), "output", "-json", "config_bundle"],
        text=True,
    )
except subprocess.CalledProcessError as exc:
    raise SystemExit(
        "Failed to read Terraform outputs. Run `terraform apply` in infrastructure/terraform to populate state."
    ) from exc

bundle = json.loads(bundle_raw)
if "value" in bundle:
    bundle = bundle["value"]

backend_public_env = bundle["backend"]["env_public"]
backend_image = bundle["fly"]["runtime"]["backend_image"]

terraform_dir_out = root_dir / 'infra' / 'terraform'
ansible_dir = root_dir / 'infra' / 'ansible'
terraform_dir_out.mkdir(parents=True, exist_ok=True)
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
(terraform_dir_out / 'main.tf').write_text(main_tf)

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
(terraform_dir_out / 'variables.tf').write_text(variables_tf)

outputs_tf = """output "backend_ip" {
  value = {provider}_instance.vtoc.public_ip
}
""".format(provider=provider)
(terraform_dir_out / 'outputs.tf').write_text(outputs_tf)

inventory = """[vtoc]
backend ansible_host=1.2.3.4
"""
(ansible_dir / 'inventory.ini').write_text(inventory)

station_env_lines = [
    f"          {key}: \"{{{{ station_urls.{key} | default('{value}') }}}}}\""
    for key, value in backend_public_env.items()
    if key != "DATABASE_URL"
]
station_vars_lines = [
    f"    {key}: \"{value}\""
    for key, value in backend_public_env.items()
    if key != "DATABASE_URL"
]

station_vars_block = "" if not station_vars_lines else "\n" + "\n".join(station_vars_lines)
station_env_block = "" if not station_env_lines else "\n" + "\n".join(station_env_lines)

database_url_default = backend_public_env["DATABASE_URL"]

playbook = f"""---
- name: Configure vTOC backend host
  hosts: vtoc
  become: true
  vars:
    docker_image: {{ docker_image | default('{backend_image}:latest') }}
    database_url: {{ database_url | default('{database_url_default}') }}{station_vars_block}
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
          DATABASE_URL: "{{ database_url }}"{station_env_block}
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
