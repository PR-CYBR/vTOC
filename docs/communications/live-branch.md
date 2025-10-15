# Live branch operations

This guide documents how the `live` branch fits into the deployment workflow and provides text that can be copied into a GitHub Discussion for ongoing status updates.

## Purpose of the `live` branch

* Acts as the protected release branch for production traffic on Fly.io.
* Mirrors the latest Fly.io deployment so operators can audit the exact commit and configuration serving users.
* Receives only tested, production-ready changes that have already merged into `main`.

## Promotion workflow to Fly.io

1. Develop features in short-lived branches that merge into `main` through reviewed pull requests.
2. When a `main` commit is ready for production, create a release branch (for example, `release/<date>`), run validation (CI, smoke tests, Fly.io staging), and open a pull request targeting `live`.
3. Tag the release commit (e.g., `vYYYY.MM.DD`) so Fly.io builds can reference an immutable image.
4. Merge the release branch into `live` only after tests pass and the release has been approved by an operator.
5. Deploy to Fly.io from the `live` branch using the GitHub Action (`fly-deploy.yml`) or the manual workflow described in [`docs/DEPLOYMENT.md`](../DEPLOYMENT.md#flyio).
6. After deployment, update the GitHub Discussion thread (see below) with the commit SHA, Fly.io release ID, and any notable runbook annotations.

## Rollback strategy

* Identify the last known good tag or commit recorded in the discussion thread.
* Use `git revert <sha>` on `live` (or reset the branch to the previous tag) and redeploy via Fly.io to roll back quickly.
* Document the rollback in the discussion, including the root cause, fix-forward plan, and any new guardrails.
* Optionally cherry-pick hotfixes from `main` if the incident requires additional mitigation before re-promoting.

## Expectations for contributors

* Feature work merges into `main`; do not open feature pull requests directly against `live`.
* Treat `live` as protected—changes must flow through the release process and be accompanied by deployment notes.
* Keep the GitHub Discussion thread updated with deployment, validation, and rollback notes so operators have a single source of truth.
* Cross-reference release testing artifacts (CI runs, Fly.io logs, dashboards) when posting updates.

## GitHub Discussion seed

**Title:** Deployment Strategy: live branch

**Category:** Announcements → Deployments (or whichever deployment-focused category exists)

**Body:**

```
# Deployment Strategy: live branch

This thread tracks Fly.io deployments promoted from `main` to the production `live` branch.

**Latest docs**
- [Live branch operations guide](https://github.com/PR-CYBR/vTOC/blob/main/docs/communications/live-branch.md)
- [Deployment guide](https://github.com/PR-CYBR/vTOC/blob/main/docs/DEPLOYMENT.md)

**Release flow**
- Develop features on short-lived branches.
- Merge into `main` after review.
- Promote validated commits from `main` into `live` via release branches.
- Deploy `live` to Fly.io with the `fly-deploy.yml` workflow or `flyctl deploy --image ghcr.io/<repo>/backend:<sha>`.

**Update template**
- Deployed commit/tag: `<sha or tag>`
- Fly.io release ID: `<fly release>`
- Validation: `<CI run URL / smoke test notes>`
- Rollback status: `<n/a or notes>`
- Runbook updates: `<links>`

Please post here when a new deployment, rollback, or hotfix occurs so operators can track current production state.
```

Copy the title/body above into a new GitHub Discussion so operators can subscribe for deployment notifications.
