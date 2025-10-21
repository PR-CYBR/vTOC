# Prod branch operations

This README documents how the `prod` branch coordinates deployments across the self-hosted (`main`) and managed cloud (`live`) environments while enforcing production verification guardrails.

## Purpose of the `prod` branch

* Acts as the umbrella release branch that consolidates changes proven in `main` (self-hosted operators) and `live` (Fly.io cloud).
* Produces the long-lived `prod` image tag in both GHCR and Docker Hub so downstream automation can subscribe to a stable artifact.
* Runs end-to-end verification of the published container images before sign-off, giving operators confidence that the multi-instance fleet is in sync.

## Multi-instance orchestration

1. Develop and test features on short-lived branches that merge into `main`. Self-hosted instances can continue to deploy directly from `main` once their validations pass.
2. Promote the same changes into `live` via release branches to refresh the Fly.io environment. Confirm cloud-specific smoke tests succeed before proceeding.
3. When both environments are ready, fast-forward or merge `prod` to the harmonized commit so that container publishing reflects the unified state.
4. Allow the **Publish Containers** workflow to build the `prod` tag. The workflow regenerates the compose manifest, ensuring self-hosted clusters and cloud workers pull a consistent stack.

## Verification guardrails

The publish workflow adds a `verify-dockerhub` job that only runs on `prod`:

* Pulls the freshly tagged `docker.io/<namespace>/<service>:prod` images produced earlier in the pipeline.
* Boots disposable backend and frontend containers, curling `/healthz` and `/` respectively until they respond successfully.
* Executes a scraper container command to verify the image exits cleanly.
* Uploads container logs and opens a GitHub Issue pointing to the workflow run when any smoke test fails, ensuring the incident is tracked and triaged before images propagate.

If the verification job fails, do **not** deploy the new images. Investigate the linked issue, remediate the root cause (code fix, configuration, or infrastructure), and rerun the workflow once resolved. On success, document the promotion in the same channels used for `main` and `live` releases so operators across both environments stay aligned.

## Communication checklist

* Announce `prod` promotions in the deployment discussion alongside the associated `main` and `live` updates.
* Include links to the successful verification run and note any overrides applied for self-hosted versus cloud operators.
* Capture follow-up tasks (for example, additional monitoring or rollback drills) if the verification pipeline surfaced new action items.
