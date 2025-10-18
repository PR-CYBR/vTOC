# Project Ready Execute workflow

The **Project Ready Execute** automation executes Codex Cloud plans once a backlog item transitions into the Ready state.

## Triggers
- Listens for `projects_v2_item` edits and runs when the Status field changes from Backlog to Ready.

## Required secrets and variables
- `secrets.CODEX_API_KEY` is required by `Ensure Codex configuration is available` and the Codex execution request.
- Repository variables read in the job: `vars.CODEX_BASE_URL` and optional `vars.PROJECT_READY_REVIEWERS`/`vars.REVIEW_TEAM` for notifications.

## Jobs and major steps
### `prepare` job
- Validates the event payload in `Validate event and gather item metadata`, ensuring the item moved from Backlog to Ready and that the `Codex Cloud Plan` field is populated.
- Outputs the encoded plan and metadata for the next job, including reviewer hints and automation status field identifiers.

### `execute` job
- Verifies required configuration in `Ensure Codex configuration is available` and materializes the plan through `Decode Codex Cloud plan`.
- Calls the Codex Cloud API in `Execute Codex Cloud plan`, capturing response JSON and logs.
- Uploads run details as artifacts via `Upload Codex execution artifacts`.
- Updates project fields and progress in `Update project item status`, and posts follow-up notes with `Post summary note`.
- Writes a run summary block to the Actions UI in `Write job summary`.

## Expected artifacts
- `Upload Codex execution artifacts` publishes the plan, a pretty-printed copy, the API response, and a log bundle under `project-ready-<run id>`.

## Common failure modes
- Missing Codex credentials trigger an early exit in `Ensure Codex configuration is available`.
- Invalid or blank plan payloads raise failures during `Validate event and gather item metadata` or `Decode Codex Cloud plan`.
- HTTP errors from Codex cause `Execute Codex Cloud plan` to fail and block the status update.
- GraphQL permission issues or schema drift can break `Update project item status`, leaving the item in Ready without reviewer reassignment.
