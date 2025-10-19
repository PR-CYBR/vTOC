# Project backlog plan workflow

The **Project backlog plan** automation generates Codex planning output when new GitHub Project items enter the backlog state.

## Triggers
- Runs on `projects_v2_item` events for newly created or edited items.

## Required secrets and variables
- `secrets.PROJECTS_WORKFLOW_TOKEN` (optional) overrides `secrets.GITHUB_TOKEN` for project mutations.
- `secrets.CODEX_API_KEY` is required by `Install Codex CLI`.
- Repository variables used: `vars.CODEX_BASE_URL` and `vars.CODEX_CLI_VERSION`.
- The workflow exports `SPECIFY_FEATURE` from project metadata so Spec Kit commands target the correct feature directory.

## Jobs and major steps
### `plan` job
- Loads the project item via `Gather project item metadata`, which also decides whether the automation should continue (`Status == Backlog`).
- Writes decoded payload details to disk in `Write backlog context` and prepares dependencies in `Set up Python` and `Install planning dependencies`.
- Installs the Codex CLI in `Install Codex CLI`, executes the planner through `Generate Codex plan`, and synchronises Spec Kit tasks in `Sync Spec Kit tasks`.
- Captures structured output via `Capture plan result`, commits changes with `Commit backlog plan`, and advances the item using `Move project item to Ready`.
- Cleans up temporary files in `Clean up temporary files` after the run.

## Expected artifacts
- No workflow artifacts are uploaded; the automation commits `backlog/backlog.yaml` and the matching `specs/<feature>/tasks.md` file directly when plans are generated.

## Common failure modes
- Missing secrets (`PROJECTS_WORKFLOW_TOKEN` or `CODEX_API_KEY`) cause early exits in `Gather project item metadata` or `Install Codex CLI`.
- Invalid backlog items (no Status field or plan context) make `Gather project item metadata` skip execution.
- Codex service outages raise errors in `Generate Codex plan`, preventing commits and status transitions.
- Missing or unparseable feature metadata leaves `SPECIFY_FEATURE` empty, which will cause `Sync Spec Kit tasks` to fail.
- Git commit issues or branch protections can cause `Commit backlog plan` to fail, leaving the item in Backlog.
