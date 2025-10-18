# Codex branch operations

This document briefs both Codex agents and human maintainers on how the `codex` branch is promoted through the environment pipeline.

## Automation workflow

- Pushing commits to `codex` triggers `.github/workflows/codex-sync-stage.yml`.
- The workflow executes the shared `.github/workflows/reusable-tests.yml` suite. Results are written to the workflow summary and exposed as outputs for downstream automations.
- When the validation status is `passed`, the workflow opens (or refreshes) a pull request from `codex` to `stage`, labels it for auto-merge, and attempts to enable GitHub's auto-merge. If protections block auto-merge, the workflow posts a notification tagging the configured maintainers team so they can intervene manually.
- Stage PR reviews continue to run via `.github/workflows/codex-pr-review.yml`, but linting is skipped for the auto-promotion PRs because the push workflow already validated the branch.

## Codex CLI usage

Codex review automation uses `scripts/automation/codex_pr_review.py`, which wraps the Codex CLI to evaluate diffs when pull requests target `codex` or `stage`. Ensure that the CLI binary is available on the runner (the action installs it automatically) and that the following inputs are configured:

- `secrets.CODEX_API_KEY`
- `vars.CODEX_BASE_URL`
- `vars.CODEX_REVIEW_MODEL`

With those values in place the workflow invokes `codex_pr_review.py` with the correct base/head SHAs and posts the generated summary back to the pull request.

## Required repository configuration

| Setting | Purpose |
| --- | --- |
| `secrets.CODEX_API_KEY` | Authenticates the Codex CLI used in review and promotion workflows. |
| `vars.CODEX_BASE_URL` | Base URL for the Codex API. |
| `vars.CODEX_REVIEW_MODEL` | Model identifier for the review CLI. |
| `vars.CODEX_STAGE_MAINTAINERS` | GitHub handle or team mention (for example `@org/stage-maintainers`) that should be pinged when auto-merge cannot be enabled. |
| `vars.CODEX_AUTO_MERGE_LABEL` | Optional label applied to the promotion PR to integrate with auto-merge policies. Defaults to `auto-merge` if unset. |

Create the `auto-merge` label (or whichever custom label you configure) in the repository so the workflow can apply it without errors.

## Promotion cadence

- Every push to `codex` automatically attempts promotion to `stage` after passing the reusable tests.
- Maintainers should treat the promotion pull request as the canonical view of pending changes bound for `stage`. Review the Codex summary, ensure any blocking stage checks are cleared, and merge when ready.
- If auto-merge fails because of branch protections, respond to the workflow's notification, resolve the blocking status checks, and manually complete the merge.
- In emergencies you can manually close the promotion PR to pause the cadence. The next successful push to `codex` will reopen it.

For questions or issues with the automation, reach out to the team listed in `vars.CODEX_STAGE_MAINTAINERS`.
