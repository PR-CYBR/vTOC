# Backlog management

The `backlog/backlog.yaml` file records structured work items that help the
vTOC team coordinate roadmap planning across engineering, automation, and
operations. Each entry is intentionally terse so it can be rendered in scripts,
GitHub Projects, and Codex plans without additional parsing. This document
explains the schema, how status transitions should occur, and the automation
rules that will keep the backlog consistent.

## File structure

The backlog file is a single YAML document with an `items` list. Duplicate the
provided template object for every work item and keep the list sorted by `id`
so merges are predictable. Comments are allowed and should be used to capture
context that does not belong in the structured fields. **Do not convert the
document to a top-level map**—automation expects `items` to be a YAML sequence
so it can merge Codex-managed fields into each entry in place.

```yaml
items:
  - id: "BL-001"
    title: "Short title"
    status: proposed
    summary: |
      Markdown-formatted description that can span multiple lines.
    project_item_id: null
    codex_plan_url: null
    codex_run_ids: []
    codex_plan_tasks: []
    codex_plan_generated_at: null
    plan_history: []
    last_updated_by: "github:handle"
    metadata: {}
```

### Field reference

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | string | Yes | Stable identifier such as `BL-123`. Use a monotonic counter and avoid reusing identifiers once assigned. |
| `title` | string | Yes | Action-oriented summary that fits comfortably in automation dashboards. |
| `status` | enum | Yes | Current lifecycle state. See [Status model](#status-model). |
| `summary` | string (block) | Yes | Markdown narrative that outlines the problem, constraints, success metrics, and any links to deeper context. |
| `project_item_id` | string / null | No | Identifier from GitHub Projects or another planning tool. Leave `null` when unassigned. |
| `codex_plan_url` | string / null | No | Link to a Codex Plan that scopes the work item. Automations will set this when a plan is generated. |
| `codex_run_ids` | array[string] | No | Historical Codex run identifiers related to this work item. Automations append to this list. |
| `codex_plan_tasks` | array[object] | No | Machine-generated breakdown from Codex plans. Treat entries as append-only records. |
| `codex_plan_generated_at` | string / null | No | ISO-8601 timestamp recorded when Codex last generated a plan. |
| `plan_history` | array[object] | No | Chronological log of prior Codex plans and their metadata. |
| `last_updated_by` | string | Yes | Actor that most recently edited the record (`github:<handle>`, `codex`, etc.). |
| `metadata` | object | No | Free-form key/value map for integration-specific data (for example deployment targets or scheduling hints). |

### Status model

Backlog items move through the following states:

| Status | Meaning | Allowed transitions | Spec Kit hook |
| --- | --- | --- | --- |
| `proposed` | Idea captured but not yet accepted or staffed. | `triaged`, `discarded` | Capture a lightweight note in `specs/<feature>/README.md` when `/speckit.init` seeds the folder. |
| `triaged` | Accepted into the backlog with clear scope and priority. | `in_progress`, `blocked`, `discarded` | `/speckit.spec` publishes `spec.md` and pushes the backlog item id into `context.yaml`. |
| `in_progress` | Actively being implemented. | `blocked`, `review`, `done`, `discarded` | `/speckit.plan` and `/speckit.tasks` split deliverables into backend/frontend cards and create `tasks/` stubs. |
| `blocked` | Implementation paused due to an external dependency. | `in_progress`, `discarded` | `/speckit.sync` annotates the feature folder with `blocked.md` and updates the backlog summary. |
| `review` | Work is complete pending validation, testing, or leadership sign-off. | `in_progress`, `done`, `discarded` | CI checks the generated `qa-checklist.md` to verify sign-off owners before merging. |
| `done` | Delivered, validated, and ready for release notes. | (terminal) | `/speckit.sync` archives the folder (see below) and updates the deployment notes. |
| `discarded` | Item is no longer pursued. Document the rationale in `summary`. | (terminal) | Delete or archive the feature folder after pushing a Codex note explaining the cancellation. |

All transitions should be recorded via pull request or automation run so the
history remains auditable.

## Spec artifact lifecycle

Artifacts generated in `specs/<feature>/` move through a predictable lifecycle that mirrors the backlog states above:

1. **Initialization (`/speckit.init`)** — Creates `README.md`, `context.yaml`, and a placeholder `spec.md`. The command records the
   backlog item identifier so downstream automations link commits back to the roadmap.
2. **Specification (`/speckit.spec`)** — Expands `spec.md` with user journeys, analytics notes, and integration assumptions. When
   the spec is marked ready, Codex locks the file and posts a summary to the backlog item thread.
3. **Planning (`/speckit.plan`)** — Writes `plan.md` and `qa-checklist.md` with backend/frontend milestones. Database migrations,
   API surface changes, and UI states all live side-by-side so reviewers can validate cross-functional dependencies.
4. **Task generation (`/speckit.tasks`)** — Produces Markdown cards under `specs/<feature>/tasks/`. Each file includes a `Backlog-ID`
   header so automation can open GitHub issues or populate project items without manual copying.
5. **Syncing (`/speckit.sync`)** — Mirrors key fields (status, owners, due dates) into `backlog/backlog.yaml`, refreshes GitHub
   Projects entries, and updates Codex prompt caches. If the backlog item is `blocked`, the sync command annotates
   `blocked.md` with the dependency rationale.
6. **Archival** — When `status` transitions to `done`, rename the folder to `specs/<feature>-archive/<yyyy-mm-dd>` or move it under
   `specs/archive/` so the active tree remains small. Automation compresses archived folders weekly and stores them in
   `backlog/.artifacts/`.

Automation jobs fail fast if required spec files go missing. Do not delete generated Markdown without updating the backlog or
running `/speckit.sync --force` so Codex can retire related prompts.

## Editing process

1. Copy the template entry from `backlog/backlog.yaml` and assign a new `id`.
2. Update the `title`, `summary`, and any relevant context fields.
3. Set `status` to `proposed` unless the item already met the triage criteria.
4. Fill in `last_updated_by` with your GitHub handle (`github:<name>`).
5. Commit the change with a descriptive message so history remains searchable.

When editing existing items:

- Keep YAML keys ordered as shown in the template to minimize diff noise.
- Update `last_updated_by` whenever you change any field.
- If you change `status`, add a short note to the `summary` describing why.
- Preserve `codex_run_ids` and append new values rather than replacing the list.

## Automation behavior

Codex and GitHub workflows will mutate the backlog with the following rules (see [`Project backlog plan`](workflows/project-backlog-plan.md), [`Project Ready Execute`](workflows/project-ready-execute.md), and [`Project done discussion`](workflows/project-done-discussion.md) for implementation details):

- **Codex plan generation**: When a Codex plan is created from a backlog item,
  the automation writes the plan URL to `codex_plan_url`, records a list of
  generated tasks in `codex_plan_tasks`, appends the run identifier to
  `codex_run_ids`, captures a timestamp in `codex_plan_generated_at`, and sets
  `last_updated_by` to `codex`. Historical plans are appended to the
  `plan_history` array with their generated timestamps so the team can audit
  changes over time. These fields must remain inside each entry in the `items`
  list. If a human needs to adjust them (for example, clearing an obsolete plan
  link) they should edit the individual item rather than moving the fields to a
  shared map or deleting them outright.
- **GitHub Project sync**: A scheduled workflow syncs `project_item_id` with the
canonical GitHub Project board. Items missing from the board remain `null`.
- **Status enforcement**: Automations only advance states forward along the
allowed transitions. If a workflow detects an invalid transition it creates a PR
comment instead of committing directly.
- **Metadata enrichment**: External integrations (for example deployment or
telemetry tooling) write machine-generated context into `metadata`. Human edits
should avoid deleting keys that automation owns; instead set their values to
`null` so the workflow can reconstruct them.

### Collaborator expectations for Codex-managed fields

- **Keep Codex fields local to each item**: `codex_plan_url`, `codex_plan_tasks`,
  `codex_plan_generated_at`, `codex_run_ids`, and `plan_history` belong to the
  item that triggered the automation. Never promote them to a shared structure
  or remove the surrounding list item.
- **Preserve history**: When editing `codex_plan_tasks` or `plan_history`, only
  append new entries or mark old entries as complete—do not reorder the data so
  Codex can diff runs reliably.
- **Use `null` to reset values**: If a value such as `codex_plan_url` should be
  cleared, set it to `null` instead of deleting the field. Automations depend on
  the key existing even when there is no value to report.
- **Avoid manual timestamp edits**: Fields such as `codex_plan_generated_at`
  should only change via automation unless you are correcting a known error.
  When a manual correction is required, capture the rationale in the item's
  `summary` or `notes` so the audit trail remains clear.

## Validation

A lightweight CI job runs `yamllint` and a schema check against
`backlog/backlog.schema.json` (to be added in a future iteration) to ensure
formatting and field types remain consistent. If the job fails, update the local
file and re-run the checks before opening a pull request.

## Spec Kit migration notes

Bot integration backlog items now map to dedicated Spec Kit directories under
`specs/`. Replace references to `docs/tasks/bot-integrations.md` with the
corresponding feature directory when updating backlog entries, PRs, or project
notes:

- `specs/001-bot-integrations-shared/` – shared runtime, clients, deployment, and observability foundations.
- `specs/002-bot-telegram/` – Telegram management bot transport, handlers, and rollout.
- `specs/003-bot-slack/` – Slack monitoring bot events pipeline and command surface.
- `specs/004-bot-discord/` – Discord operations bot gateway, commands, and resilience.
- `specs/005-bot-docs-qa-rollout/` – documentation, QA automation, and rollout orchestration.

Each directory includes `spec.md`, `plan.md`, `research.md`, `quickstart.md`,
`tasks.md`, and `contracts/` assets generated with the `/speckit.specify`,
`/speckit.plan`, and `/speckit.tasks` commands. When backlog scope changes,
update the relevant Spec Kit documents first, then link to them from
`backlog/backlog.yaml` via the `links` and `plan_history` fields.
