# `live` branch guide

The `live` branch mirrors what is currently deployed on Fly.io. Terraform Cloud pushes to this branch after promoting new
container images, which in turn triggers the Fly deployment workflow.

## Deployment mechanics

- Commits on `live` should only be created by automation.
- The branch pins infrastructure state and application image digests for repeatable rollouts.
- Monitoring dashboards and health probes should point at the commit referenced here.

## Operating tips

- Use `scripts/fly_deploy.sh` for manual redeploys with the exact image versions tracked on `live`.
- Investigate failed `Fly Deploy` workflows immediately—the branch is the canonical source for production.
- Allow the automated `prod → main` pull request to close the loop after a healthy deploy.
