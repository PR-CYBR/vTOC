# Spec Kit integration workflow

Spec Kit acts as the bridge between discovery artifacts, Codex automation, and
our delivery pipelines. This reference explains how each command interacts with
external systems.

## Command matrix

| Command | Codex | GitHub Projects | Deployment pipelines |
| --- | --- | --- | --- |
| `/speckit.init` | Seeds a Codex memory with context.yaml contents so AI prompts can recall feature background. | Creates or updates a draft project item in the "Intake" view. | No impact. |
| `/speckit.spec` | Syncs the approved spec to Codex and exposes Q&A shortcuts. | Links the spec URL on the project item and tags it with `Needs plan`. | Updates release checklist templates so deploy previews include feature toggles. |
| `/speckit.plan` | Generates a plan summary that Codex can expand into code walkthroughs. | Moves the item to "Planned" and attaches milestone checkboxes. | Adds backend/frontend test suites to the required pipeline list for the branch. |
| `/speckit.tasks` | Registers each task as a Codex runnable, enabling `/codex run <task>` reminders. | Opens draft issues (not yet public) scoped to the project columns defined in the task metadata. | Annotates tasks with pipeline requirements so CI blocks merges if the wrong suite is skipped. |
| `/speckit.sync` | Refreshes the knowledge base with the latest spec, plan, and QA checklist. | Synchronizes status, assignees, and due dates across all linked project views. | Triggers workflow dispatches: backend image builds, frontend preview deploys, and infrastructure smoke tests when `qa-checklist.md` toggles integration checks. |

## File locations

- `specs/<feature>/context.yaml` — Canonical source for Codex memory injection.
- `specs/<feature>/spec.md` — Referenced by GitHub Project notes and PR templates.
- `specs/<feature>/plan.md` — Parsed by the deployment orchestrator to enable
  stage-specific pipelines.
- `specs/<feature>/qa-checklist.md` — Consumed by the `project-ready-execute`
  workflow to determine release gating.
- `specs/<feature>/tasks/*.md` — Backed by Codex runnable tasks and GitHub
  draft issues.

## Automation hooks

1. **Codex refresh** — A scheduled job runs `codex refresh --scope specs` nightly
   to keep the assistant aligned with the latest artifacts.
2. **Project sync** — `github-actions/project-sync.yml` (triggered by
   `/speckit.sync`) reconciles backlog statuses, updates labels, and ensures each
   task appears in the correct swimlane.
3. **Pipeline fan-out** — When a feature folder includes `qa-checklist.md` items
   tagged with `infra:` or `ops:`, the deployment workflows enable Fly.io smoke
   tests and station telemetry validation automatically.

Use this file as a quick reference when onboarding new collaborators or
troubleshooting why a project card did not update after running a Spec Kit
command.
