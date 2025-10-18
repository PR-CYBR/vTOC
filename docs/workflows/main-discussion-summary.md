# Main discussion summary workflow

The **Main discussion summary** automation publishes release-note style updates to GitHub Discussions after commits land on `main`.

## Triggers
- Fires on `push` events to `main`.
- May be invoked manually via `workflow_dispatch` for ad-hoc summaries.

## Required secrets and variables
- `secrets.CODEX_API_KEY` authenticates the Codex CLI setup inside the container job.
- Repository variables configure output: `vars.CODEX_BASE_URL`, `vars.DOCS_DISCUSSION_CATEGORY_ID`, and optional `vars.DOCS_DISCUSSION_LABELS` / `vars.DOCS_DISCUSSION_TITLE_PREFIX`.
- `secrets.GITHUB_TOKEN` powers the discussion creation and repository checkout.

## Jobs and major steps
### `summarize` job
- Runs inside a `python:3.11-slim` container, installing Git and curl in `Install required packages`.
- Installs the Codex CLI via `Setup Codex CLI` and checks out the repo history in `Check out repository`.
- Establishes the commit window through `Determine commit range`; empty diffs skip later steps.
- Generates markdown notes with `Run commit summary script`, uploads them using `Upload discussion markdown`, and posts them via `Create or update discussion`.

## Expected artifacts
- `Upload discussion markdown` stores `discussion.md` as `main-discussion-summary-<run id>` for later reference.

## Common failure modes
- Missing Codex credentials or base URL values trigger early failures in `Setup Codex CLI` or `Install required packages`.
- Empty commit ranges lead `Determine commit range` to short-circuit the run (expected when no files changed).
- Missing `DOCS_DISCUSSION_CATEGORY_ID` or insufficient permissions cause `Create or update discussion` to fail, preventing new discussion threads from being created.
