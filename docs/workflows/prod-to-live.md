# Promote prod to live

This workflow automatically promotes the `prod` branch into `live` after a push lands in production.

## Trigger

- **On push to `prod`** – any new commit pushed to the production branch starts the workflow.

## What it does

1. Checks out the current `prod` branch revision.
2. Uses [`peter-evans/create-pull-request`](https://github.com/peter-evans/create-pull-request) to open or update a pull request targeting `live`.
3. Enables auto-merge on the promotion pull request so it completes as soon as all required checks pass.
4. Updates the `live` branch protection rule to require the release gate checks (tests and container publishing).

## Why it matters

- Keeps `live` synchronized with the hardened `prod` branch through a reviewable pull request.
- Guarantees that the release gate workflow runs and passes before changes ship to `live`.
- Avoids manual intervention by enabling auto-merge and ensuring branch protection enforces the necessary checks.
