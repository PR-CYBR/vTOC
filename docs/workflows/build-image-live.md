# Build Live Images workflow

The **Build Live Images** workflow publishes production-tagged containers whenever the hardened `live` branch changes.

## Triggers
- `push` events to the `live` branch, ignoring updates under `infrastructure/**`.

## Required secrets and variables
- Relies on the repository `GITHUB_TOKEN` for `actions/registry-login@v1` and `docker/login-action@v3`.
- No additional secrets are required because the workflow uses OIDC-backed authentication to GHCR.

## Jobs and major steps
### `publish` job
- Checks out the repo in `Checkout repository` and normalizes the namespace via `Lowercase image repository`.
- Enables cross-platform builds with `Set up QEMU` and `Set up Docker Buildx`.
- Authenticates to the registry through `Authenticate to GHCR` and `Log in to GHCR`.
- Computes dual `:SHA` and `:live` tags in `Compute image tags`.
- Builds and pushes each service image with the three `Build and push … image` steps, targeting `linux/amd64` and `linux/arm64`.

## Expected artifacts
- No artifacts are uploaded; the job's output is the set of images tagged `:live` and `:<commit SHA>` for backend, frontend, and scraper.

## Common failure modes
- GHCR authentication problems (`Authenticate to GHCR` or `Log in to GHCR`) surface if the workflow lacks `packages:write` permissions.
- Build regressions for any container will fail the corresponding `Build and push … image` step.
- Incorrect Docker context changes can make `Compute image tags` succeed but break the push steps if the tags collide or are invalid.
