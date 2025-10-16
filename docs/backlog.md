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
context that does not belong in the structured fields.

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
| `last_updated_by` | string | Yes | Actor that most recently edited the record (`github:<handle>`, `codex`, etc.). |
| `metadata` | object | No | Free-form key/value map for integration-specific data (for example deployment targets or scheduling hints). |

### Status model

Backlog items move through the following states:

| Status | Meaning | Allowed transitions |
| --- | --- | --- |
| `proposed` | Idea captured but not yet accepted or staffed. | `triaged`, `discarded` |
| `triaged` | Accepted into the backlog with clear scope and priority. | `in_progress`, `blocked`, `discarded` |
| `in_progress` | Actively being implemented. | `blocked`, `review`, `done`, `discarded` |
| `blocked` | Implementation paused due to an external dependency. | `in_progress`, `discarded` |
| `review` | Work is complete pending validation, testing, or leadership sign-off. | `in_progress`, `done`, `discarded` |
| `done` | Delivered, validated, and ready for release notes. | (terminal) |
| `discarded` | Item is no longer pursued. Document the rationale in `summary`. | (terminal) |

All transitions should be recorded via pull request or automation run so the
history remains auditable.

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

Codex and GitHub workflows will mutate the backlog with the following rules:

- **Codex plan generation**: When a Codex plan is created from a backlog item,
- the automation writes the plan URL to `codex_plan_url`, records a list of
  generated tasks in `codex_plan_tasks`, appends the run identifier to
  `codex_run_ids`, captures a timestamp in `codex_plan_generated_at`, and sets
  `last_updated_by` to `codex`. Historical plans are appended to the
  `plan_history` array with their generated timestamps so the team can audit
  changes over time.
- **GitHub Project sync**: A scheduled workflow syncs `project_item_id` with the
canonical GitHub Project board. Items missing from the board remain `null`.
- **Status enforcement**: Automations only advance states forward along the
allowed transitions. If a workflow detects an invalid transition it creates a PR
comment instead of committing directly.
- **Metadata enrichment**: External integrations (for example deployment or
telemetry tooling) write machine-generated context into `metadata`. Human edits
should avoid deleting keys that automation owns; instead set their values to
`null` so the workflow can reconstruct them.

## Validation

A lightweight CI job runs `yamllint` and a schema check against
`backlog/backlog.schema.json` (to be added in a future iteration) to ensure
formatting and field types remain consistent. If the job fails, update the local
file and re-run the checks before opening a pull request.
