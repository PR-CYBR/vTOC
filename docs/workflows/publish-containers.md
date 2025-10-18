# Publish Containers workflow

The **Publish Containers** GitHub Actions workflow keeps the Docker images and compose manifest in sync with `main`, `live`, `prod`, and tagged releases.

## Triggers
- `workflow_dispatch` with an optional `release_tag` input for ad-hoc promotions.
- Weekly scheduled run at 12:00 UTC on Mondays.
- `push` events targeting the `main`, `live`, and `prod` branches or tags matching `v*`.
- When the workflow runs on the `prod` branch, it automatically passes `prod` as the `release_tag` to keep a stable production alias in both registries.

## Required secrets and variables
- `secrets.GITHUB_TOKEN` is used by `Log in to GHCR`, `Upload compose manifest artifact`, and `Attach compose file to release` for registry and release access.
- No additional repository variables are required; tags are derived from the workflow context or the optional dispatch input.

## Jobs and major steps
### `tests` job
- Checks out the repository via `actions/checkout@v4`.
- Installs the frontend toolchain in `Set up pnpm`, `Set up Node.js`, and `Enable corepack` before running `Install frontend dependencies`.
- Runs the React test and build suites in `Frontend tests` and executes UI smoke coverage with `Playwright smoke tests`.
- Provisions Python in `Set up Python`, installs dependencies through `Install backend dependencies`, and executes API checks with `Backend tests`.

### `publish` job
- Normalizes the target registry name in `Lowercase image repository` and prepares QEMU/Buildx for multi-arch builds.
- Authenticates via `Log in to GHCR` and calculates version tags in `Compute image tags`.
- Builds and pushes the backend, frontend, and scraper images using the respective `Build and push … image` steps.
- Regenerates the docker compose manifest in `Generate compose manifest`, stores it via `Upload compose manifest artifact`, and attaches it to tagged releases with `Attach compose file to release`.

### `verify-dockerhub` job
- Runs only after a successful publish on the `prod` branch.
- Pulls the `docker.io/<namespace>/<service>:prod` images emitted by the publish job and revalidates that they start correctly.
- Launches disposable containers for the backend (`/healthz`) and frontend (`/`) to curl their health endpoints until they succeed, and performs an exit-status check for the scraper image.
- Uploads container logs when a verification step fails and opens a GitHub Issue referencing the workflow run and prod tag via `actions/github-script` for rapid triage.

## Expected artifacts
- `Upload compose manifest artifact` publishes `docker-compose.generated.yml` for downstream deployment tooling.
- `dockerhub-verification-logs` (only on failures) captures the container logs gathered during production verification.

## Common failure modes
- Test suites failing in `Frontend tests`, `Playwright smoke tests`, or `Backend tests` block the publish job because `publish` depends on `tests`.
- Registry authentication issues (`Log in to GHCR`) or insufficient permissions will prevent pushes and cause the build steps to fail.
- Missing or malformed `release_tag` inputs can surface in `Compute image tags`, yielding invalid tag sets and build failures.
- Changes that break compose generation cause `Generate compose manifest` to fail, preventing the artifact upload and release attachment steps.
- Production verification failures (for example, health checks timing out or missing Docker Hub credentials) trigger the `verify-dockerhub` job to upload logs and open a GitHub Issue for follow-up.
