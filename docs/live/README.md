# Live Branch Overview

The `live` branch represents the actively running production environment that consumers interact with.

## Terraform Cloud integration

Infrastructure state and deployments are coordinated through Terraform Cloud. Promotion pull requests targeting `live` should have already passed through the Terraform Cloud pipelines while in `prod`, so merges simply confirm that the latest applied infrastructure matches the source of truth.

## Fly deployment expectations

Fly.io receives container images produced by the release gate workflow. Once a promotion pull request merges, Fly deploys the images referenced by the `live` branch. Operational readiness checks in Fly should be complete before approving manual overrides.

## Automated promotion path

1. Code merges into `prod` after passing its gating workflows.
2. The `Promote prod to live` workflow opens or updates a pull request from `prod` to `live`, requests auto-merge, and enforces the release status checks.
3. The `Live Release PR Gate` workflow runs tests and publishes containers using the `prod` branch head.
4. GitHub automatically merges the promotion pull request once all required checks succeed, finalizing the promotion to `live`.
