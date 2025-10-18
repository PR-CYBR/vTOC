# vTOC Platform

![CI](https://github.com/PR-CYBR/vTOC/actions/workflows/ci.yml/badge.svg)
![Preview Deploy](https://github.com/PR-CYBR/vTOC/actions/workflows/preview-deploy.yml/badge.svg)

vTOC pairs a FastAPI backend, a map-first Vite frontend, and automation agents to deliver a virtual tactical operations center.
This README now serves as the global navigation hub—follow the links below to get to the right branch guide, documentation, or
collaboration surface quickly.

## Branch playbooks

- [`main` branch guide](docs/branches/main.md) – documentation-first branch that is only updated through the automated production
  sync pull request.
- [`prod` branch guide](docs/branches/prod.md) – the staging ground for release candidates and production hotfixes.
- [`live` branch guide](docs/branches/live.md) – mirrors what Terraform Cloud deploys to Fly.io.

## Release flow overview

1. Start feature work from a topic branch that targets `prod` and run the standard CI (`ci.yml`) and preview deploy checks.
2. Merge reviewed changes into `prod`. Terraform Cloud promotes the release to the hardened `live` branch which triggers the
   [`Fly Deploy`](.github/workflows/fly-deploy.yml) workflow.
3. After the deploy step succeeds, the `verify-sync` job hits
   [`https://vtoc.pr-cybr.com/healthz`](https://vtoc.pr-cybr.com/healthz). A passing probe automatically upserts a `prod → main`
   synchronization PR so that the documentation branch stays aligned with production.
4. Maintainers merge the synchronization PR—direct merges to `main` are blocked, enforcing the “only merge from prod” policy.

If anything fails along the way, investigate the workflow run, fix the branch that failed (usually `prod` or `live`), and let the
automation retry. The manual [Configure Main Branch Protection](.github/workflows/protect-main.yml) workflow keeps the
protection rules reproducible by running [`scripts/automation/protect-main-branch.sh`](scripts/automation/protect-main-branch.sh)
with the GitHub CLI.

## Collaboration hubs

- [Discussions](https://github.com/PR-CYBR/vTOC/discussions) – async planning, release notes, and incident follow-ups.
- [Projects](https://github.com/orgs/PR-CYBR/projects) – roadmap boards and sprint tracking.
- [Wiki](https://github.com/PR-CYBR/vTOC/wiki) – reserved for curated runbooks and operations guides (coming soon).

## Documentation map

- [Quick start](docs/QUICKSTART.md) – developer onboarding and local setup.
- [Architecture](docs/ARCHITECTURE.md) & [Diagrams](docs/DIAGRAMS.md) – system overview and reference visuals.
- [Hardware setup](docs/HARDWARE.md) & [Station checklist](docs/SETUP.md) – on-premise station guidance.
- [Deployment guide](docs/DEPLOYMENT.md) & [infrastructure notes](infrastructure/README-infra.md) – Fly.io and Terraform Cloud
  automation details.
- [Service READMEs](services) – per-service instructions across ADS-B, GPS, H4M bridge, and more.

## Tooling highlights

- [`scripts/bootstrap_cli`](scripts/bootstrap_cli) – orchestrates local, containerized, and cloud bootstrap flows.
- [`scripts/fly_deploy.sh`](scripts/fly_deploy.sh) – manual helper that mirrors the automated Fly.io deployment.
- [`scripts/automation`](scripts/automation) – automation entry points, including backlog management and branch protection.
- [`backend/`](backend) & [`frontend/`](frontend) – primary application codebases (FastAPI + Vite/React).

Have an improvement in mind? Open a discussion first, then drive a PR through the `prod` branch so the release automation can
close the loop.
