# `prod` branch guide

The `prod` branch is the source of truth for production deployments. Release candidates are assembled here after clearing
feature review on topic branches. Once a change is merged into `prod`, the Fly deploy workflow promotes it to the hardened `live`
branch and triggers the post-deploy health check.

## Release cadence

- `prod` should only accept merges through reviewed pull requests.
- Successful deploys automatically result in a synchronization PR back to `main`.
- Hotfixes land here first; automation fans out to `live` and then back-propagates to `main`.

## Checklist before merging

- [ ] CI workflows are green (including application tests and container builds).
- [ ] Operational runbooks are updated for any new dependencies or rollout steps.
- [ ] Rollback instructions are documented in the pull request description.

Keeping `prod` stable ensures the downstream `live` deployments and `main` documentation stay accurate.
